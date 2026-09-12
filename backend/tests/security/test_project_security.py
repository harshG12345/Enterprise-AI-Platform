"""Security tests for Project workspace isolation and ownership enforcement."""

import uuid

import pytest
from httpx import AsyncClient


async def create_user_with_role(async_client: AsyncClient, role: str) -> str:
    """Helper to create a user and return access token."""
    email = f"sec_{role.lower()}_{uuid.uuid4().hex[:8]}@enterprise-ai.io"
    password = "SecurePassword123!"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": f"{role} User", "password": password, "role": role},
    )
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    return login_res.json()["data"]["access_token"]


@pytest.mark.asyncio
async def test_non_owner_cannot_modify_or_delete_project(async_client: AsyncClient):
    """Verify User A cannot update or delete User B's project."""
    token_a = await create_user_with_role(async_client, "DATA_SCIENTIST")
    token_b = await create_user_with_role(async_client, "DATA_SCIENTIST")

    # User A creates a project
    create_res = await async_client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"name": "Proprietary Algorithm Project", "description": "Confidential"},
    )
    project_id = create_res.json()["data"]["id"]

    # User B attempts to update User A's project
    update_res = await async_client.put(
        f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"name": "Hijacked Project Name"},
    )
    assert update_res.status_code == 403
    assert update_res.json()["error"]["code"] == "PERMISSION_DENIED"

    # User B attempts to delete User A's project
    del_res = await async_client.delete(
        f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert del_res.status_code == 403
    assert del_res.json()["error"]["code"] == "PERMISSION_DENIED"


@pytest.mark.asyncio
async def test_admin_can_manage_any_project(async_client: AsyncClient):
    """Verify ADMIN role has universal workspace management capabilities."""
    token_user = await create_user_with_role(async_client, "USER")
    token_admin = await create_user_with_role(async_client, "ADMIN")

    # User creates project
    create_res = await async_client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {token_user}"},
        json={"name": "User Sandbox Project"},
    )
    project_id = create_res.json()["data"]["id"]

    # Admin reads project
    admin_get = await async_client.get(
        f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {token_admin}"},
    )
    assert admin_get.status_code == 200

    # Admin deletes project
    admin_del = await async_client.delete(
        f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {token_admin}"},
    )
    assert admin_del.status_code == 200
