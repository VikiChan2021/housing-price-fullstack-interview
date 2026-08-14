import os
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any
from uuid import UUID, uuid4

from fastapi import Body, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.responses import Response

from app.runtime import ModelArtifactError, ModelRuntime, load_runtime
from app.schemas import (
    ErrorBody,
    ErrorDetail,
    ErrorEnvelope,
    HealthResponse,
    ModelInfo,
    PredictionItem,
    PredictionResponse,
    PropertyFeatures,
    ReadinessResponse,
)


def _repository_root() -> Path:
    source = Path(__file__).resolve()
    for candidate in (source.parent, *source.parents):
        if (candidate / "models").is_dir() and (candidate / "services/ml-api").is_dir():
            return candidate
    return Path.cwd()


def _paths() -> tuple[Path, Path]:
    model_path = os.getenv("ML_MODEL_PATH")
    metadata_path = os.getenv("ML_METADATA_PATH")
    if model_path and metadata_path:
        return Path(model_path), Path(metadata_path)
    root = _repository_root()
    return (
        Path(model_path or root / "models/model.joblib"),
        Path(metadata_path or root / "models/metadata.json"),
    )


def _request_id(request: Request) -> str:
    return str(request.state.request_id)


def _error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: list[ErrorDetail] | None = None,
) -> JSONResponse:
    envelope = ErrorEnvelope(
        error=ErrorBody(
            code=code,
            message=message,
            details=details or [],
            request_id=_request_id(request),
        )
    )
    return JSONResponse(status_code=status_code, content=envelope.model_dump())


def _field_path(location: tuple[Any, ...]) -> str:
    branch_labels = {"body", "object", "PropertyFeatures", "list[PropertyFeatures]"}
    parts = [part for part in location if part not in branch_labels]
    if parts and isinstance(parts[0], int):
        index = parts.pop(0)
        prefix = f"items[{index}]"
        return ".".join([prefix, *map(str, parts)])
    return ".".join(map(str, parts)) or "body"


def _validation_details(exc: RequestValidationError | ValidationError) -> list[ErrorDetail]:
    details: list[ErrorDetail] = []
    seen: set[tuple[str, str]] = set()
    errors = exc.errors()
    if isinstance(exc, RequestValidationError):
        selected_branch = (
            "list[PropertyFeatures]" if isinstance(exc.body, list) else "PropertyFeatures"
        )
        branch_errors = [error for error in errors if selected_branch in error["loc"]]
        errors = branch_errors or errors
    for error in errors:
        detail = (_field_path(tuple(error["loc"])), str(error["msg"]))
        if detail not in seen:
            seen.add(detail)
            details.append(ErrorDetail(field=detail[0], message=detail[1]))
    return details


