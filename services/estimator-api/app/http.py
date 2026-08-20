"""Install request-ID propagation and stable validation errors for the Estimator API."""

from collections.abc import Awaitable, Callable
from typing import Any
from uuid import UUID, uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.responses import Response

from app.schemas import ErrorBody, ErrorDetail, ErrorEnvelope


def request_id(request: Request) -> str:
    """Read the UUID established by request middleware."""

    return str(request.state.request_id)


def error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: list[ErrorDetail] | None = None,
) -> JSONResponse:
    """Build the shared error envelope with the active request identifier."""

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
    """Render Pydantic locations as public object or items[index] paths."""

    parts = [part for part in location if part != "body"]
    if parts and isinstance(parts[0], int):
        index = parts.pop(0)
        return ".".join([f"items[{index}]", *map(str, parts)])
    return ".".join(map(str, parts)) or "body"


def install_http_handlers(application: FastAPI) -> None:
    """Attach HTTP middleware and exception handling to an application instance."""

    @application.middleware("http")
    async def request_identifier(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        supplied = request.headers.get("X-Request-ID")
        try:
            # Accept only UUID request IDs so log correlation cannot contain arbitrary text.
            request.state.request_id = UUID(supplied) if supplied else uuid4()
        except ValueError:
            request.state.request_id = uuid4()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id(request)
        return response

    @application.exception_handler(RequestValidationError)
    async def request_validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        # Distinguish malformed JSON syntax (400) from valid JSON with invalid fields (422).
        malformed_json = any(error["type"] == "json_invalid" for error in exc.errors())
        details = [
            ErrorDetail(field=_field_path(tuple(error["loc"])), message=str(error["msg"]))
            for error in exc.errors()
        ]
        return error_response(
            request,
            400 if malformed_json else 422,
            "VALIDATION_ERROR",
            "Request body is not valid JSON."
            if malformed_json
            else "One or more fields are invalid.",
            details,
        )
