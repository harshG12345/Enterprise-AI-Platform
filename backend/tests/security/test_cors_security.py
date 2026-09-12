"""Security validation tests for CORS origin lockdown and preflight policies."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_cors_preflight_for_allowed_origin(async_client: AsyncClient):
    """Verify that OPTIONS preflight requests from allowed origins receive valid CORS headers."""
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "authorization,content-type",
    }
    resp = await async_client.options("/api/v1/auth/login", headers=headers)
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert resp.headers.get("access-control-allow-credentials") == "true"


@pytest.mark.asyncio
async def test_cors_preflight_for_disallowed_origin(async_client: AsyncClient):
    """Verify that untrusted foreign origins do not receive permissive CORS headers."""
    headers = {
        "Origin": "http://malicious-attacker-domain.com",
        "Access-Control-Request-Method": "POST",
    }
    resp = await async_client.options("/api/v1/auth/login", headers=headers)
    assert resp.headers.get("access-control-allow-origin") != "http://malicious-attacker-domain.com"
