"""Middleware for request-ID tracing, performance timing, Prometheus metrics, and security headers."""

import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logger import logger, request_id_ctx
from app.monitoring.metrics import record_http_request


class RequestTracingMiddleware(BaseHTTPMiddleware):
    """Assigns unique Request-ID, logs execution latency, records Prometheus metrics, and sets security headers."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Extract or generate unique correlation ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        # Bind contextvar for structured logging throughout the request lifecycle
        token = request_id_ctx.set(request_id)

        start_time = time.perf_counter()
        try:
            response = await call_next(request)
            duration_seconds = time.perf_counter() - start_time
            process_time_ms = duration_seconds * 1000.0

            # Record Prometheus HTTP latency & count metrics (skip /metrics itself to avoid self-amplification)
            if not request.url.path.endswith("/metrics"):
                record_http_request(
                    method=request.method,
                    path=request.url.path,
                    status_code=response.status_code,
                    duration_seconds=duration_seconds,
                )

            # Set tracing & timing headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time-MS"] = f"{process_time_ms:.2f}"

            # Enterprise OWASP security headers
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=(), payment=()"
            # Content-Security-Policy (allows Swagger UI & ReDoc CDN assets for interactive documentation)
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https: https://fastapi.tiangolo.com; "
                "font-src 'self' data: https://cdn.jsdelivr.net; "
                "connect-src 'self' http: https: ws: wss:; "
                "frame-ancestors 'none';"
            )

            # Structured request access log
            logger.info(
                f"{request.method} {request.url.path} - status={response.status_code} - {process_time_ms:.2f}ms",
                extra={"request_id": request_id},
            )

            return response
        finally:
            # Reset contextvar token
            request_id_ctx.reset(token)
