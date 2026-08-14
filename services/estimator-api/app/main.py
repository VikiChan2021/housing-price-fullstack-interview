import os
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Annotated, Any, cast
from uuid import UUID, uuid4

from fastapi import Body, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.responses import Response

from app.ml_client import (
    HttpMlApiClient,
    MlApiClient,
    UpstreamBadGateway,
    UpstreamTimeout,
    UpstreamUnavailable,
)
from app.schemas import (
    ErrorBody,
    ErrorDetail,
    ErrorEnvelope,
    EstimateBatchResponse,
    EstimateResponse,
    HealthResponse,
    IndexedEstimate,
    MlPredictionResponse,
    PropertyFeatures,
    ReadinessResponse,
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


def _field_path(location: tuple[Any, ...], prefix: str = "") -> str:
    parts = [part for part in location if part != "body"]
    if parts and isinstance(parts[0], int):
        index = parts.pop(0)
        return ".".join([f"items[{index}]", *map(str, parts)])
    result = ".".join(map(str, parts)) or "body"
    return f"{prefix}{result}"


def create_app(client: MlApiClient | None = None) -> FastAPI:
    configured_client = client or HttpMlApiClient(
        base_url=os.getenv("ML_API_BASE_URL", "http://ml-api:8000"),
        timeout_seconds=float(os.getenv("ML_API_TIMEOUT_SECONDS", "3")),
    )

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        application.state.ml_client = configured_client
        yield
        await configured_client.aclose()

    application = FastAPI(
        title="Housing Price Estimator API",
        version="0.1.0",
        description="Validated estimate orchestration backed only by ML API HTTP calls.",
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
        details = [
            ErrorDetail(field=_field_path(tuple(error["loc"])), message=str(error["msg"]))
            for error in exc.errors()
        ]
        return _error_response(
            request,
            400 if malformed_json else 422,
            "VALIDATION_ERROR",
            "Request body is not valid JSON."
            if malformed_json
            else "One or more fields are invalid.",
            details,
        )

    def ml_client() -> MlApiClient:
        return cast(MlApiClient, application.state.ml_client)

    async def call_ml(
        request: Request, properties: list[PropertyFeatures]
    ) -> tuple[MlPredictionResponse | None, JSONResponse | None]:
        try:
            return await ml_client().predict(properties, _request_id(request)), None
        except UpstreamTimeout:
            return None, _error_response(
                request, 504, "UPSTREAM_TIMEOUT", "ML API request timed out."
            )
        except UpstreamBadGateway:
            return None, _error_response(
                request, 502, "UPSTREAM_UNAVAILABLE", "ML API returned an invalid response."
            )
        except UpstreamUnavailable:
            return None, _error_response(
                request, 503, "UPSTREAM_UNAVAILABLE", "ML API is unavailable."
            )

    @application.post(
        "/api/v1/estimates",
        response_model=EstimateResponse,
        responses={
            422: {"model": ErrorEnvelope},
            502: {"model": ErrorEnvelope},
            503: {"model": ErrorEnvelope},
            504: {"model": ErrorEnvelope},
        },
        tags=["estimates"],
    )
    async def create_estimate(
        request: Request, property_features: PropertyFeatures
    ) -> EstimateResponse | JSONResponse:
        result, error = await call_ml(request, [property_features])
        if error is not None:
            return error
        assert result is not None
        prediction = result.predictions[0]
        return EstimateResponse(
            estimate_id=str(uuid4()),
            property=property_features,
            predicted_price=prediction.predicted_price,
            model_version=result.model_version,
            warnings=prediction.warnings,
            created_at=datetime.now(UTC),
            request_id=_request_id(request),
        )

    @application.post(
        "/api/v1/estimates/batch",
        response_model=EstimateBatchResponse,
        responses={
            413: {"model": ErrorEnvelope},
            422: {"model": ErrorEnvelope},
            502: {"model": ErrorEnvelope},
            503: {"model": ErrorEnvelope},
            504: {"model": ErrorEnvelope},
        },
        tags=["estimates"],
    )
    async def create_estimate_batch(
        request: Request,
        properties: Annotated[list[PropertyFeatures], Body()],
    ) -> EstimateBatchResponse | JSONResponse:
        if not properties:
            return _error_response(request, 422, "EMPTY_BATCH", "Estimate batch must not be empty.")
        if len(properties) > 100:
            return _error_response(
                request, 413, "BATCH_TOO_LARGE", "Estimate batch exceeds 100 items."
            )
        result, error = await call_ml(request, properties)
        if error is not None:
            return error
        assert result is not None
        created_at = datetime.now(UTC)
        estimates = [
            IndexedEstimate(
                index=index,
                estimate_id=str(uuid4()),
                property=property_features,
                predicted_price=prediction.predicted_price,
                model_version=result.model_version,
                warnings=prediction.warnings,
                created_at=created_at,
            )
            for index, (property_features, prediction) in enumerate(
                zip(properties, result.predictions, strict=True)
            )
        ]
        return EstimateBatchResponse(
            estimates=estimates, count=len(estimates), request_id=_request_id(request)
        )

    @application.get("/health", response_model=HealthResponse, tags=["infrastructure"])
    async def health() -> HealthResponse:
        dependency_up = await ml_client().health()
        return HealthResponse(
            status="healthy" if dependency_up else "degraded",
            ml_api_status="up" if dependency_up else "down",
        )

    @application.get(
        "/ready",
        response_model=ReadinessResponse,
        responses={503: {"model": ErrorEnvelope}},
        tags=["infrastructure"],
    )
    async def ready(request: Request) -> ReadinessResponse | JSONResponse:
        if not await ml_client().ready():
            return _error_response(request, 503, "UPSTREAM_UNAVAILABLE", "ML API is not ready.")
        return ReadinessResponse(status="healthy")

    return application


app = create_app()
