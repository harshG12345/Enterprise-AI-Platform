"""Unit and integration tests for Celery Asynchronous Training Tasks, Worker Isolation, and Job Status Polling."""

import io
import uuid

import pandas as pd
import pytest
from httpx import AsyncClient

from app.tasks.celery_app import celery_app


def test_celery_task_configuration():
    """Verify Celery app is configured with JSON serialization, track_started, and task limits."""
    assert celery_app.conf.task_serializer == "json"
    assert celery_app.conf.result_serializer == "json"
    assert celery_app.conf.task_track_started is True
    assert "app.tasks.training_tasks" in celery_app.conf.include


@pytest.mark.asyncio
async def test_async_training_job_lifecycle_and_polling(async_client: AsyncClient):
    """End-to-end async training test: queue job -> eager worker execution -> poll status -> verify model & metrics."""
    # 1. Register & Login
    email = f"celery_lead_{uuid.uuid4().hex[:8]}@enterprise-ai.io"
    password = "SecurePassword123!"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Celery Engineer", "password": password, "role": "DATA_SCIENTIST"},
    )
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Project
    proj_resp = await async_client.post(
        "/api/v1/projects",
        json={"name": "Celery Asynchronous Project", "description": "Testing Phase 10 Celery Tasks"},
        headers=headers,
    )
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["data"]["id"]

    # 3. Upload Tabular Dataset
    df = pd.DataFrame(
        {
            "feat_a": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0],
            "feat_b": [2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5, 10.5, 11.5, 12.5, 13.5],
            "target": [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1],
        }
    )
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    upload_resp = await async_client.post(
        "/api/v1/datasets/upload",
        data={"project_id": project_id},
        files={"file": ("celery_train.csv", io.BytesIO(csv_bytes), "text/csv")},
        headers=headers,
    )
    assert upload_resp.status_code == 201
    dataset_id = upload_resp.json()["data"]["id"]

    # 4. Enqueue Asynchronous Training Task
    train_resp = await async_client.post(
        "/api/v1/training/train-async",
        json={
            "project_id": project_id,
            "dataset_id": dataset_id,
            "target_column": "target",
            "task_type": "classification",
            "algorithm": "random_forest_classifier",
            "hyperparameters": {"n_estimators": 20, "max_depth": 5},
            "model_name": "Async RF Classifier",
        },
        headers=headers,
    )
    assert train_resp.status_code == 202
    job_data = train_resp.json()["data"]
    job_id = job_data["job_id"]
    assert job_data["celery_task_id"] is not None

    # 5. Poll Job Status via /api/v1/jobs/{id}
    poll_resp = await async_client.get(
        f"/api/v1/jobs/{job_id}",
        headers=headers,
    )
    assert poll_resp.status_code == 200
    polled = poll_resp.json()["data"]
    assert polled["status"] == "SUCCESS"
    assert polled["model_id"] is not None
    assert polled["completed_at"] is not None
    assert polled["metrics"] is not None
    assert "test" in polled["metrics"]

    # 6. List Jobs via /api/v1/jobs
    list_jobs_resp = await async_client.get(
        f"/api/v1/jobs?project_id={project_id}",
        headers=headers,
    )
    assert list_jobs_resp.status_code == 200
    job_list = list_jobs_resp.json()["data"]
    assert len(job_list) >= 1
    assert any(j["id"] == job_id for j in job_list)


@pytest.mark.asyncio
async def test_async_training_failure_handling(async_client: AsyncClient):
    """Verify that worker failures mark the job FAILED and store safe error messages."""
    email = f"celery_fail_{uuid.uuid4().hex[:8]}@enterprise-ai.io"
    password = "SecurePassword123!"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Test User", "password": password, "role": "DATA_SCIENTIST"},
    )
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    proj_resp = await async_client.post(
        "/api/v1/projects",
        json={"name": "Celery Error Handling Project", "description": "Phase 10 error test"},
        headers=headers,
    )
    project_id = proj_resp.json()["data"]["id"]

    df = pd.DataFrame({"col_x": [1, 2, 3, 4, 5, 6], "col_y": [10, 20, 30, 40, 50, 60]})
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    upload_resp = await async_client.post(
        "/api/v1/datasets/upload",
        data={"project_id": project_id},
        files={"file": ("error_test.csv", io.BytesIO(csv_bytes), "text/csv")},
        headers=headers,
    )
    dataset_id = upload_resp.json()["data"]["id"]

    # Launch task with non-existent target column to trigger safe worker failure
    train_resp = await async_client.post(
        "/api/v1/training/train-async",
        json={
            "project_id": project_id,
            "dataset_id": dataset_id,
            "target_column": "non_existent_target",
            "task_type": "classification",
            "algorithm": "logistic_regression",
            "hyperparameters": {},
        },
        headers=headers,
    )
    assert train_resp.status_code == 202
    job_id = train_resp.json()["data"]["job_id"]

    # Poll status: must be FAILED with non-empty error_message
    poll_resp = await async_client.get(f"/api/v1/jobs/{job_id}", headers=headers)
    assert poll_resp.status_code == 200
    polled = poll_resp.json()["data"]
    assert polled["status"] == "FAILED"
    assert "Target column 'non_existent_target' not found" in polled["error_message"]
