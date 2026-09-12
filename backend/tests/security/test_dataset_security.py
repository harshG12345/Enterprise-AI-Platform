"""Security tests for dataset file validation, path safety, and tenant access isolation."""

import io
import uuid

import pytest
from httpx import AsyncClient


async def setup_test_context(async_client: AsyncClient, name: str) -> tuple[str, str]:
    """Helper to create user and project workspace."""
    email = f"{name}_{uuid.uuid4().hex[:8]}@enterprise-ai.io"
    password = "SecurePassword123!"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": name, "password": password, "role": "DATA_SCIENTIST"},
    )
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    token = login_res.json()["data"]["access_token"]

    proj_res = await async_client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": f"{name} Workspace"},
    )
    project_id = proj_res.json()["data"]["id"]
    return token, project_id


@pytest.mark.asyncio
async def test_unsupported_file_extension_rejected(async_client: AsyncClient):
    """Verify non-CSV/XLSX file extensions are blocked."""
    token, project_id = await setup_test_context(async_client, "ext_user")
    headers = {"Authorization": f"Bearer {token}"}

    files = {
        "file": ("malicious_script.sh", io.BytesIO(b"#!/bin/bash\necho 'hack'"), "text/x-sh"),
    }
    res = await async_client.post(
        "/api/v1/datasets/upload",
        headers=headers,
        data={"project_id": project_id},
        files=files,
    )
    assert res.status_code in (400, 422)
    assert res.json()["success"] is False


@pytest.mark.asyncio
async def test_duplicate_columns_rejected(async_client: AsyncClient):
    """Verify tabular datasets with duplicate column headers are rejected."""
    token, project_id = await setup_test_context(async_client, "dup_col_user")
    headers = {"Authorization": f"Bearer {token}"}

    # CSV with duplicate column 'feature_a'
    dup_csv = "feature_a,feature_b,feature_a\n1,2,3\n4,5,6\n"
    files = {
        "file": ("dup_headers.csv", io.BytesIO(dup_csv.encode("utf-8")), "text/csv"),
    }
    res = await async_client.post(
        "/api/v1/datasets/upload",
        headers=headers,
        data={"project_id": project_id},
        files=files,
    )
    assert res.status_code in (400, 422)
    assert "duplicate" in res.json()["error"]["message"].lower()


@pytest.mark.asyncio
async def test_empty_dataset_file_rejected(async_client: AsyncClient):
    """Verify empty 0-byte file uploads are rejected."""
    token, project_id = await setup_test_context(async_client, "empty_file_user")
    headers = {"Authorization": f"Bearer {token}"}

    files = {
        "file": ("empty.csv", io.BytesIO(b""), "text/csv"),
    }
    res = await async_client.post(
        "/api/v1/datasets/upload",
        headers=headers,
        data={"project_id": project_id},
        files=files,
    )
    assert res.status_code in (400, 422)
    assert res.json()["success"] is False
