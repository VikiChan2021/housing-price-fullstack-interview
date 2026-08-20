"""Strict public DTOs and the private ML response contract used by estimator orchestration."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt


class StrictModel(BaseModel):
    """Reject unknown JSON fields instead of silently accepting client mistakes."""

    model_config = ConfigDict(extra="forbid")


# Annotated layers reusable finite-number validation with the bounds on each feature.
FiniteNumber = Annotated[float, Field(allow_inf_nan=False)]


class PropertyFeatures(StrictModel):
    """Mirror the seven ML features while deliberately excluding source identifiers."""

    square_footage: Annotated[FiniteNumber, Field(gt=0, le=100_000)]
    bedrooms: Annotated[StrictInt, Field(ge=0, le=100)]
    bathrooms: Annotated[FiniteNumber, Field(ge=0, le=100)]
    year_built: Annotated[StrictInt, Field(ge=1600, le=2100)]
    lot_size: Annotated[FiniteNumber, Field(gt=0, le=100_000_000)]
    distance_to_city_center: Annotated[FiniteNumber, Field(ge=0, le=10_000)]
    school_rating: Annotated[FiniteNumber, Field(ge=0, le=10)]


class RangeWarning(StrictModel):
    code: Literal["OUTSIDE_TRAINING_RANGE"]
    field: str
    message: str
    value: float
    training_min: float
    training_max: float


class MlPredictionItem(StrictModel):
    index: int
    predicted_price: Annotated[float, Field(gt=0, allow_inf_nan=False)]
    warnings: list[RangeWarning]


class MlPredictionResponse(StrictModel):
    """Validate the downstream ML wire format before business responses are created."""

    predictions: list[MlPredictionItem]
    count: int
    model_version: str
    request_id: str


class EstimateBase(StrictModel):
    """Fields shared by single estimates and indexed batch estimates."""

    estimate_id: str
    property: PropertyFeatures
    predicted_price: Annotated[float, Field(gt=0, allow_inf_nan=False)]
    model_version: str
    warnings: list[RangeWarning]
    created_at: datetime


class EstimateResponse(EstimateBase):
    request_id: str


class IndexedEstimate(EstimateBase):
    index: int


class EstimateBatchResponse(StrictModel):
    estimates: list[IndexedEstimate]
    count: int
    request_id: str


class ErrorDetail(StrictModel):
    field: str
    message: str


class ErrorBody(StrictModel):
    code: str
    message: str
    details: list[ErrorDetail]
    request_id: str


class ErrorEnvelope(StrictModel):
    error: ErrorBody


class HealthResponse(StrictModel):
    status: Literal["healthy", "degraded"]
    service: Literal["estimator-api"] = "estimator-api"
    ml_api_status: Literal["up", "down"]


class ReadinessResponse(StrictModel):
    status: Literal["healthy"]
    service: Literal["estimator-api"] = "estimator-api"
