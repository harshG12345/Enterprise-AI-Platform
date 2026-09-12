"""Unit tests for Dataset upload, schema extraction, preview, and deletion."""

import io
import uuid

import pytest
from httpx import AsyncClient


async def create_user_and_project(async_client: AsyncClient) -> tuple[str, str, str]:
    """Helper to create user and project, returning (token, user_id, project_id)."""
    email = f"dataset_ds_{uuid.uuid4().hex[:8]}@enterprise-ai.io"
    password = "SecurePassword123!"
    reg_res = await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Data Science Engineer", "password": password, "role": "DATA_SCIENTIST"},
    )
    user_id = reg_res.json()["data"]["id"]
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    token = login_res.json()["data"]["access_token"]

    proj_res = await async_client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Dataset Test Project", "description": "Workspace for tabular data tests"},
    )
    project_id = proj_res.json()["data"]["id"]
    return token, user_id, project_id


@pytest.mark.asyncio
async def test_dataset_upload_and_preview_flow(async_client: AsyncClient):
    """Verify CSV dataset upload, schema metadata extraction, preview, and deletion."""
    token, _, project_id = await create_user_and_project(async_client)
    headers = {"Authorization": f"Bearer {token}"}

    # Generate synthetic CSV content
    csv_content = (
        "age,income,education,defaulted\n"
        "25,50000,Bachelors,0\n"
        "38,75000,Masters,0\n"
        "45,120000,PhD,0\n"
        "29,35000,HighSchool,1\n"
        "52,90000,Bachelors,0\n"
    )
    files = {
        "file": ("credit_data.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv"),
    }
    data = {"project_id": project_id}

    # 1. Upload CSV
    upload_res = await async_client.post(
        "/api/v1/datasets/upload",
        headers=headers,
        data=data,
        files=files,
    )
    assert upload_res.status_code == 201
    dataset = upload_res.json()["data"]
    dataset_id = dataset["id"]
    assert dataset["filename"] == "credit_data.csv"
    assert dataset["row_count"] == 5
    assert dataset["column_count"] == 4
    assert dataset["status"] == "VALIDATED"

    # 2. Get Dataset Details & Schema
    detail_res = await async_client.get(f"/api/v1/datasets/{dataset_id}", headers=headers)
    assert detail_res.status_code == 200
    detail_data = detail_res.json()["data"]
    assert len(detail_data["columns"]) == 4
    col_names = [c["name"] for c in detail_data["columns"]]
    assert "age" in col_names
    assert "defaulted" in col_names

    # 3. Preview Dataset Rows
    preview_res = await async_client.get(
        f"/api/v1/datasets/{dataset_id}/preview?page=1&page_size=2",
        headers=headers,
    )
    assert preview_res.status_code == 200
    preview_data = preview_res.json()["data"]
    assert preview_data["total_rows"] == 5
    assert len(preview_data["rows"]) == 2
    assert preview_data["columns"] == ["age", "income", "education", "defaulted"]
    assert preview_data["total_pages"] == 3

    # 4. List Datasets with project filter
    list_res = await async_client.get(
        f"/api/v1/datasets?project_id={project_id}",
        headers=headers,
    )
    assert list_res.status_code == 200
    list_data = list_res.json()["data"]
    assert list_data["total"] >= 1
    assert any(d["id"] == dataset_id for d in list_data["items"])

    # 5. Delete Dataset
    del_res = await async_client.delete(f"/api/v1/datasets/{dataset_id}", headers=headers)
    assert del_res.status_code == 200

    # 6. Verify Deleted
    get_res = await async_client.get(f"/api/v1/datasets/{dataset_id}", headers=headers)
    assert get_res.status_code == 404
