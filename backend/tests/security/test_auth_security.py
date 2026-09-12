"""Security test suite validating password strength, JWT tamper resistance, and RBAC."""

import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_weak_password_rejected(async_client: AsyncClient):
    """Verify weak passwords fail validation with 422/400."""
    response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "weak@enterprise-ai.io",
            "full_name": "Weak Pass User",
            "password": "123",  # Fails min-length and complexity
        },
    )
    assert response.status_code in (400, 422)
    assert response.json()["success"] is False


@pytest.mark.asyncio
async def test_duplicate_email_registration_rejected(async_client: AsyncClient):
    """Verify duplicate email throws conflict error."""
    email = f"dup_{uuid.uuid4().hex[:8]}@enterprise-ai.io"
    payload = {
        "email": email,
        "full_name": "Original User",
        "password": "ValidPassword123!",
    }
    # First registration
    r1 = await async_client.post("/api/v1/auth/register", json=payload)
    assert r1.status_code == 201

    # Second registration with same email
    r2 = await async_client.post("/api/v1/auth/register", json=payload)
    assert r2.status_code == 409
    assert r2.json()["error"]["code"] == "CONFLICT"


@pytest.mark.asyncio
async def test_tampered_or_invalid_jwt(async_client: AsyncClient):
    """Verify forged JWT tokens are blocked with 401 unauthenticated."""
    response = await async_client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer invalid.jwt.token.here"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


@pytest.mark.asyncio
async def test_rbac_admin_endpoint_forbidden_for_standard_user(async_client: AsyncClient):
    """Verify standard USER cannot access ADMIN-only user listing endpoint."""
    email = f"standard_{uuid.uuid4().hex[:8]}@enterprise-ai.io"
    password = "StandardUser123!"

    # Register as standard USER
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Standard User", "password": password, "role": "USER"},
    )

    # Login
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    token = login_res.json()["data"]["access_token"]

    # Attempt to access GET /users (Admin only)
    admin_res = await async_client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert admin_res.status_code == 403
    assert admin_res.json()["error"]["code"] == "PERMISSION_DENIED"
