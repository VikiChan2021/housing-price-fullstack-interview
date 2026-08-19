from typing import Annotated, cast

from fastapi import APIRouter, Body, Depends, Request
from fastapi.responses import JSONResponse

from app.http import error_response, request_id
from app.runtime import ModelArtifactError, ModelRuntime
from app.schemas import (
    ErrorEnvelope,
    HealthResponse,
    ModelInfo,
    PredictionItem,
    PredictionResponse,
    PropertyFeatures,
    ReadinessResponse,
)

prediction_router = APIRouter(prefix="/api/v1", tags=["predictions"])
model_router = APIRouter(prefix="/api/v1", tags=["model"])
infrastructure_router = APIRouter(tags=["infrastructure"])


def get_model_runtime(request: Request) -> ModelRuntime | None:
    return cast(ModelRuntime | None, getattr(request.app.state, "runtime", None))


ModelRuntimeDependency = Annotated[ModelRuntime | None, Depends(get_model_runtime)]


@prediction_router.post(
    "/predict",
    response_model=PredictionResponse,
    responses={
        200: {
            "description": "Ordered predictions",
            "content": {
                "application/json": {
                    "example": {
                        "predictions": [{"index": 0, "predicted_price": 248849.64, "warnings": []}],
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
    runtime: ModelRuntimeDependency,
) -> PredictionResponse | JSONResponse:
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
    "/model-info",
    response_model=ModelInfo,
    responses={503: {"model": ErrorEnvelope}},
)
async def model_info(request: Request, runtime: ModelRuntimeDependency) -> ModelInfo | JSONResponse:
    if runtime is None:
        return error_response(request, 503, "MODEL_NOT_READY", "Model artifact is not ready.")
    return runtime.model_info


@infrastructure_router.get(
    "/health",
    response_model=HealthResponse,
    responses={503: {"model": ErrorEnvelope}},
)
async def health(
    request: Request, runtime: ModelRuntimeDependency
) -> HealthResponse | JSONResponse:
    if runtime is None:
        return error_response(request, 503, "MODEL_NOT_READY", "Model artifact is not ready.")
    return HealthResponse(status="healthy", model_loaded=True, model_version=runtime.model_version)


@infrastructure_router.get(
    "/ready",
    response_model=ReadinessResponse,
    responses={503: {"model": ErrorEnvelope}},
)
async def ready(
    request: Request, runtime: ModelRuntimeDependency
) -> ReadinessResponse | JSONResponse:
    if runtime is None:
        return error_response(request, 503, "MODEL_NOT_READY", "Model artifact is not ready.")
    return ReadinessResponse(status="healthy")
