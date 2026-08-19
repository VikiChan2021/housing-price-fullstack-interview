from datetime import UTC, datetime
from typing import Annotated, cast
from uuid import uuid4

from fastapi import APIRouter, Body, Depends, Request
from fastapi.responses import JSONResponse

from app.http import error_response, request_id
from app.ml_client import (
    MlApiClient,
    UpstreamBadGateway,
    UpstreamTimeout,
    UpstreamUnavailable,
)
from app.openapi import (
    ESTIMATE_BATCH_RESPONSES,
    ESTIMATE_RESPONSES,
    UPSTREAM_NOT_READY_RESPONSES,
)
from app.schemas import (
    EstimateBatchResponse,
    EstimateResponse,
    HealthResponse,
    IndexedEstimate,
    MlPredictionResponse,
    PropertyFeatures,
    ReadinessResponse,
)

estimate_router = APIRouter(tags=["estimates"])
infrastructure_router = APIRouter(tags=["infrastructure"])


def get_ml_client(request: Request) -> MlApiClient:
    return cast(MlApiClient, request.app.state.ml_client)


MlClientDependency = Annotated[MlApiClient, Depends(get_ml_client)]


async def _call_ml(
    request: Request,
    properties: list[PropertyFeatures],
    ml_client: MlApiClient,
) -> tuple[MlPredictionResponse | None, JSONResponse | None]:
    try:
        return await ml_client.predict(properties, request_id(request)), None
    except UpstreamTimeout:
        return None, error_response(request, 504, "UPSTREAM_TIMEOUT", "ML API request timed out.")
    except UpstreamBadGateway:
        return None, error_response(
            request, 502, "UPSTREAM_UNAVAILABLE", "ML API returned an invalid response."
        )
    except UpstreamUnavailable:
        return None, error_response(request, 503, "UPSTREAM_UNAVAILABLE", "ML API is unavailable.")


@estimate_router.post(
    "/api/v1/estimates",
    response_model=EstimateResponse,
    responses=ESTIMATE_RESPONSES,
)
async def create_estimate(
    request: Request,
    property_features: PropertyFeatures,
    ml_client: MlClientDependency,
) -> EstimateResponse | JSONResponse:
    result, error = await _call_ml(request, [property_features], ml_client)
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
        request_id=request_id(request),
    )


@estimate_router.post(
    "/api/v1/estimates/batch",
    response_model=EstimateBatchResponse,
    responses=ESTIMATE_BATCH_RESPONSES,
)
async def create_estimate_batch(
    request: Request,
    properties: Annotated[list[PropertyFeatures], Body()],
    ml_client: MlClientDependency,
) -> EstimateBatchResponse | JSONResponse:
    if not properties:
        return error_response(request, 422, "EMPTY_BATCH", "Estimate batch must not be empty.")
    if len(properties) > 100:
        return error_response(request, 413, "BATCH_TOO_LARGE", "Estimate batch exceeds 100 items.")
    result, error = await _call_ml(request, properties, ml_client)
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
        estimates=estimates, count=len(estimates), request_id=request_id(request)
    )


@infrastructure_router.get("/health", response_model=HealthResponse)
async def health(ml_client: MlClientDependency) -> HealthResponse:
    dependency_up = await ml_client.health()
    return HealthResponse(
        status="healthy" if dependency_up else "degraded",
        ml_api_status="up" if dependency_up else "down",
    )


@infrastructure_router.get(
    "/ready",
    response_model=ReadinessResponse,
    responses=UPSTREAM_NOT_READY_RESPONSES,
)
async def ready(
    request: Request, ml_client: MlClientDependency
) -> ReadinessResponse | JSONResponse:
    if not await ml_client.ready():
        return error_response(request, 503, "UPSTREAM_UNAVAILABLE", "ML API is not ready.")
    return ReadinessResponse(status="healthy")
