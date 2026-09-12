"""Security validation tests for sliding window rate limiting."""

import pytest
from httpx import AsyncClient

from app.core.rate_limiter import rate_limiter


@pytest.fixture(autouse=True)
def reset_limiter():
    """Reset in-memory rate limiter between tests."""
    rate_limiter.reset()
    yield
    rate_limiter.reset()


@pytest.mark.asyncio
async def test_rate_limiter_in_memory_direct():
    """Verify sliding window rate limiter directly with simulated timestamps."""
    key = "test_user_ip:auth"
    limit = 5
    window = 10

    # 1. First 5 requests must succeed
    for i in range(5):
        allowed, max_req, remaining, retry_after = await rate_limiter.is_allowed(key, limit, window)
        assert allowed is True
        assert max_req == 5
        assert remaining == (4 - i)
        assert retry_after == 0

    # 2. 6th request must be rejected
    allowed, max_req, remaining, retry_after = await rate_limiter.is_allowed(key, limit, window)
    assert allowed is False
    assert remaining == 0
    assert retry_after > 0


@pytest.mark.asyncio
async def test_rate_limiting_headers_on_api(async_client: AsyncClient):
    """Verify rate limiting headers are injected on standard API requests."""
    resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@enterprise-ai.io", "password": "WrongPassword123!"},
    )
    assert "x-ratelimit-limit" in resp.headers
    assert "x-ratelimit-remaining" in resp.headers
