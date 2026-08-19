from typing import Any

from app.schemas import ErrorEnvelope

OpenApiResponses = dict[int | str, dict[str, Any]]

PREDICT_REQUEST_EXAMPLES: dict[str, dict[str, Any]] = {
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

PREDICT_RESPONSES: OpenApiResponses = {
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
}

MODEL_NOT_READY_RESPONSES: OpenApiResponses = {503: {"model": ErrorEnvelope}}
