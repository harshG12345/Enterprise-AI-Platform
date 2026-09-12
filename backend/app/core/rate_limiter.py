"""High-performance Sliding Window Rate Limiting Engine for API Security."""

import asyncio
import time
from collections import defaultdict
from typing import Dict, List, Tuple

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config.settings import get_settings
from app.core.logger import logger
from app.core.responses import APIErrorResponse, ErrorDetail

settings = get_settings()


class InMemoryRateLimiter:
    """Thread-safe sliding window rate limiter tracking request timestamps per client key."""

    def __init__(self):
        # Maps key -> list of float timestamps
        self._history: Dict[str, List[float]] = defaultdict(list)
        self._lock = asyncio.Lock()
        self._last_cleanup = time.time()

    async def is_allowed(self, key: str, max_requests: int, window_seconds: int = 60) -> Tuple[bool, int, int, int]:
        """Check if request is permitted under sliding window policy.

        Returns: (allowed: bool, limit: int, remaining: int, retry_after: int)
        """
        async with self._lock:
            now = time.time()
            cutoff = now - window_seconds

            # Prune obsolete timestamps older than window
            timestamps = [ts for ts in self._history[key] if ts > cutoff]

            current_count = len(timestamps)
            if current_count >= max_requests:
                # Rate limit exceeded
                oldest_ts = timestamps[0]
                retry_after = max(1, int(oldest_ts + window_seconds - now))
                self._history[key] = timestamps
                return False, max_requests, 0, retry_after

            # Allow request and append current timestamp
            timestamps.append(now)
            self._history[key] = timestamps
            remaining = max_requests - len(timestamps)

            # Periodic background garbage collection every 5 minutes
            if now - self._last_cleanup > 300:
                self._cleanup(cutoff)
                self._last_cleanup = now

            return True, max_requests, remaining, 0

    def _cleanup(self, cutoff: float) -> None:
        """Evict stale keys from memory."""
        keys_to_remove = [k for k, v in self._history.items() if not v or v[-1] < cutoff]
        for k in keys_to_remove:
            del self._history[k]

    def reset(self) -> None:
        """Clear all rate limit histories (used in tests)."""
        self._history.clear()


# Global limiter singleton
rate_limiter = InMemoryRateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Enforces tiered rate limits on incoming HTTP requests."""

    def __init__(self, app):
        super().__init__(app)
        self.whitelisted_paths = {
            "/health",
            "/api/v1/health",
            "/metrics",
            "/api/v1/metrics",
            "/docs",
            "/redoc",
            "/api/v1/openapi.json",
        }

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP addressing behind reverse proxies."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        if request.client and request.client.host:
            return request.client.host
        return "127.0.0.1"

    def _get_tier_limit(self, path: str) -> Tuple[int, int]:
        """Determine rate limit quota (max_requests, window_seconds) based on URI pattern."""
        if any(path.startswith(p) for p in ["/api/v1/auth/login", "/api/v1/auth/register"]):
            return settings.RATE_LIMIT_AUTH_PER_MINUTE, 60
        if "/predictions/realtime" in path:
            return settings.RATE_LIMIT_PREDICTION_PER_MINUTE, 60
        return settings.RATE_LIMIT_DEFAULT_PER_MINUTE, 60

    async def dispatch(self, request: Request, call_next) -> Response:
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)

        path = request.url.path
        # Skip whitelisted utility and observability endpoints
        if path in self.whitelisted_paths or path.endswith(("/docs", "/openapi.json", "/health", "/metrics")):
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        max_requests, window = self._get_tier_limit(path)
        rate_key = f"{client_ip}:{path.split('/')[3] if len(path.split('/')) > 3 else 'root'}"

        allowed, limit, remaining, retry_after = await rate_limiter.is_allowed(
            key=rate_key,
            max_requests=max_requests,
            window_seconds=window,
        )

        if not allowed:
            request_id = getattr(request.state, "request_id", None)
            logger.warning(
                f"Rate limit exceeded for IP {client_ip} on path {path} - retry_after={retry_after}s",
                extra={"request_id": request_id},
            )
            response = JSONResponse(
                status_code=429,
                content=APIErrorResponse(
                    success=False,
                    error=ErrorDetail(
                        code="RATE_LIMIT_EXCEEDED",
                        message=f"Too many requests. Rate limit exceeded for endpoint. Please retry in {retry_after} seconds.",
                        details={"limit": limit, "retry_after_seconds": retry_after},
                    ),
                    request_id=request_id,
                ).model_dump(),
            )
            response.headers["Retry-After"] = str(retry_after)
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = "0"
            return response

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
