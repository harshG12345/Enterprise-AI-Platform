"""Unit tests for Project workspace CRUD operations and listing."""

import uuid

import pytest
from httpx import AsyncClient


async def create_test_user_and_token(async_client: AsyncClient, role: str = "DATA_SCIENTIST") -> tuple[str, str]:
    """Helper to create a user and return (user_id, token)."""
    email = f"user_{uuid.uuid4().hex[:8]}@enterprise-ai.io"
    password = "SecurePassword123!"
    reg_res = await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Project Tester", "password": password, "role": role},
    )
    user_id = reg_res.json()["data"]["id"]
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    token = login_res.json()["data"]["access_token"]
    return user_id, token


@pytest.mark.asyncio
async def test_project_crud_lifecycle(async_client: AsyncClient):
    """Verify create, list, retrieve, update, and delete project flow."""
    _, token = await create_test_user_and_token(async_client)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Project
    create_res = await async_client.post(
        "/api/v1/projects",
        headers=headers,
        json={"name": "Customer Lifetime Value", "description": "Predict LTV based on user tenure"},
    )
    assert create_res.status_code == 201
    project = create_res.json()["data"]
    project_id = project["id"]
    assert project["name"] == "Customer Lifetime Value"

    # 2. List Projects
    list_res = await async_client.get("/api/v1/projects", headers=headers)
    assert list_res.status_code == 200
    list_data = list_res.json()["data"]
    assert list_data["total"] >= 1
    assert any(p["id"] == project_id for p in list_data["items"])

    # 3. Get Project Details
    detail_res = await async_client.get(f"/api/v1/projects/{project_id}", headers=headers)
    assert detail_res.status_code == 200
    detail_data = detail_res.json()["data"]
    assert detail_data["id"] == project_id
    assert "datasets" in detail_data
    assert "models" in detail_data

    # 4. Update Project
    update_res = await async_client.put(
        f"/api/v1/projects/{project_id}",
        headers=headers,
        json={"name": "Customer LTV Engine v2", "description": "Updated model description"},
    )
    assert update_res.status_code == 200
    assert update_res.json()["data"]["name"] == "Customer LTV Engine v2"

    # 5. Delete Project
    delete_res = await async_client.delete(f"/api/v1/projects/{project_id}", headers=headers)
    assert delete_res.status_code == 200

    # 6. Verify Deleted
    get_res = await async_client.get(f"/api/v1/projects/{project_id}", headers=headers)
    assert get_res.status_code == 404
