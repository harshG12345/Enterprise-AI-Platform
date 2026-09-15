"""Unit tests for Health Readiness and Audit Logs REST endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_deep_readiness_probe(async_client: AsyncClient):
    """Test /health and /health/ready endpoints for system and database connectivity."""
    # 1. Liveness
    live_res = await async_client.get("/api/v1/health")
    assert live_res.status_code == 200
    live_data = live_res.json()["data"]
    assert live_data["status"] == "healthy"

    # 2. Deep Readiness Probe
    ready_res = await async_client.get("/api/v1/health/ready")
    assert ready_res.status_code == 200
    ready_data = ready_res.json()["data"]
    assert "status" in ready_data
    assert "database" in ready_data
    assert "redis" in ready_data
    assert "mlflow" in ready_data


@pytest.mark.asyncio
async def test_audit_logs_endpoint_rbac(async_client: AsyncClient):
    """Test /api/v1/audit-logs endpoint with pagination and RBAC scoping."""
    # 1. Register a standard user
    user_email = "auditee@enterprise.ai"
    await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": user_email,
            "password": "SecurePassword123!",
            "full_name": "Audit Test User",
            "role": "DATA_SCIENTIST",
        },
    )
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": user_email, "password": "SecurePassword123!"},
    )
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Perform action that generates audit log (e.g., create project)
    proj_res = await async_client.post(
        "/api/v1/projects",
        json={"name": "Audit Test Project", "description": "Testing audit logging"},
        headers=headers,
    )
    assert proj_res.status_code == 201

    # 3. Query audit logs
    audit_res = await async_client.get("/api/v1/audit-logs", headers=headers)
    assert audit_res.status_code == 200
    data = audit_res.json()["data"]
    assert "items" in data
    assert data["total"] >= 1
    assert data["items"][0]["action"] == "PROJECT_CREATE"
