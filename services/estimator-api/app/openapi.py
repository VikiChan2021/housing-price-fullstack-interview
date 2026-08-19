from typing import Any

from app.schemas import ErrorEnvelope

OpenApiResponses = dict[int | str, dict[str, Any]]

ESTIMATE_RESPONSES: OpenApiResponses = {
    422: {"model": ErrorEnvelope},
    502: {"model": ErrorEnvelope},
    503: {"model": ErrorEnvelope},
    504: {"model": ErrorEnvelope},
}

ESTIMATE_BATCH_RESPONSES: OpenApiResponses = {
    413: {"model": ErrorEnvelope},
    **ESTIMATE_RESPONSES,
}

UPSTREAM_NOT_READY_RESPONSES: OpenApiResponses = {503: {"model": ErrorEnvelope}}
