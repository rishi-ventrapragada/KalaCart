"""
Centralized exception handling — consistent JSON envelope.

All error responses: { success: false, message, error_code, details? } with proper HTTP codes.
"""

import logging
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

logger = logging.getLogger(__name__)


class KalaCartException(Exception):
    """Base application exception with HTTP semantics."""

    def __init__(
        self,
        message: str = "Application error",
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Any] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details


def _error_response(
    message: str,
    error_code: str,
    status_code: int,
    details: Optional[Any] = None,
) -> JSONResponse:
    """Build consistent error JSON."""
    payload: dict = {
        "success": False,
        "message": message,
        "error_code": error_code,
    }
    if details is not None:
        payload["details"] = details
    else:
        payload["details"] = None
    # Ensure error_code also at top for backwards compat
    payload["error_code"] = error_code
    return JSONResponse(status_code=status_code, content=payload)


async def kalacart_exception_handler(request: Request, exc: KalaCartException) -> JSONResponse:
    # Phase C: include request_id for correlation (from middleware ContextVar if present)
    try:
        from app.core.middleware import get_request_id

        req_id = getattr(request.state, "request_id", None) or get_request_id() or "-"
    except Exception:
        req_id = "-"
    logger.warning(
        "KalaCartException at %s %s req_id=%s — %s [%s] details=%s",
        request.method,
        request.url.path,
        req_id,
        exc.message,
        exc.error_code,
        exc.details,
    )
    return _error_response(
        message=exc.message,
        error_code=exc.error_code,
        status_code=exc.status_code,
        details=exc.details,
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    # Map HTTP status to error_code — Phase C audit: coverage verified for 400/401/403/404/409/422/429/500/503
    # plus fallback HTTP_{code} for any unexpected (e.g., 413 from image upload).
    # StarletteHTTPException is not separately registered because FastAPI's HTTPException
    # handler catches it; generic fallback also catches unhandled 500s.
    code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "UNPROCESSABLE_ENTITY",
        429: "RATE_LIMITED",
        500: "INTERNAL_ERROR",
        503: "SERVICE_UNAVAILABLE",
    }
    error_code = code_map.get(exc.status_code, f"HTTP_{exc.status_code}")
    # Prefer detail as message; handle dict/list details
    message: str
    details: Optional[Any] = None
    if isinstance(exc.detail, str):
        message = exc.detail
    elif isinstance(exc.detail, dict):
        # If detail is dict with message/error_code, respect it
        message = exc.detail.get("message") or exc.detail.get("detail") or str(exc.detail)
        details = exc.detail.get("details") or exc.detail.get("errors")
        error_code = exc.detail.get("error_code") or error_code
    else:
        message = str(exc.detail)
        details = None

    try:
        from app.core.middleware import get_request_id

        req_id = getattr(request.state, "request_id", None) or get_request_id() or "-"
    except Exception:
        req_id = "-"
    logger.warning(
        "HTTPException %s at %s %s req_id=%s — %s",
        exc.status_code,
        request.method,
        request.url.path,
        req_id,
        message,
    )
    return _error_response(
        message=message,
        error_code=error_code,
        status_code=exc.status_code,
        details=details,
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    # FastAPI validation errors (422)
    # Build details list from pydantic errors
    try:
        errors = exc.errors()  # type: ignore
        # Simplify for response
        details = [
            {
                "loc": err.get("loc"),
                "msg": err.get("msg"),
                "type": err.get("type"),
            }
            for err in errors
        ]
        # Human-readable message: first error
        first = errors[0] if errors else {}
        msg = first.get("msg", "Validation failed") if isinstance(first, dict) else "Validation failed"
        message = f"Validation error: {msg}"
    except Exception:
        details = str(exc)
        message = "Validation failed"

    try:
        from app.core.middleware import get_request_id

        req_id = getattr(request.state, "request_id", None) or get_request_id() or "-"
    except Exception:
        req_id = "-"
    logger.warning(
        "ValidationError at %s %s req_id=%s — %s details=%s",
        request.method,
        request.url.path,
        req_id,
        message,
        details,
    )
    return _error_response(
        message=message,
        error_code="VALIDATION_ERROR",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details=details,
    )


async def pydantic_validation_handler(request: Request, exc: ValidationError) -> JSONResponse:
    # Direct Pydantic ValidationError (not FastAPI wrapper)
    try:
        details = [
            {"loc": e.get("loc"), "msg": e.get("msg"), "type": e.get("type")}
            for e in exc.errors()
        ]
        first = exc.errors()[0] if exc.errors() else {}
        msg = first.get("msg", "Validation failed") if isinstance(first, dict) else "Validation failed"
        message = f"Validation error: {msg}"
    except Exception:
        details = str(exc)
        message = "Validation failed"
    logger.warning(
        "Pydantic ValidationError at %s %s — %s",
        request.method,
        request.url.path,
        message,
    )
    return _error_response(
        message=message,
        error_code="VALIDATION_ERROR",
        status_code=status.HTTP_400_BAD_REQUEST,
        details=details,
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    try:
        from app.core.middleware import get_request_id

        req_id = getattr(request.state, "request_id", None) or get_request_id() or "-"
    except Exception:
        req_id = "-"
    logger.error(
        "Unhandled exception at %s %s req_id=%s — %s",
        request.method,
        request.url.path,
        req_id,
        exc,
        exc_info=True,
    )
    # Don't leak internal details (stack, token, PII) in production; but provide message for dev
    try:
        from app.core.config import get_settings

        is_debug = get_settings().DEBUG
    except Exception:
        is_debug = False

    details = str(exc)[:500] if is_debug else None  # Phase C: truncate to avoid PII leak
    return _error_response(
        message="Internal server error",
        error_code="INTERNAL_ERROR",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        details=details,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register all centralized handlers with the FastAPI app.
    Call this in app/main.py after creating `app = FastAPI(...)`.
    """
    app.add_exception_handler(KalaCartException, kalacart_exception_handler)  # type: ignore
    app.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore
    app.add_exception_handler(ValidationError, pydantic_validation_handler)  # type: ignore
    app.add_exception_handler(Exception, generic_exception_handler)  # type: ignore
    logger.info("Exception handlers registered")
