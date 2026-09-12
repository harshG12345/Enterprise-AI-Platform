"""Unit test for health and readiness endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient):
    """Verify liveness endpoint returns healthy status and standard envelope."""
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "healthy"
    assert "app_name" in payload["data"]
    assert "version" in payload["data"]
    assert "X-Request-ID" in response.headers


@pytest.mark.asyncio
async def test_readiness_check(async_client: AsyncClient):
    """Verify readiness endpoint returns ready status."""
    response = await async_client.get("/api/v1/health/ready")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "ready"


@pytest.mark.asyncio
async def test_root_endpoint(async_client: AsyncClient):
    """Verify root landing endpoint."""
    response = await async_client.get("/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "online"
