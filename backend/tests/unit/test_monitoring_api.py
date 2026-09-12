"""Unit and integration tests for Model Monitoring and Statistical Drift Detection Engine."""

import io
import uuid

import numpy as np
import pandas as pd
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_statistical_drift_and_monitoring_engine(async_client: AsyncClient):
    """Test drift computation: baseline stability (HEALTHY), shifted data detection (DRIFT_DETECTED), KS/PSI tests, and overview."""
    # 1. Register & Login Data Scientist
    ds_email = f"ds_drift_{uuid.uuid4().hex[:8]}@enterprise-ai.io"
    password = "SecurePassword123!"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": ds_email, "full_name": "Drift DS", "password": password, "role": "DATA_SCIENTIST"},
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
        json={"name": "Drift Monitoring Project", "description": "Testing Phase 13"},
        headers=headers,
    )
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["data"]["id"]

    # 3. Create Baseline Dataset (Normal Distribution ~ N(10, 2))
    np.random.seed(42)
    n_samples = 100
    base_f1 = np.random.normal(10.0, 2.0, n_samples)
    base_f2 = np.random.normal(50.0, 5.0, n_samples)
    base_target = (base_f1 * 2 + base_f2 * 0.5 + np.random.normal(0, 1, n_samples) > 45).astype(int)

    df_base = pd.DataFrame({"feat_1": base_f1, "feat_2": base_f2, "target": base_target})
    csv_base_bytes = df_base.to_csv(index=False).encode("utf-8")

    upload_base_resp = await async_client.post(
        "/api/v1/datasets/upload",
        data={"project_id": project_id},
        files={"file": ("baseline_data.csv", io.BytesIO(csv_base_bytes), "text/csv")},
        headers=headers,
    )
    assert upload_base_resp.status_code == 201
    base_dataset_id = upload_base_resp.json()["data"]["id"]

    # 4. Train Model on Baseline Data
    train_resp = await async_client.post(
        "/api/v1/training/train",
        json={
            "project_id": project_id,
            "dataset_id": base_dataset_id,
            "target_column": "target",
            "task_type": "classification",
            "algorithm": "logistic_regression",
            "hyperparameters": {"lr": 0.05},
            "model_name": "Drift Monitor Logistic Regression",
        },
        headers=headers,
    )
    assert train_resp.status_code == 200
    model_id = train_resp.json()["data"]["model_id"]

    # 5. Execute Several Normal Real-Time Inferences (from same baseline distribution)
    for _ in range(5):
        sample_f1 = float(np.random.normal(10.0, 2.0))
        sample_f2 = float(np.random.normal(50.0, 5.0))
        await async_client.post(
            "/api/v1/predictions/realtime",
            json={"model_id": model_id, "features": {"feat_1": sample_f1, "feat_2": sample_f2}},
            headers=headers,
        )

    # 6. Test GET /monitoring/models/{model_id}/drift (Should be HEALTHY or low PSI)
    drift_resp = await async_client.get(
        f"/api/v1/monitoring/models/{model_id}/drift",
        headers=headers,
    )
    assert drift_resp.status_code == 200
    drift_data = drift_resp.json()["data"]
    assert drift_data["model_id"] == model_id
    assert drift_data["health_status"] in ["HEALTHY", "WARNING"]
    assert len(drift_data["feature_reports"]) == 2
    assert all("histogram_bins" in fr for fr in drift_data["feature_reports"])

    # 7. Upload Heavily Shifted Evaluation Dataset (feat_1 ~ N(50, 10), feat_2 ~ N(200, 20))
    shift_f1 = np.random.normal(50.0, 10.0, n_samples)
    shift_f2 = np.random.normal(200.0, 20.0, n_samples)
    df_shift = pd.DataFrame({"feat_1": shift_f1, "feat_2": shift_f2, "target": base_target})
    csv_shift_bytes = df_shift.to_csv(index=False).encode("utf-8")

    upload_shift_resp = await async_client.post(
        "/api/v1/datasets/upload",
        data={"project_id": project_id},
        files={"file": ("shifted_data.csv", io.BytesIO(csv_shift_bytes), "text/csv")},
        headers=headers,
    )
    assert upload_shift_resp.status_code == 201
    shift_dataset_id = upload_shift_resp.json()["data"]["id"]

    # 8. Trigger Custom Drift Analysis Against Shifted Dataset
    custom_drift_resp = await async_client.post(
        f"/api/v1/monitoring/models/{model_id}/drift/analyze",
        json={"current_dataset_id": shift_dataset_id, "alpha": 0.05, "psi_threshold": 0.2},
        headers=headers,
    )
    assert custom_drift_resp.status_code == 200
    shift_drift_data = custom_drift_resp.json()["data"]
    assert shift_drift_data["health_status"] == "DRIFT_DETECTED"
    assert shift_drift_data["drifted_features_count"] >= 1
    assert shift_drift_data["max_psi"] >= 0.2
    assert shift_drift_data["feature_reports"][0]["drift_detected"] is True
    assert shift_drift_data["feature_reports"][0]["p_value"] < 0.05
    assert len(shift_drift_data["feature_reports"][0]["histogram_bins"]) > 0

    # 9. Test Monitoring Overview
    overview_resp = await async_client.get(
        f"/api/v1/monitoring/overview?project_id={project_id}",
        headers=headers,
    )
    assert overview_resp.status_code == 200
    overview = overview_resp.json()["data"]
    assert len(overview) >= 1
    matched = next((m for m in overview if m["model_id"] == model_id), None)
    assert matched is not None
    assert matched["total_inferences"] >= 5
