"""Define prediction, model-information, health, and readiness endpoints."""

from typing import Annotated, cast

from fastapi import APIRouter, Body, Depends, Request
from fastapi.responses import JSONResponse

from app.http import error_response, request_id
from app.openapi import (
    MODEL_NOT_READY_RESPONSES,
    PREDICT_REQUEST_EXAMPLES,
    PREDICT_RESPONSES,
)
from app.runtime import ModelArtifactError, ModelRuntime
from app.schemas import (
    HealthResponse,
    ModelInfo,
    PredictionItem,
    PredictionResponse,
    PropertyFeatures,
    ReadinessResponse,
)

prediction_router = APIRouter(tags=["predictions"])
model_router = APIRouter(tags=["model"])
infrastructure_router = APIRouter(tags=["infrastructure"])


def get_model_runtime(request: Request) -> ModelRuntime | None:
    """Resolve the startup-loaded runtime from application state for dependency injection."""

    return cast(ModelRuntime | None, getattr(request.app.state, "runtime", None))


# Annotated keeps the runtime type visible to static checking while attaching FastAPI metadata.
ModelRuntimeDependency = Annotated[ModelRuntime | None, Depends(get_model_runtime)]
PredictionPayload = Annotated[
    PropertyFeatures | list[PropertyFeatures],
    Body(openapi_examples=PREDICT_REQUEST_EXAMPLES),
]


@prediction_router.post(
    "/api/v1/predict",
    response_model=PredictionResponse,
    responses=PREDICT_RESPONSES,
)
async def predict(
    request: Request,
    payload: PredictionPayload,
    runtime: ModelRuntimeDependency,
) -> PredictionResponse | JSONResponse:
    """Accept one property or a bounded batch and preserve input order in the response."""

    # Normalize the union to one list so validation and response construction share a path.
    items = payload if isinstance(payload, list) else [payload]
    if not items:
        return error_response(request, 422, "EMPTY_BATCH", "Prediction batch must not be empty.")
    if len(items) > 100:
        return error_response(
            request, 413, "BATCH_TOO_LARGE", "Prediction batch exceeds 100 items."
        )
    if runtime is None:
        return error_response(request, 503, "MODEL_NOT_READY", "Model artifact is not ready.")
    try:
        prices = runtime.predict(items)
    except ModelArtifactError:
        return error_response(request, 503, "MODEL_NOT_READY", "Model inference failed.")
    # strict=True prevents silent truncation if a faulty runtime returns too few prices.
    predictions = [
        PredictionItem(index=index, predicted_price=price, warnings=runtime.warnings_for(item))
        for index, (item, price) in enumerate(zip(items, prices, strict=True))
    ]
    return PredictionResponse(
        predictions=predictions,
        count=len(predictions),
        model_version=runtime.model_version,
        request_id=request_id(request),
    )


@model_router.get(
    "/api/v1/model-info",
    response_model=ModelInfo,
    responses=MODEL_NOT_READY_RESPONSES,
)
async def model_info(request: Request, runtime: ModelRuntimeDependency) -> ModelInfo | JSONResponse:
    """Expose validated artifact metadata only when the runtime is usable."""

    if runtime is None:
        return error_response(request, 503, "MODEL_NOT_READY", "Model artifact is not ready.")
    return runtime.model_info


@infrastructure_router.get(
    "/health",
    response_model=HealthResponse,
    responses=MODEL_NOT_READY_RESPONSES,
)
async def health(
    request: Request, runtime: ModelRuntimeDependency
) -> HealthResponse | JSONResponse:
    """Report process health together with the artifact-backed serving state."""

    if runtime is None:
        return error_response(request, 503, "MODEL_NOT_READY", "Model artifact is not ready.")
    return HealthResponse(status="healthy", model_loaded=True, model_version=runtime.model_version)


@infrastructure_router.get(
    "/ready",
    response_model=ReadinessResponse,
    responses=MODEL_NOT_READY_RESPONSES,
)
async def ready(
    request: Request, runtime: ModelRuntimeDependency
) -> ReadinessResponse | JSONResponse:
    """Allow traffic only after artifact loading and startup smoke inference succeed."""

    if runtime is None:
        return error_response(request, 503, "MODEL_NOT_READY", "Model artifact is not ready.")
    return ReadinessResponse(status="healthy")
