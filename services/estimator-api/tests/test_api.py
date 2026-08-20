"""Estimator orchestration and HTTP contract tests using a controllable ML client double."""

from collections.abc import Sequence

import pytest
from conftest import request
from openapi_spec_validator import validate

from app.main import create_app
from app.ml_client import UpstreamBadGateway, UpstreamTimeout, UpstreamUnavailable
from app.schemas import (
    MlPredictionItem,
    MlPredictionResponse,
    PropertyFeatures,
    RangeWarning,
)

VALID_PROPERTY = {
    "square_footage": 1550,
    "bedrooms": 3,
    "bathrooms": 2,
    "year_built": 1997,
    "lot_size": 6800,
    "distance_to_city_center": 4.1,
    "school_rating": 7.6,
}


class FakeMlClient:
    """Protocol-compatible fake that records calls and injects dependency states."""

    def __init__(self) -> None:
        self.is_healthy = True
        self.is_ready = True
        self.failure: Exception | None = None
        self.calls: list[tuple[list[PropertyFeatures], str]] = []
        self.closed = False

    async def predict(
        self, properties: Sequence[PropertyFeatures], request_id: str
    ) -> MlPredictionResponse:
        if self.failure:
            raise self.failure
        self.calls.append((list(properties), request_id))
        return MlPredictionResponse(
            predictions=[
                MlPredictionItem(
                    index=index,
                    predicted_price=248_849.64 + index,
                    warnings=(
                        [
                            RangeWarning(
                                code="OUTSIDE_TRAINING_RANGE",
                                field="year_built",
                                message="Value is outside the range observed during training.",
                                value=2013,
                                training_min=1978,
                                training_max=2012,
                            )
                        ]
                        if property_features.year_built == 2013
                        else []
                    ),
                )
                for index, property_features in enumerate(properties)
            ],
            count=len(properties),
            model_version="ridge-v1-test",
            request_id=request_id,
        )

    async def health(self) -> bool:
        return self.is_healthy

    async def ready(self) -> bool:
        return self.is_ready

    async def aclose(self) -> None:
        self.closed = True


def test_single_estimate_calls_ml_and_returns_business_fields() -> None:
    ml = FakeMlClient()
    app = create_app(ml)
    response = request(
        app,
        "POST",
        "/api/v1/estimates",
        json={**VALID_PROPERTY, "year_built": 2013},
        headers={"X-Request-ID": "5c59f6b4-4a42-49c5-a7aa-b1dcb1431212"},
    )

    assert response.status_code == 200
    assert response.json()["predicted_price"] == 248_849.64
    assert response.json()["model_version"] == "ridge-v1-test"
    assert response.json()["property"]["year_built"] == 2013
    assert response.json()["warnings"][0]["field"] == "year_built"
    assert response.json()["request_id"] == "5c59f6b4-4a42-49c5-a7aa-b1dcb1431212"
    assert len(ml.calls) == 1


def test_batch_estimate_preserves_order() -> None:
    ml = FakeMlClient()
    app = create_app(ml)
    response = request(
        app,
        "POST",
        "/api/v1/estimates/batch",
        json=[VALID_PROPERTY, {**VALID_PROPERTY, "square_footage": 2200}],
    )

    assert response.status_code == 200
    assert response.json()["count"] == 2
    assert [item["index"] for item in response.json()["estimates"]] == [0, 1]
    assert [item["property"]["square_footage"] for item in response.json()["estimates"]] == [
        1550,
        2200,
    ]


def test_validation_happens_before_ml_call() -> None:
    ml = FakeMlClient()
    app = create_app(ml)
    invalid = request(app, "POST", "/api/v1/estimates", json={"square_footage": -1})
    empty = request(app, "POST", "/api/v1/estimates/batch", json=[])
    large = request(app, "POST", "/api/v1/estimates/batch", json=[VALID_PROPERTY] * 101)

    # No recorded call proves invalid traffic cannot consume downstream ML capacity.
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "VALIDATION_ERROR"
    assert empty.status_code == 422
    assert empty.json()["error"]["code"] == "EMPTY_BATCH"
    assert large.status_code == 413
    assert large.json()["error"]["code"] == "BATCH_TOO_LARGE"
    assert ml.calls == []


@pytest.mark.parametrize(
    ("failure", "status", "code"),
    [
        (UpstreamTimeout("timeout"), 504, "UPSTREAM_TIMEOUT"),
        (UpstreamBadGateway("invalid"), 502, "UPSTREAM_UNAVAILABLE"),
        (UpstreamUnavailable("down"), 503, "UPSTREAM_UNAVAILABLE"),
    ],
)
def test_upstream_failures_are_stable(failure: Exception, status: int, code: str) -> None:
    # Parametrization holds transport categories to one stable public mapping table.
    ml = FakeMlClient()
    ml.failure = failure
    app = create_app(ml)
    response = request(app, "POST", "/api/v1/estimates", json=VALID_PROPERTY)

    assert response.status_code == status
    assert response.json()["error"]["code"] == code
    assert response.headers["X-Request-ID"] == response.json()["error"]["request_id"]


def test_health_degrades_and_readiness_fails_when_ml_is_down() -> None:
    # Liveness and readiness deliberately answer different operational questions.
    ml = FakeMlClient()
    ml.is_healthy = False
    ml.is_ready = False
    app = create_app(ml)
    health = request(app, "GET", "/health")
    ready = request(app, "GET", "/ready")

    assert health.status_code == 200
    assert health.json() == {
        "status": "degraded",
        "service": "estimator-api",
        "ml_api_status": "down",
    }
    assert ready.status_code == 503
    assert ready.json()["error"]["code"] == "UPSTREAM_UNAVAILABLE"


def test_generated_openapi_is_valid_and_documents_failure_paths() -> None:
    app = create_app(FakeMlClient())
    specification = app.openapi()

    validate(specification)
    single_responses = specification["paths"]["/api/v1/estimates"]["post"]["responses"]
    assert {"200", "422", "502", "503", "504"} <= set(single_responses)
    batch_responses = specification["paths"]["/api/v1/estimates/batch"]["post"]["responses"]
    assert {"200", "413", "422", "502", "503", "504"} <= set(batch_responses)
