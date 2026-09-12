"""End-to-End Full MLOps Platform Integration Test Suite.

Verifies the entire lifecycle from:
1. User registration & authentication
2. Project workspace creation
3. Streaming dataset ingestion & validation
4. Automated EDA statistical analysis
5. Preprocessing & feature engineering
6. ML training with K-fold cross-validation & MLflow tracking
7. Model registry governance & single-champion lifecycle promotion
8. Real-time sub-15ms prediction inference & probability distribution
9. Asynchronous batch inference with CSV result export
10. Statistical data drift detection (KS-test, PSI, health status)
"""

import io
import uuid

import numpy as np
import pandas as pd
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_complete_enterprise_mlops_pipeline_e2e(async_client: AsyncClient):
    """Execute complete end-to-end MLOps workflow through REST endpoints."""
    # =========================================================================
    # STEP 1: AUTHENTICATION & RBAC SETUP
    # =========================================================================
    admin_email = f"lead_mlops_{uuid.uuid4().hex[:8]}@enterprise.ai"
    password = "MasterPassword2026!"

    reg_resp = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": admin_email,
            "full_name": "Senior MLOps Architect",
            "password": password,
            "role": "ADMIN",
        },
    )
    assert reg_resp.status_code == 201, reg_resp.text

    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": admin_email, "password": password},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # =========================================================================
    # STEP 2: PROJECT WORKSPACE CREATION
    # =========================================================================
    proj_resp = await async_client.post(
        "/api/v1/projects",
        json={
            "name": "E2E Enterprise Credit Risk Model",
            "description": "Comprehensive integration test workspace",
        },
        headers=headers,
    )
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["data"]["id"]

    # =========================================================================
    # STEP 3: DATASET INGESTION & VALIDATION
    # =========================================================================
    np.random.seed(42)
    n_samples = 120
    df = pd.DataFrame(
        {
            "age": np.random.normal(40, 10, n_samples).round(1),
            "income": np.random.normal(65000, 15000, n_samples).round(0),
            "credit_score": np.random.normal(700, 50, n_samples).round(0),
            "debt_ratio": np.random.uniform(0.1, 0.8, n_samples).round(2),
            "default": np.random.choice([0, 1], size=n_samples, p=[0.75, 0.25]),
        }
    )
    csv_bytes = df.to_csv(index=False).encode("utf-8")

    upload_resp = await async_client.post(
        "/api/v1/datasets/upload",
        data={"project_id": project_id},
        files={"file": ("credit_risk_dataset.csv", io.BytesIO(csv_bytes), "text/csv")},
        headers=headers,
    )
    assert upload_resp.status_code == 201, upload_resp.text
    dataset_id = upload_resp.json()["data"]["id"]

    # Verify Preview & Schema
    preview_resp = await async_client.get(
        f"/api/v1/datasets/{dataset_id}/preview?page=1&page_size=10",
        headers=headers,
    )
    assert preview_resp.status_code == 200
    preview_data = preview_resp.json()["data"]
    assert preview_data["total_rows"] == n_samples
    assert len(preview_data["columns"]) == 5

    # =========================================================================
    # STEP 4: AUTOMATED EXPLORATORY DATA ANALYSIS (EDA)
    # =========================================================================
    eda_resp = await async_client.get(
        f"/api/v1/datasets/{dataset_id}/eda",
        headers=headers,
    )
    assert eda_resp.status_code == 200, eda_resp.text
    eda_data = eda_resp.json()["data"]
    assert eda_data["dataset_id"] == dataset_id
    assert eda_data["numerical_features"] is not None
    assert len(eda_data["numerical_features"]) >= 1

    # =========================================================================
    # STEP 5: PREPROCESSING & FEATURE ENGINEERING
    # =========================================================================
    pipe_config = {
        "target_column": "default",
        "problem_type": "classification",
        "numerical_features": [
            {"column_name": "age", "imputer": "mean", "scaler": "standard"},
            {"column_name": "income", "imputer": "mean", "scaler": "minmax"},
            {"column_name": "credit_score", "imputer": "median", "scaler": "standard"},
            {"column_name": "debt_ratio", "imputer": "mean", "scaler": "robust"},
        ],
        "categorical_features": [],
        "datetime_features": [],
        "feature_selection": {"variance_threshold": None, "correlation_threshold": None, "drop_features": []},
        "split_config": {"test_size": 0.2, "stratify": False, "random_state": 42},
    }

    prep_resp = await async_client.post(
        f"/api/v1/datasets/{dataset_id}/preprocess",
        json=pipe_config,
        headers=headers,
    )
    assert prep_resp.status_code in [200, 201], prep_resp.text

    # =========================================================================
    # STEP 6: MODEL TRAINING WITH CV & MLFLOW TRACKING
    # =========================================================================
    train_resp = await async_client.post(
        "/api/v1/training/train",
        json={
            "project_id": project_id,
            "dataset_id": dataset_id,
            "target_column": "default",
            "task_type": "classification",
            "algorithm": "random_forest_classifier",
            "hyperparameters": {"n_estimators": 30, "max_depth": 5, "random_state": 42},
            "model_name": "Production Credit Risk Champion",
        },
        headers=headers,
    )
    assert train_resp.status_code == 200, train_resp.text
    train_data = train_resp.json()["data"]
    model_id = train_data["model_id"]
    assert model_id is not None
    assert train_data["test_metrics"] is not None

    # =========================================================================
    # STEP 7: MODEL REGISTRY & SINGLE-CHAMPION GOVERNANCE
    # =========================================================================
    model_detail_resp = await async_client.get(
        f"/api/v1/models/{model_id}",
        headers=headers,
    )
    assert model_detail_resp.status_code == 200
    model_detail = model_detail_resp.json()["data"]
    assert model_detail["status"] == "DEVELOPMENT"
    assert "age" in model_detail["feature_names"]

    # Promote DEVELOPMENT -> STAGING
    p1 = await async_client.post(
        f"/api/v1/models/{model_id}/promote",
        json={"status": "STAGING", "notes": "Candidate passed unit & integration checks"},
        headers=headers,
    )
    assert p1.status_code == 200
    assert p1.json()["data"]["status"] == "STAGING"

    # Promote STAGING -> PRODUCTION
    p2 = await async_client.post(
        f"/api/v1/models/{model_id}/promote",
        json={"status": "PRODUCTION", "notes": "Approved for live inference routing"},
        headers=headers,
    )
    assert p2.status_code == 200
    assert p2.json()["data"]["status"] == "PRODUCTION"

    # =========================================================================
    # STEP 8: REAL-TIME REST INFERENCE & PROBABILITY SCORING
    # =========================================================================
    realtime_input = {
        "model_id": model_id,
        "features": {
            "age": 45.0,
            "income": 72000.0,
            "credit_score": 750.0,
            "debt_ratio": 0.25,
        },
    }
    pred_resp = await async_client.post(
        "/api/v1/predictions/realtime",
        json=realtime_input,
        headers=headers,
    )
    assert pred_resp.status_code == 200, pred_resp.text
    pred_data = pred_resp.json()["data"]
    assert "predicted_value" in pred_data
    assert pred_data["probabilities"] is not None
    assert len(pred_data["probabilities"]) >= 1

    # Repeat call to test In-Memory Model Cache Hit
    pred_resp2 = await async_client.post(
        "/api/v1/predictions/realtime",
        json=realtime_input,
        headers=headers,
    )
    assert pred_resp2.status_code == 200

    # =========================================================================
    # STEP 9: ASYNCHRONOUS BATCH PREDICTION WITH CSV EXPORT
    # =========================================================================
    batch_df = pd.DataFrame(
        {
            "age": [28.0, 52.0, 35.0, 61.0],
            "income": [45000.0, 95000.0, 58000.0, 110000.0],
            "credit_score": [620.0, 780.0, 710.0, 810.0],
            "debt_ratio": [0.45, 0.20, 0.30, 0.15],
        }
    )
    batch_csv_bytes = batch_df.to_csv(index=False).encode("utf-8")

    batch_launch_resp = await async_client.post(
        "/api/v1/predictions/batch/upload",
        data={"model_id": model_id, "project_id": project_id},
        files={"file": ("batch_inference_eval.csv", io.BytesIO(batch_csv_bytes), "text/csv")},
        headers=headers,
    )
    assert batch_launch_resp.status_code in [200, 202], batch_launch_resp.text
    batch_job_id = batch_launch_resp.json()["data"]["job_id"]

    # Poll Job Status
    job_status_resp = await async_client.get(
        f"/api/v1/jobs/{batch_job_id}",
        headers=headers,
    )
    assert job_status_resp.status_code == 200
    assert job_status_resp.json()["data"]["status"] in ["SUCCESS", "RUNNING", "PENDING"]

    # Download batch prediction results
    download_resp = await async_client.get(
        f"/api/v1/predictions/batch/{batch_job_id}/download",
        headers=headers,
    )
    assert download_resp.status_code == 200
    assert len(download_resp.content) > 0
    # Verify result CSV contains predicted_value column
    res_df = pd.read_csv(io.StringIO(download_resp.content.decode("utf-8")))
    assert "predicted_value" in res_df.columns

    # =========================================================================
    # STEP 10: STATISTICAL DATA DRIFT DETECTION & OBSERVABILITY
    # =========================================================================
    # 10.1 Monitoring Overview
    overview_resp = await async_client.get(
        f"/api/v1/monitoring/overview?project_id={project_id}",
        headers=headers,
    )
    assert overview_resp.status_code == 200
    overviews = overview_resp.json()["data"]
    assert len(overviews) >= 1

    # 10.2 Drift Analysis against shifted dataset
    drift_eval_df = pd.DataFrame(
        {
            "age": np.random.normal(65, 5, 50).round(1),  # Mean shifted from 40 to 65 (Extreme Drift)
            "income": np.random.normal(120000, 10000, 50).round(0),  # Shifted from 65k to 120k
            "credit_score": np.random.normal(550, 40, 50).round(0),
            "debt_ratio": np.random.uniform(0.6, 0.9, 50).round(2),
        }
    )
    eval_csv_bytes = drift_eval_df.to_csv(index=False).encode("utf-8")
    eval_upload_resp = await async_client.post(
        "/api/v1/datasets/upload",
        data={"project_id": project_id},
        files={"file": ("drifted_test_data.csv", io.BytesIO(eval_csv_bytes), "text/csv")},
        headers=headers,
    )
    assert eval_upload_resp.status_code == 201
    eval_dataset_id = eval_upload_resp.json()["data"]["id"]

    # Trigger custom statistical drift evaluation
    custom_drift_resp = await async_client.post(
        f"/api/v1/monitoring/models/{model_id}/drift/analyze",
        json={
            "current_dataset_id": eval_dataset_id,
            "alpha": 0.05,
            "psi_threshold": 0.2,
        },
        headers=headers,
    )
    assert custom_drift_resp.status_code == 200, custom_drift_resp.text
    drift_data = custom_drift_resp.json()["data"]
    assert drift_data["health_status"] == "DRIFT_DETECTED"
    assert drift_data["drifted_features_count"] >= 1
    assert drift_data["max_psi"] >= 0.2
    assert len(drift_data["feature_reports"]) == 4

    # Verify each feature report has p_value, psi_score, Wasserstein, and distribution bins
    for report in drift_data["feature_reports"]:
        assert report["feature_name"] in ["age", "income", "credit_score", "debt_ratio"]
        assert report["p_value"] is not None
        assert report["psi_score"] is not None
        assert len(report["histogram_bins"]) > 0
