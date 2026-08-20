"""Strict request, response, warning, error, and model-metadata contracts for the ML API."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt


class StrictModel(BaseModel):
    """Reject unknown fields so client typos cannot be silently ignored."""

    model_config = ConfigDict(extra="forbid")


# Annotated composes reusable finite-number validation with field-specific bounds below.
FiniteNumber = Annotated[float, Field(allow_inf_nan=False)]


class PropertyFeatures(StrictModel):
    """Seven inference features; the source row identifier is intentionally absent."""

    square_footage: Annotated[FiniteNumber, Field(gt=0, le=100_000)]
    bedrooms: Annotated[StrictInt, Field(ge=0, le=100)]
    bathrooms: Annotated[FiniteNumber, Field(ge=0, le=100)]
    year_built: Annotated[StrictInt, Field(ge=1600, le=2100)]
    lot_size: Annotated[FiniteNumber, Field(gt=0, le=100_000_000)]
    distance_to_city_center: Annotated[FiniteNumber, Field(ge=0, le=10_000)]
    school_rating: Annotated[FiniteNumber, Field(ge=0, le=10)]


class RangeWarning(StrictModel):
    code: Literal["OUTSIDE_TRAINING_RANGE"] = "OUTSIDE_TRAINING_RANGE"
    field: str
    message: str = "Value is outside the range observed during training."
    value: float
    training_min: float
    training_max: float


class PredictionItem(StrictModel):
    index: int
    predicted_price: Annotated[float, Field(gt=0, allow_inf_nan=False)]
    warnings: list[RangeWarning]


class PredictionResponse(StrictModel):
    """Ordered batch response whose indexes let callers verify input/output pairing."""

    predictions: list[PredictionItem]
    count: int
    model_version: str
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
    status: Literal["healthy", "unhealthy"]
    service: Literal["ml-api"] = "ml-api"
    model_loaded: bool
    model_version: str | None


class ReadinessResponse(StrictModel):
    status: Literal["healthy"]
    service: Literal["ml-api"] = "ml-api"


class MetricSummary(StrictModel):
    evaluation_protocol: Literal["nested_5_fold_cross_validation"]
    r2_mean: float
    r2_std: Annotated[float, Field(ge=0)]
    mae_mean: Annotated[float, Field(ge=0)]
    mae_std: Annotated[float, Field(ge=0)]
    rmse_mean: Annotated[float, Field(ge=0)]
    rmse_std: Annotated[float, Field(ge=0)]


class Hyperparameters(StrictModel):
    alpha: Annotated[float, Field(gt=0)]


class ModelInfo(StrictModel):
    model_name: Literal["ridge_regression"]
    model_version: str
    feature_names: list[str]
    coefficient_space: Literal["standardized"]
    hyperparameters: Hyperparameters
    coefficients: dict[str, float]
    intercept: float
    feature_mean: dict[str, float]
    feature_scale: dict[str, float]
    training_rows: int
    training_data_sha256: str
    metrics: MetricSummary
    limitations: list[str]
