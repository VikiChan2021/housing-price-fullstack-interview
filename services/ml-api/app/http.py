"""Install request-correlation and stable validation-error handling for the ML API."""

from collections.abc import Awaitable, Callable
from typing import Any
from uuid import UUID, uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.responses import Response

from app.schemas import ErrorBody, ErrorDetail, ErrorEnvelope


def request_id(request: Request) -> str:
    """Return the canonical UUID assigned by the outermost HTTP middleware."""

    return str(request.state.request_id)


def error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: list[ErrorDetail] | None = None,
) -> JSONResponse:
    """Build the shared error envelope without duplicating request-ID plumbing."""

    envelope = ErrorEnvelope(
        error=ErrorBody(
            code=code,
            message=message,
            details=details or [],
            request_id=request_id(request),
        )
    )
    return JSONResponse(status_code=status_code, content=envelope.model_dump())


def _field_path(location: tuple[Any, ...]) -> str:
    """Translate Pydantic union locations into public single/batch field paths."""

    branch_labels = {"body", "object", "PropertyFeatures", "list[PropertyFeatures]"}
    parts = [part for part in location if part not in branch_labels]
    if parts and isinstance(parts[0], int):
        # Batch indexes are rendered as items[n].field for actionable client errors.
        index = parts.pop(0)
        return ".".join([f"items[{index}]", *map(str, parts)])
    return ".".join(map(str, parts)) or "body"


def _validation_details(exc: RequestValidationError | ValidationError) -> list[ErrorDetail]:
    """Select the relevant union branch and remove duplicate validation messages."""

    errors = exc.errors()
    if isinstance(exc, RequestValidationError):
        selected_branch = (
            "list[PropertyFeatures]" if isinstance(exc.body, list) else "PropertyFeatures"
        )
        # FastAPI reports failures for both union branches; expose only the submitted shape.
        errors_for_selected_branch = [error for error in errors if selected_branch in error["loc"]]
        errors = errors_for_selected_branch or errors

    details: list[ErrorDetail] = []
    seen: set[tuple[str, str]] = set()
    for error in errors:
        detail = (_field_path(tuple(error["loc"])), str(error["msg"]))
        if detail not in seen:
            seen.add(detail)
            details.append(ErrorDetail(field=detail[0], message=detail[1]))
    return details


def install_http_handlers(application: FastAPI) -> None:
    """Register middleware and handlers on an application factory instance."""

    @application.middleware("http")
    async def request_identifier(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        supplied = request.headers.get("X-Request-ID")
        try:
            # Parsing rejects arbitrary identifiers and normalizes valid UUIDs.
            request.state.request_id = UUID(supplied) if supplied else uuid4()
        except ValueError:
            request.state.request_id = uuid4()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id(request)
        return response

    @application.exception_handler(RequestValidationError)
    async def request_validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        # Malformed JSON is a syntax error (400); valid JSON with bad fields is semantic (422).
        malformed_json = any(error["type"] == "json_invalid" for error in exc.errors())
        return error_response(
            request,
            400 if malformed_json else 422,
            "VALIDATION_ERROR",
            "Request body is not valid JSON."
            if malformed_json
            else "One or more fields are invalid.",
            _validation_details(exc),
        )
