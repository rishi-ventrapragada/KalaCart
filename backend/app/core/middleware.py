"""
Production Middlewares for KalaCart API (Phase 8).
Includes Request ID generation/propagation and latency logging.
"""

import time
import uuid
import logging
import contextvars
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("kalacart.access")

# Phase C: context-local request ID for correlation across logs / handlers
# Usage: from app.core.middleware import get_request_id; get_request_id()
_request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="")

def get_request_id() -> str:
    """Return current request's X-Request-ID or empty string if outside request context."""
    try:
        return _request_id_ctx.get()
    except LookupError:
        return ""

# SECURITY: ensure logs never contain Authorization header / raw token
_SENSITIVE_HEADERS = {"authorization", "x-api-key", "cookie"}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Defense-in-depth security headers (OWASP Secure Headers).
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - Referrer-Policy: strict-origin-when-cross-origin
    - Permissions-Policy: minimal
    - HSTS (production only, 1 year)
    - CSP: restrictive default (API is JSON, not HTML)
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        # HSTS only over HTTPS — check via Settings or x-forwarded-proto
        try:
            from app.core.config import get_settings

            if get_settings().is_production:
                response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        except Exception:
            pass
        # Remove server fingerprinting
        if "Server" in response.headers:
            del response.headers["Server"]
        return response


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    Attaches a unique X-Request-ID to each incoming request and logs request duration.
    Phase C: also stores req_id in a ContextVar so any downstream handler/logger
    can include correlation ID without threading Request through every call.
    PII-safe: never logs Authorization header / raw token.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = req_id
        # Store in ContextVar for correlation in downstream handlers/loggers
        token = _request_id_ctx.set(req_id)

        start_time = time.perf_counter()
        try:
            response: Response = await call_next(request)
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(
                "Request failed | method=%s path=%s duration_ms=%.2f req_id=%s error=%s",
                request.method,
                request.url.path,
                duration_ms,
                req_id,
                str(exc)[:500],  # PII-safe: truncate, never log Authorization
            )
            # Record observable critical error event
            try:
                from app.core.metrics import metrics_collector
                metrics_collector.record_request(
                    method=request.method,
                    path=request.url.path,
                    status_code=500,
                    duration_ms=duration_ms,
                    request_id=req_id,
                )
                metrics_collector.record_error_event(
                    message=f"Unhandled exception: {str(exc)[:200]}",
                    route=request.url.path,
                    method=request.method,
                    status_code=500,
                    request_id=req_id,
                    level="CRITICAL",
                )
            except Exception:
                pass

            # Reset before re-raising to avoid leak
            try:
                _request_id_ctx.reset(token)
            except Exception:
                pass
            raise

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        response.headers["X-Request-ID"] = req_id
        response.headers["X-Response-Time-Ms"] = str(duration_ms)

        # Record metrics in collector
        try:
            from app.core.metrics import metrics_collector
            metrics_collector.record_request(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
                request_id=req_id,
            )
            if response.status_code >= 500:
                metrics_collector.record_error_event(
                    message=f"HTTP {response.status_code} on {request.method} {request.url.path}",
                    route=request.url.path,
                    method=request.method,
                    status_code=response.status_code,
                    request_id=req_id,
                    level="CRITICAL",
                )
        except Exception:
            pass

        # Log non-health endpoints (PII-safe: no headers/tokens)
        if not request.url.path.startswith(("/health", "/docs", "/openapi.json")):
            logger.info(
                "Request completed | status=%d method=%s path=%s duration_ms=%.2f req_id=%s",
                response.status_code,
                request.method,
                request.url.path,
                duration_ms,
                req_id,
            )

        # Reset ContextVar after request — prevents leak across tasks
        try:
            _request_id_ctx.reset(token)
        except Exception:
            pass
        # Re-set briefly for any post-middleware hooks in same task (optional)
        # Caller can still read via get_request_id() before next request overwrites
        _request_id_ctx.set(req_id)
        return response
