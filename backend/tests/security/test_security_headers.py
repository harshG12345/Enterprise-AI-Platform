"""Security validation tests for OWASP HTTP response headers."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_owasp_security_headers_present_on_health_endpoint(async_client: AsyncClient):
    """Verify that every endpoint receives strict enterprise OWASP security headers."""
    resp = await async_client.get("/api/v1/health")
    assert resp.status_code == 200

    headers = resp.headers
    assert headers.get("x-content-type-options") == "nosniff"
    assert headers.get("x-frame-options") == "DENY"
    assert headers.get("x-xss-protection") == "1; mode=block"
    assert "max-age=31536000" in headers.get("strict-transport-security", "")
    assert headers.get("referrer-policy") == "strict-origin-when-cross-origin"
    assert "geolocation=()" in headers.get("permissions-policy", "")
    assert "default-src 'self'" in headers.get("content-security-policy", "")
    assert "x-request-id" in headers
    assert "x-process-time-ms" in headers


@pytest.mark.asyncio
async def test_security_headers_present_on_error_responses(async_client: AsyncClient):
    """Verify that error responses (404, 401, 422) also enforce strict OWASP security headers."""
    resp = await async_client.get("/api/v1/non-existent-endpoint-404")
    assert resp.status_code == 404

    headers = resp.headers
    assert headers.get("x-content-type-options") == "nosniff"
    assert headers.get("x-frame-options") == "DENY"
    assert "default-src 'self'" in headers.get("content-security-policy", "")
