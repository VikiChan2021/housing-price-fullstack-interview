"""HTTP contract tests backed by a real trained Ridge artifact."""

import json
from pathlib import Path
from uuid import UUID

import pytest
from conftest import request
from openapi_spec_validator import validate

from app.main import create_app

VALID_PROPERTY = {
    "square_footage": 1550,
    "bedrooms": 3,
    "bathrooms": 2,
    "year_built": 1997,
    "lot_size": 6800,
    "distance_to_city_center": 4.1,
    "school_rating": 7.6,
}


def test_single_and_batch_predictions_preserve_order(trained_artifacts: tuple[Path, Path]) -> None:
    app = create_app(*trained_artifacts)
    single = request(app, "POST", "/api/v1/predict", json=VALID_PROPERTY)
    batch = request(
        app,
        "POST",
        "/api/v1/predict",
        json=[VALID_PROPERTY, {**VALID_PROPERTY, "square_footage": 2200}],
    )

    # The response index is the public guarantee that batch outputs align with inputs.
    assert single.status_code == 200
    assert single.json()["count"] == 1
    assert single.json()["predictions"][0]["predicted_price"] > 0
    assert batch.status_code == 200
    assert [item["index"] for item in batch.json()["predictions"]] == [0, 1]
    assert batch.json()["count"] == 2
    UUID(single.json()["request_id"])
    assert single.headers["X-Request-ID"] == single.json()["request_id"]


def test_outside_training_range_returns_ordered_warning(
    trained_artifacts: tuple[Path, Path],
) -> None:
    app = create_app(*trained_artifacts)
    response = request(
        app,
        "POST",
        "/api/v1/predict",
        json={**VALID_PROPERTY, "year_built": 2013, "school_rating": 9.2},
    )

    assert response.status_code == 200
    assert [warning["field"] for warning in response.json()["predictions"][0]["warnings"]] == [
        "year_built",
        "school_rating",
    ]


def test_validation_empty_and_large_batches_use_stable_errors(
    trained_artifacts: tuple[Path, Path],
) -> None:
    # Exercise schema, business batch bounds, and malformed JSON as separate failure classes.
    app = create_app(*trained_artifacts)
    missing = request(app, "POST", "/api/v1/predict", json={"square_footage": 1})
    empty = request(app, "POST", "/api/v1/predict", json=[])
    large = request(app, "POST", "/api/v1/predict", json=[VALID_PROPERTY] * 101)
    malformed = request(
        app,
        "POST",
        "/api/v1/predict",
        content=b"{",
        headers={"content-type": "application/json"},
    )

    assert missing.status_code == 422
    assert missing.json()["error"]["code"] == "VALIDATION_ERROR"
    assert any(detail["field"] == "bathrooms" for detail in missing.json()["error"]["details"]), (
        missing.json()
    )
    assert empty.status_code == 422
    assert empty.json()["error"]["code"] == "EMPTY_BATCH"
    assert large.status_code == 413
    assert large.json()["error"]["code"] == "BATCH_TOO_LARGE"
    assert malformed.status_code == 400


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("square_footage", "large"),
        ("square_footage", -1),
        ("school_rating", 11),
        ("year_built", 1599),
    ],
)
def test_invalid_types_and_hard_boundaries_return_field_errors(
    trained_artifacts: tuple[Path, Path], field: str, value: object
) -> None:
    app = create_app(*trained_artifacts)
    response = request(app, "POST", "/api/v1/predict", json={**VALID_PROPERTY, field: value})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert response.json()["error"]["details"][0]["field"] == field


def test_batch_validation_uses_stable_item_path(trained_artifacts: tuple[Path, Path]) -> None:
    app = create_app(*trained_artifacts)
    response = request(
        app,
        "POST",
        "/api/v1/predict",
        json=[VALID_PROPERTY, {**VALID_PROPERTY, "school_rating": 11}],
    )

    assert response.status_code == 422
    assert response.json()["error"]["details"][0]["field"] == "items[1].school_rating"


def test_model_info_health_and_openapi_examples(trained_artifacts: tuple[Path, Path]) -> None:
    app = create_app(*trained_artifacts)
    info = request(app, "GET", "/api/v1/model-info")
    health = request(app, "GET", "/health")
    ready = request(app, "GET", "/ready")
    openapi = request(app, "GET", "/openapi.json")

    assert info.status_code == health.status_code == ready.status_code == 200
    assert info.json()["feature_names"] == list(VALID_PROPERTY)
    assert set(info.json()["coefficients"]) == set(VALID_PROPERTY)
    assert health.json()["model_loaded"] is True
    # Generated documentation is tested as a client-facing contract, not treated as prose only.
    examples = openapi.json()["paths"]["/api/v1/predict"]["post"]["requestBody"]["content"][
        "application/json"
    ]["examples"]
    assert {"single", "batch"} <= set(examples)
    responses = openapi.json()["paths"]["/api/v1/predict"]["post"]["responses"]
    assert responses["200"]["content"]["application/json"]["example"]["count"] == 1
    assert (
        responses["422"]["content"]["application/json"]["example"]["error"]["code"]
        == "VALIDATION_ERROR"
    )
    assert "503" in openapi.json()["paths"]["/health"]["get"]["responses"]
    validate(openapi.json())


def test_missing_and_corrupt_models_are_not_reported_healthy(tmp_path: Path) -> None:
    # Both absent and unreadable artifacts must leave the process diagnosable but not ready.
    missing_app = create_app(tmp_path / "missing.joblib", tmp_path / "missing.json")
    missing = request(missing_app, "GET", "/health")
    assert missing.status_code == 503
    assert missing.json()["error"]["code"] == "MODEL_NOT_READY"

    corrupt_model = tmp_path / "corrupt.joblib"
    corrupt_metadata = tmp_path / "metadata.json"
    corrupt_model.write_bytes(b"not-a-model")
    corrupt_metadata.write_text(json.dumps({}), encoding="utf-8")
    corrupt_app = create_app(corrupt_model, corrupt_metadata)
    corrupt = request(corrupt_app, "GET", "/ready")
    assert corrupt.status_code == 503
    assert corrupt.json()["error"]["code"] == "MODEL_NOT_READY"
