"""Unit and integration tests for Model Registry, Lifecycle Governance, Leaderboard, and Downloads."""

import io
import uuid

import pandas as pd
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_model_registry_lifecycle_and_governance(async_client: AsyncClient):
    """Test full model registry flow: training -> registry list -> details -> promotion -> audit logs -> leaderboard."""
    # 1. Register & Login Data Scientist
    ds_email = f"lead_ds_{uuid.uuid4().hex[:8]}@enterprise-ai.io"
    password = "SecurePassword123!"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": ds_email, "full_name": "Lead DS", "password": password, "role": "DATA_SCIENTIST"},
    )
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": ds_email, "password": password},
    )
    token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Register Standard User for RBAC test
    user_email = f"viewer_{uuid.uuid4().hex[:8]}@enterprise-ai.io"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": user_email, "full_name": "Viewer", "password": password, "role": "USER"},
    )
    user_login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": user_email, "password": password},
    )
    user_token = user_login_resp.json()["data"]["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}

    # 3. Create Project
    proj_resp = await async_client.post(
        "/api/v1/projects",
        json={"name": "Model Registry Governance Project", "description": "Testing Phase 11"},
        headers=headers,
    )
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["data"]["id"]

    # 4. Upload Dataset
    df = pd.DataFrame(
        {
            "feat1": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0],
            "feat2": [2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0],
            "label": [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1],
        }
    )
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    upload_resp = await async_client.post(
        "/api/v1/datasets/upload",
        data={"project_id": project_id},
        files={"file": ("registry_test.csv", io.BytesIO(csv_bytes), "text/csv")},
        headers=headers,
    )
    assert upload_resp.status_code == 201
    dataset_id = upload_resp.json()["data"]["id"]

    # 5. Train Model 1 (Logistic Regression)
    train1_resp = await async_client.post(
        "/api/v1/training/train",
        json={
            "project_id": project_id,
            "dataset_id": dataset_id,
            "target_column": "label",
            "task_type": "classification",
            "algorithm": "logistic_regression",
            "hyperparameters": {"lr": 0.05, "max_iter": 100},
            "model_name": "Governance Logistic Regression",
        },
        headers=headers,
    )
    assert train1_resp.status_code == 200
    model1_id = train1_resp.json()["data"]["model_id"]

    # 6. Train Model 2 (Random Forest)
    train2_resp = await async_client.post(
        "/api/v1/training/train",
        json={
            "project_id": project_id,
            "dataset_id": dataset_id,
            "target_column": "label",
            "task_type": "classification",
            "algorithm": "random_forest_classifier",
            "hyperparameters": {"n_estimators": 25, "max_depth": 5},
            "model_name": "Governance Random Forest",
        },
        headers=headers,
    )
    assert train2_resp.status_code == 200
    model2_id = train2_resp.json()["data"]["model_id"]

    # 7. List Models via /api/v1/models
    list_resp = await async_client.get(
        f"/api/v1/models?project_id={project_id}",
        headers=headers,
    )
    assert list_resp.status_code == 200
    models_list = list_resp.json()["data"]
    assert len(models_list) >= 2
    assert any(m["id"] == model1_id for m in models_list)
    assert any(m["id"] == model2_id for m in models_list)

    # 8. Get Model Details via /api/v1/models/{id}
    detail_resp = await async_client.get(
        f"/api/v1/models/{model1_id}",
        headers=headers,
    )
    assert detail_resp.status_code == 200
    detail = detail_resp.json()["data"]
    assert detail["id"] == model1_id
    assert detail["name"] == "Governance Logistic Regression"
    assert detail["status"] == "DEVELOPMENT"
    assert detail["metrics"] is not None
    assert len(detail["feature_names"]) >= 1

    # 9. Test RBAC: Standard USER cannot promote model
    user_promote_resp = await async_client.post(
        f"/api/v1/models/{model1_id}/promote",
        json={"status": "STAGING", "notes": "Unauthorized attempt"},
        headers=user_headers,
    )
    assert user_promote_resp.status_code == 403

    # 10. Promote Model 1 to STAGING by Data Scientist
    promote_stage_resp = await async_client.post(
        f"/api/v1/models/{model1_id}/promote",
        json={"status": "STAGING", "notes": "Validated in staging environment"},
        headers=headers,
    )
    assert promote_stage_resp.status_code == 200
    assert promote_stage_resp.json()["data"]["status"] == "STAGING"

    # 11. Promote Model 1 to PRODUCTION
    promote_prod_resp = await async_client.post(
        f"/api/v1/models/{model1_id}/promote",
        json={"status": "PRODUCTION", "notes": "Passed all quality benchmarks"},
        headers=headers,
    )
    assert promote_prod_resp.status_code == 200
    assert promote_prod_resp.json()["data"]["status"] == "PRODUCTION"

    # 12. Promote Model 2 to PRODUCTION (Model 1 should automatically be demoted to STAGING)
    promote_prod2_resp = await async_client.post(
        f"/api/v1/models/{model2_id}/promote",
        json={"status": "PRODUCTION", "notes": "New superior champion model"},
        headers=headers,
    )
    assert promote_prod2_resp.status_code == 200
    assert promote_prod2_resp.json()["data"]["status"] == "PRODUCTION"

    # Verify Model 1 was demoted to STAGING
    m1_detail = (await async_client.get(f"/api/v1/models/{model1_id}", headers=headers)).json()["data"]
    assert m1_detail["status"] == "STAGING"

    # Verify Audit History has recorded transitions
    assert len(m1_detail["audit_history"]) >= 2

    # 13. Leaderboard check
    lb_resp = await async_client.get(
        f"/api/v1/models/leaderboard?project_id={project_id}",
        headers=headers,
    )
    assert lb_resp.status_code == 200
    leaderboard = lb_resp.json()["data"]
    assert len(leaderboard) >= 2
    assert leaderboard[0]["rank"] == 1
    assert leaderboard[0]["primary_metric_name"] == "accuracy"

    # 14. Compare Models
    comp_resp = await async_client.post(
        "/api/v1/models/compare",
        json={"model_ids": [model1_id, model2_id]},
        headers=headers,
    )
    assert comp_resp.status_code == 200
    comp_data = comp_resp.json()["data"]
    assert len(comp_data["models"]) == 2
    assert "accuracy" in comp_data["all_metrics"]

    # 15. Download Artifact
    dl_resp = await async_client.get(
        f"/api/v1/models/{model1_id}/download",
        headers=headers,
    )
    assert dl_resp.status_code == 200
    assert len(dl_resp.content) > 0

    # 16. Archive Model
    archive_resp = await async_client.post(
        f"/api/v1/models/{model1_id}/archive",
        headers=headers,
    )
    assert archive_resp.status_code == 200
    assert archive_resp.json()["data"]["status"] == "ARCHIVED"