def create_app(model_path: Path | None = None, metadata_path: Path | None = None) -> FastAPI:
    configured_model, configured_metadata = _paths()
    chosen_model = model_path or configured_model
    chosen_metadata = metadata_path or configured_metadata

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        try:
            application.state.runtime = load_runtime(chosen_model, chosen_metadata)
            application.state.load_error = None
        except ModelArtifactError as exc:
            application.state.runtime = None
            application.state.load_error = str(exc)
        yield

    application = FastAPI(
        title="Housing Price ML API",
        version="0.1.0",
        description="Artifact-backed Ridge regression with deterministic nested CV training.",
        lifespan=lifespan,
    )

    @application.middleware("http")
    async def request_identifier(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        supplied = request.headers.get("X-Request-ID")
        try:
            request.state.request_id = UUID(supplied) if supplied else uuid4()
        except ValueError:
            request.state.request_id = uuid4()
        response = await call_next(request)
        response.headers["X-Request-ID"] = _request_id(request)
        return response

    @application.exception_handler(RequestValidationError)
    async def request_validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        malformed_json = any(error["type"] == "json_invalid" for error in exc.errors())
        return _error_response(
            request,
            400 if malformed_json else 422,
            "VALIDATION_ERROR",
            "Request body is not valid JSON."
            if malformed_json
            else "One or more fields are invalid.",
            _validation_details(exc),
        )

    def runtime_or_none() -> ModelRuntime | None:
        return getattr(application.state, "runtime", None)

    @application.post(
        "/api/v1/predict",
        response_model=PredictionResponse,
        responses={
            200: {
                "description": "Ordered predictions",
                "content": {
                    "application/json": {
                        "example": {
                            "predictions": [
                                {"index": 0, "predicted_price": 248849.64, "warnings": []}
                            ],
                            "count": 1,
                            "model_version": "ridge-v1-0e36c622-a05bac12",
                            "request_id": "5c59f6b4-4a42-49c5-a7aa-b1dcb1431212",
                        }
                    }
                },
            },
            413: {"model": ErrorEnvelope},
            422: {
                "model": ErrorEnvelope,
                "content": {
                    "application/json": {
                        "example": {
                            "error": {
                                "code": "VALIDATION_ERROR",
                                "message": "One or more fields are invalid.",
                                "details": [
                                    {
                                        "field": "school_rating",
                                        "message": "Input should be less than or equal to 10",
                                    }
                                ],
                                "request_id": "5c59f6b4-4a42-49c5-a7aa-b1dcb1431212",
                            }
                        }
                    }
                },
            },
            503: {"model": ErrorEnvelope},
        },
        tags=["predictions"],
    )
    async def predict(
        request: Request,
        payload: Annotated[
            PropertyFeatures | list[PropertyFeatures],
            Body(
                openapi_examples={
                    "single": {
                        "summary": "Single property",
                        "value": {
                            "square_footage": 1550,
                            "bedrooms": 3,
                            "bathrooms": 2,
                            "year_built": 1997,
                            "lot_size": 6800,
                            "distance_to_city_center": 4.1,
                            "school_rating": 7.6,
                        },
                    },
                    "batch": {
                        "summary": "Batch of properties",
                        "value": [
                            {
                                "square_footage": 1550,
                                "bedrooms": 3,
                                "bathrooms": 2,
                                "year_built": 1997,
                                "lot_size": 6800,
                                "distance_to_city_center": 4.1,
                                "school_rating": 7.6,
                            }
                        ],
                    },
                }
            ),
        ],
    ) -> PredictionResponse | JSONResponse:
        items = payload if isinstance(payload, list) else [payload]
        if not items:
            return _error_response(
                request, 422, "EMPTY_BATCH", "Prediction batch must not be empty."
            )
        if len(items) > 100:
            return _error_response(
                request, 413, "BATCH_TOO_LARGE", "Prediction batch exceeds 100 items."
            )
        runtime = runtime_or_none()
        if runtime is None:
            return _error_response(request, 503, "MODEL_NOT_READY", "Model artifact is not ready.")
        try:
            prices = runtime.predict(items)
        except ModelArtifactError:
            return _error_response(request, 503, "MODEL_NOT_READY", "Model inference failed.")
        predictions = [
            PredictionItem(index=index, predicted_price=price, warnings=runtime.warnings_for(item))
            for index, (item, price) in enumerate(zip(items, prices, strict=True))
        ]
        return PredictionResponse(
            predictions=predictions,
            count=len(predictions),
            model_version=runtime.model_version,
            request_id=_request_id(request),
        )

    @application.get(
        "/api/v1/model-info",
        response_model=ModelInfo,
        responses={503: {"model": ErrorEnvelope}},
        tags=["model"],
    )
    async def model_info(request: Request) -> ModelInfo | JSONResponse:
        runtime = runtime_or_none()
        if runtime is None:
            return _error_response(request, 503, "MODEL_NOT_READY", "Model artifact is not ready.")
        return runtime.model_info

    @application.get(
        "/health",
        response_model=HealthResponse,
        responses={503: {"model": ErrorEnvelope}},
        tags=["infrastructure"],
    )
    async def health(request: Request) -> HealthResponse | JSONResponse:
        runtime = runtime_or_none()
        if runtime is None:
            return _error_response(request, 503, "MODEL_NOT_READY", "Model artifact is not ready.")
        return HealthResponse(
            status="healthy", model_loaded=True, model_version=runtime.model_version
        )

    @application.get(
        "/ready",
        response_model=ReadinessResponse,
        responses={503: {"model": ErrorEnvelope}},
        tags=["infrastructure"],
    )
    async def ready(request: Request) -> ReadinessResponse | JSONResponse:
        if runtime_or_none() is None:
            return _error_response(request, 503, "MODEL_NOT_READY", "Model artifact is not ready.")
        return ReadinessResponse(status="healthy")

    return application


app = create_app()
