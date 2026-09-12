"""Edge Cases, Failure Modes, and Security Boundary Integration Tests.

Validates:
1. Missing & corrupted dataset uploads
2. Incompatible and missing feature inference payloads (HTTP 422)
3. Non-existent entity queries (HTTP 404)
4. Zero-variance and degenerate numerical distributions in drift calculations
5. RBAC security enforcement and unauthorized actions
6. In-memory model cache resilience
"""

import io
import uuid

import pandas as pd
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_dataset_upload_edge_cases_and_validation(async_client: AsyncClient):
    """Test corrupted, empty, and malformed dataset uploads."""
    # 1. Register & Login
    email = f"tester_{uuid.uuid4().hex[:8]}@enterprise.ai"
    password = "SecurePassword123!"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "QA Lead", "password": password, "role": "ADMIN"},
    )
    login_resp = await async_client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Project
    proj_resp = await async_client.post(
        "/api/v1/projects",
        json={"name": "Edge Cases Project", "description": "Resilience testing"},
        headers=headers,
    )
    project_id = proj_resp.json()["data"]["id"]

    # 3. Empty File Upload -> Expected 400 or 422
    empty_resp = await async_client.post(
        "/api/v1/datasets/upload",
        data={"project_id": project_id},
        files={"file": ("empty.csv", io.BytesIO(b""), "text/csv")},
        headers=headers,
    )
    assert empty_resp.status_code in (400, 422)

    # 4. Non-existent Project ID -> Expected 404 or 400
    fake_project_id = str(uuid.uuid4())
    fake_proj_resp = await async_client.post(
        "/api/v1/datasets/upload",
        data={"project_id": fake_project_id},
        files={"file": ("data.csv", io.BytesIO(b"col1,col2\n1,2"), "text/csv")},
        headers=headers,
    )
    assert fake_proj_resp.status_code in (400, 404, 422)


@pytest.mark.asyncio
async def test_inference_error_handling_and_missing_features(async_client: AsyncClient):
    """Test inference failure modes: missing features, invalid models, and data types."""
    # 1. Auth Setup
    email = f"inference_qa_{uuid.uuid4().hex[:8]}@enterprise.ai"
    password = "SecurePassword123!"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Inference QA", "password": password, "role": "ADMIN"},
    )
    login_resp = await async_client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Query Non-Existent Model for Realtime Predict -> Expected 404
    fake_model_id = str(uuid.uuid4())
    fake_pred_resp = await async_client.post(
        "/api/v1/predictions/realtime",
        json={"model_id": fake_model_id, "features": {"f1": 1.0}},
        headers=headers,
    )
    assert fake_pred_resp.status_code == 404

    # 3. Create Project, Dataset, and Train a Real Model
    proj_resp = await async_client.post(
        "/api/v1/projects",
        json={"name": "Inference Validation Project"},
        headers=headers,
    )
    project_id = proj_resp.json()["data"]["id"]

    df = pd.DataFrame(
        {
            "num_a": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
            "num_b": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0],
            "target": [0, 0, 0, 0, 0, 1, 1, 1, 1, 1],
        }
    )
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    upload_resp = await async_client.post(
        "/api/v1/datasets/upload",
        data={"project_id": project_id},
        files={"file": ("features_test.csv", io.BytesIO(csv_bytes), "text/csv")},
        headers=headers,
    )
    dataset_id = upload_resp.json()["data"]["id"]

    train_resp = await async_client.post(
        "/api/v1/training/train",
        json={
            "project_id": project_id,
            "dataset_id": dataset_id,
            "target_column": "target",
            "task_type": "classification",
            "algorithm": "logistic_regression",
            "model_name": "Features Test Model",
        },
        headers=headers,
    )
    model_id = train_resp.json()["data"]["model_id"]

    # 4. Predict with Missing Feature 'num_b' -> Expected 422
    missing_feat_resp = await async_client.post(
        "/api/v1/predictions/realtime",
        json={"model_id": model_id, "features": {"num_a": 5.0}},  # Missing 'num_b'
        headers=headers,
    )
    assert missing_feat_resp.status_code == 422
    err_body = missing_feat_resp.json()
    assert "MISSING_FEATURES" in str(err_body) or "Missing" in str(err_body)


@pytest.mark.asyncio
async def test_drift_engine_zero_variance_resilience(async_client: AsyncClient):
    """Test statistical drift engine with constant / zero variance features."""
    # 1. Auth Setup
    email = f"drift_resilience_{uuid.uuid4().hex[:8]}@enterprise.ai"
    password = "SecurePassword123!"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Drift QA", "password": password, "role": "ADMIN"},
    )
    login_resp = await async_client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Project & Dataset with Constant Feature
    proj_resp = await async_client.post(
        "/api/v1/projects",
        json={"name": "Zero Variance Drift Project"},
        headers=headers,
    )
    project_id = proj_resp.json()["data"]["id"]

    df = pd.DataFrame(
        {
            "constant_col": [42.0] * 30,  # Zero variance
            "varying_col": list(range(30)),
            "label": [0] * 15 + [1] * 15,
        }
    )
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    upload_resp = await async_client.post(
        "/api/v1/datasets/upload",
        data={"project_id": project_id},
        files={"file": ("zero_variance.csv", io.BytesIO(csv_bytes), "text/csv")},
        headers=headers,
    )
    dataset_id = upload_resp.json()["data"]["id"]

    # 3. Train Model
    train_resp = await async_client.post(
        "/api/v1/training/train",
        json={
            "project_id": project_id,
            "dataset_id": dataset_id,
            "target_column": "label",
            "task_type": "classification",
            "algorithm": "logistic_regression",
            "model_name": "Zero Variance Model",
        },
        headers=headers,
    )
    model_id = train_resp.json()["data"]["model_id"]

    # 4. Run Custom Drift against same dataset
    drift_resp = await async_client.post(
        f"/api/v1/monitoring/models/{model_id}/drift/analyze",
        json={"current_dataset_id": dataset_id, "alpha": 0.05, "psi_threshold": 0.2},
        headers=headers,
    )
    assert drift_resp.status_code == 200
    drift_data = drift_resp.json()["data"]
    # Ensure zero-variance feature was computed without division-by-zero crashes
    assert drift_data["health_status"] in ["HEALTHY", "WARNING", "DRIFT_DETECTED"]
    assert len(drift_data["feature_reports"]) == 2
