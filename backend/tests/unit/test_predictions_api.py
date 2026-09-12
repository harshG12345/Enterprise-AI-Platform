"""Unit and integration tests for Real-Time and Asynchronous Batch Prediction Engine."""

import io
import uuid

import pandas as pd
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_realtime_and_batch_prediction_engine(async_client: AsyncClient):
    """Test full prediction lifecycle: real-time inference, missing feature validation, batch predictions, and CSV download."""
    # 1. Register & Login Data Scientist
    ds_email = f"ds_inference_{uuid.uuid4().hex[:8]}@enterprise-ai.io"
    password = "SecurePassword123!"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": ds_email, "full_name": "Inference DS", "password": password, "role": "DATA_SCIENTIST"},
    )
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": ds_email, "password": password},
    )
    token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Project
    proj_resp = await async_client.post(
        "/api/v1/projects",
        json={"name": "Inference Engine Test Project", "description": "Testing Phase 12"},
        headers=headers,
    )
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["data"]["id"]

    # 3. Upload Classification Dataset
    df_cls = pd.DataFrame(
        {
            "feat_a": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0],
            "feat_b": [2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0],
            "target": [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1],
        }
    )
    csv_cls_bytes = df_cls.to_csv(index=False).encode("utf-8")
    upload_cls_resp = await async_client.post(
        "/api/v1/datasets/upload",
        data={"project_id": project_id},
        files={"file": ("cls_data.csv", io.BytesIO(csv_cls_bytes), "text/csv")},
        headers=headers,
    )
    assert upload_cls_resp.status_code == 201
    cls_dataset_id = upload_cls_resp.json()["data"]["id"]

    # 4. Train Classification Model (Logistic Regression)
    train_cls_resp = await async_client.post(
        "/api/v1/training/train",
        json={
            "project_id": project_id,
            "dataset_id": cls_dataset_id,
            "target_column": "target",
            "task_type": "classification",
            "algorithm": "logistic_regression",
            "hyperparameters": {"lr": 0.05, "max_iter": 100},
            "model_name": "Inference Classifier",
        },
        headers=headers,
    )
    assert train_cls_resp.status_code == 200
    cls_model_id = train_cls_resp.json()["data"]["model_id"]

    # 5. Train Regression Model (Ridge Regression)
    df_reg = pd.DataFrame(
        {
            "sqft": [500.0, 800.0, 1200.0, 1500.0, 1800.0, 2200.0, 2500.0, 3000.0, 3500.0, 4000.0],
            "bedrooms": [1.0, 2.0, 2.0, 3.0, 3.0, 4.0, 4.0, 5.0, 5.0, 6.0],
            "price": [150.0, 220.0, 310.0, 390.0, 450.0, 540.0, 620.0, 710.0, 830.0, 950.0],
        }
    )
    csv_reg_bytes = df_reg.to_csv(index=False).encode("utf-8")
    upload_reg_resp = await async_client.post(
        "/api/v1/datasets/upload",
        data={"project_id": project_id},
        files={"file": ("reg_data.csv", io.BytesIO(csv_reg_bytes), "text/csv")},
        headers=headers,
    )
    assert upload_reg_resp.status_code == 201
    reg_dataset_id = upload_reg_resp.json()["data"]["id"]

    train_reg_resp = await async_client.post(
        "/api/v1/training/train",
        json={
            "project_id": project_id,
            "dataset_id": reg_dataset_id,
            "target_column": "price",
            "task_type": "regression",
            "algorithm": "ridge_regression",
            "hyperparameters": {"alpha": 1.0},
            "model_name": "Inference Regressor",
        },
        headers=headers,
    )
    assert train_reg_resp.status_code == 200
    reg_model_id = train_reg_resp.json()["data"]["model_id"]

    # 6. Test Real-time Classification Inference
    rt_cls_resp = await async_client.post(
        "/api/v1/predictions/realtime",
        json={
            "model_id": cls_model_id,
            "features": {"feat_a": 10.5, "feat_b": 11.5},
            "include_probabilities": True,
        },
        headers=headers,
    )
    assert rt_cls_resp.status_code == 200
    rt_cls_data = rt_cls_resp.json()["data"]
    assert rt_cls_data["model_id"] == cls_model_id
    assert rt_cls_data["task_type"] == "classification"
    assert rt_cls_data["predicted_value"] in [0, 1]
    assert rt_cls_data["latency_ms"] >= 0.0
    assert rt_cls_data["probabilities"] is not None
    assert len(rt_cls_data["probabilities"]) >= 2

    # 7. Test Direct Model Inference Endpoint
    direct_resp = await async_client.post(
        f"/api/v1/predictions/models/{cls_model_id}/predict",
        json={"feat_a": 1.5, "feat_b": 2.5},
        headers=headers,
    )
    assert direct_resp.status_code == 200
    assert direct_resp.json()["data"]["predicted_value"] in [0, 1]

    # 8. Test Missing Required Features Validation (422)
    missing_resp = await async_client.post(
        "/api/v1/predictions/realtime",
        json={
            "model_id": cls_model_id,
            "features": {"feat_a": 5.0},  # missing feat_b
        },
        headers=headers,
    )
    assert missing_resp.status_code == 422
    err = missing_resp.json()["error"]
    assert err["code"] == "MISSING_FEATURES"

    # 9. Test Real-time Regression Inference
    rt_reg_resp = await async_client.post(
        "/api/v1/predictions/realtime",
        json={
            "model_id": reg_model_id,
            "features": {"sqft": 2000.0, "bedrooms": 3.0},
        },
        headers=headers,
    )
    assert rt_reg_resp.status_code == 200
    rt_reg_data = rt_reg_resp.json()["data"]
    assert rt_reg_data["model_id"] == reg_model_id
    assert rt_reg_data["task_type"] == "regression"
    assert isinstance(rt_reg_data["predicted_value"], (int, float))
    assert rt_reg_data["predicted_value"] > 0

    # 10. Test Prediction History and Stats
    hist_resp = await async_client.get(
        f"/api/v1/predictions?project_id={project_id}",
        headers=headers,
    )
    assert hist_resp.status_code == 200
    hist = hist_resp.json()["data"]
    assert len(hist) >= 3

    stats_resp = await async_client.get(
        f"/api/v1/predictions/stats?project_id={project_id}",
        headers=headers,
    )
    assert stats_resp.status_code == 200
    stats = stats_resp.json()["data"]
    assert stats["total_predictions"] >= 3
    assert stats["average_latency_ms"] >= 0

    # 11. Test Batch Prediction on Existing Dataset
    batch_resp = await async_client.post(
        "/api/v1/predictions/batch",
        json={
            "model_id": cls_model_id,
            "project_id": project_id,
            "dataset_id": cls_dataset_id,
        },
        headers=headers,
    )
    assert batch_resp.status_code == 202
    job_id = batch_resp.json()["data"]["job_id"]

    # Check batch job completion and download result CSV
    dl_resp = await async_client.get(
        f"/api/v1/predictions/batch/{job_id}/download",
        headers=headers,
    )
    assert dl_resp.status_code == 200
    csv_text = dl_resp.content.decode("utf-8")
    assert "predicted_value" in csv_text
    assert "feat_a" in csv_text

    # 12. Test Batch Prediction via Multipart File Upload
    batch_upload_df = pd.DataFrame(
        {
            "sqft": [1100.0, 2400.0, 3100.0],
            "bedrooms": [2.0, 4.0, 5.0],
        }
    )
    batch_upload_csv = batch_upload_df.to_csv(index=False).encode("utf-8")

    batch_up_resp = await async_client.post(
        "/api/v1/predictions/batch/upload",
        data={"model_id": reg_model_id, "project_id": project_id},
        files={"file": ("new_batch.csv", io.BytesIO(batch_upload_csv), "text/csv")},
        headers=headers,
    )
    assert batch_up_resp.status_code == 202
    up_job_id = batch_up_resp.json()["data"]["job_id"]

    # Download batch upload output CSV
    dl_up_resp = await async_client.get(
        f"/api/v1/predictions/batch/{up_job_id}/download",
        headers=headers,
    )
    assert dl_up_resp.status_code == 200
    up_csv_text = dl_up_resp.content.decode("utf-8")
    assert "predicted_value" in up_csv_text
    assert "sqft" in up_csv_text
