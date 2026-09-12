"""Unit tests for user registration, login, profile, and password update."""

import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_login_flow(async_client: AsyncClient):
    """Verify complete user registration and login workflow."""
    email = f"scientist_{uuid.uuid4().hex[:8]}@enterprise-ai.io"
    password = "StrongPassword123!"

    # 1. Register User
    reg_response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": "Marie Curie",
            "password": password,
            "role": "DATA_SCIENTIST",
        },
    )
    assert reg_response.status_code == 201
    reg_data = reg_response.json()
    assert reg_data["success"] is True
    assert reg_data["data"]["email"] == email
    assert reg_data["data"]["role"] == "DATA_SCIENTIST"

    # 2. Login User
    login_response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_response.status_code == 200
    login_data = login_response.json()
    assert login_data["success"] is True
    token = login_data["data"]["access_token"]
    assert token is not None

    # 3. Access Protected /users/me
    me_response = await async_client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    me_data = me_response.json()
    assert me_data["data"]["email"] == email
    assert me_data["data"]["full_name"] == "Marie Curie"


@pytest.mark.asyncio
async def test_change_password_flow(async_client: AsyncClient):
    """Verify password update and subsequent login with new password."""
    email = f"user_{uuid.uuid4().hex[:8]}@enterprise-ai.io"
    old_pw = "InitialPassword123!"
    new_pw = "UpdatedPassword456!"

    # Register
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Test User", "password": old_pw},
    )

    # Login
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": old_pw},
    )
    token = login_res.json()["data"]["access_token"]

    # Change password
    change_res = await async_client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_password": old_pw, "new_password": new_pw},
    )
    assert change_res.status_code == 200
    assert change_res.json()["success"] is True

    # Login with old password should fail
    fail_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": old_pw},
    )
    assert fail_res.status_code == 401

    # Login with new password should succeed
    succ_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": new_pw},
    )
    assert succ_res.status_code == 200
