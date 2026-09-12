"""Unit and integration tests for MLflow Experiment Tracking, Runs, and Comparison Matrices."""

import io
import uuid

import pandas as pd
import pytest
from httpx import AsyncClient

from app.ml.tracker import MLflowTracker


def test_tracker_experiment_lifecycle(tmp_path):
    """Verify MLflowTracker creates experiments, logs params/metrics/tags/artifacts, and closes runs."""
    tracker = MLflowTracker(base_dir=str(tmp_path / "mlflow"))

    # 1. Create experiment
    exp_id = tracker.create_experiment(name="Test Experiment A", tags={"env": "testing"})
    assert exp_id is not None
    exp_meta = tracker.get_experiment(exp_id)
    assert exp_meta["name"] == "Test Experiment A"

    # 2. Start run
    run_id = tracker.start_run(experiment_id=exp_id, run_name="Run Alpha", tags={"model": "RandomForest"})
    assert run_id is not None

    # 3. Log parameters & metrics
    tracker.log_param(run_id, "n_estimators", 50)
    tracker.log_param(run_id, "max_depth", 6)
    tracker.log_metric(run_id, "accuracy", 0.92, step=1)
    tracker.log_metric(run_id, "accuracy", 0.95, step=2)
    tracker.log_metric(run_id, "f1_score", 0.94, step=2)

    # 4. Log artifact
    tracker.log_dict(run_id, {"confusion": [[50, 2], [3, 45]]}, "evaluation/confusion_matrix.json")

    # 5. End run
    tracker.end_run(run_id, status="FINISHED")

    # 6. Retrieve run
    run = tracker.get_run(run_id)
    assert run is not None
    assert run["run_name"] == "Run Alpha"
    assert run["status"] == "FINISHED"
    assert run["parameters"]["n_estimators"] == "50"
    assert run["parameters"]["max_depth"] == "6"
    assert run["metrics"]["accuracy"] == 0.95
    assert run["metrics"]["f1_score"] == 0.94
    assert run["tags"]["model"] == "RandomForest"
    assert len(run["artifacts"]) >= 1


def test_tracker_metric_history(tmp_path):
    """Verify step-wise learning curve metric history tracking."""
    tracker = MLflowTracker(base_dir=str(tmp_path / "mlflow"))
    exp_id = tracker.create_experiment(name="Learning Curve Exp")
    run_id = tracker.start_run(experiment_id=exp_id, run_name="Epoch Run")

    # Log 5 steps
    losses = [0.8, 0.6, 0.45, 0.3, 0.22]
    for step, loss in enumerate(losses, start=1):
        tracker.log_metric(run_id, "train_loss", loss, step=step)

    tracker.end_run(run_id)

    history = tracker.get_metric_history(run_id, "train_loss")
    assert len(history) == 5
    assert history[0]["step"] == 1
    assert history[0]["value"] == 0.8
    assert history[-1]["step"] == 5
    assert history[-1]["value"] == 0.22


@pytest.mark.asyncio
async def test_experiments_api_workflow(async_client: AsyncClient):
    """End-to-end API test: register -> create project -> create experiment -> start runs -> compare."""
    # 1. Register & Login
    email = f"experimenter_{uuid.uuid4().hex[:8]}@enterprise-ai.io"
    password = "SecurePassword123!"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "MLOps Lead", "password": password, "role": "DATA_SCIENTIST"},
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
        json={"name": "MLflow Experiment Tracking Project", "description": "Testing Phase 9"},
        headers=headers,
    )
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["data"]["id"]

    # 3. Create Experiment
    exp_resp = await async_client.post(
        "/api/v1/experiments",
        json={
            "project_id": project_id,
            "name": "Hyperparameter Sweep v1",
            "tags": {"objective": "benchmark"},
        },
        headers=headers,
    )
    assert exp_resp.status_code == 201
    exp_data = exp_resp.json()["data"]
    exp_id = exp_data["id"]
    assert exp_data["name"] == "Hyperparameter Sweep v1"

    # 4. Create Run 1
    run1_resp = await async_client.post(
        f"/api/v1/experiments/{exp_id}/runs",
        json={
            "experiment_id": exp_id,
            "run_name": "RF-Depth-4",
            "parameters": {"n_estimators": 50, "max_depth": 4, "criterion": "gini"},
            "tags": {"version": "v1.0"},
        },
        headers=headers,
    )
    assert run1_resp.status_code == 201
    run1_id = run1_resp.json()["data"]["run_id"]

    # 5. Create Run 2
    run2_resp = await async_client.post(
        f"/api/v1/experiments/{exp_id}/runs",
        json={
            "experiment_id": exp_id,
            "run_name": "RF-Depth-10",
            "parameters": {"n_estimators": 50, "max_depth": 10, "criterion": "entropy"},
            "tags": {"version": "v1.1"},
        },
        headers=headers,
    )
    assert run2_resp.status_code == 201
    run2_id = run2_resp.json()["data"]["run_id"]

    # 6. List Runs
    list_runs_resp = await async_client.get(
        f"/api/v1/experiments/{exp_id}/runs",
        headers=headers,
    )
    assert list_runs_resp.status_code == 200
    runs = list_runs_resp.json()["data"]
    assert len(runs) >= 2

    # 7. Compare Runs
    comp_resp = await async_client.post(
        "/api/v1/experiments/compare",
        json={"run_ids": [run1_id, run2_id]},
        headers=headers,
    )
    assert comp_resp.status_code == 200
    comp_data = comp_resp.json()["data"]
    assert len(comp_data["runs"]) == 2
    assert "n_estimators" in comp_data["common_parameters"]
    assert "max_depth" in comp_data["differing_parameters"]


@pytest.mark.asyncio
async def test_training_service_mlflow_run_link(async_client: AsyncClient):
    """Verify that training automatically records an MLflow run and links the ID."""
    email = f"trainer_mlflow_{uuid.uuid4().hex[:8]}@enterprise-ai.io"
    password = "SecurePassword123!"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Trainer", "password": password, "role": "DATA_SCIENTIST"},
    )
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    proj_resp = await async_client.post(
        "/api/v1/projects",
        json={"name": "MLflow Auto Run Project", "description": "Phase 9 test"},
        headers=headers,
    )
    project_id = proj_resp.json()["data"]["id"]

    df = pd.DataFrame(
        {
            "feat1": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
            "feat2": [2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0],
            "target": [0, 0, 0, 0, 0, 1, 1, 1, 1, 1],
        }
    )
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    upload_resp = await async_client.post(
        "/api/v1/datasets/upload",
        data={"project_id": project_id},
        files={"file": ("mlflow_test.csv", io.BytesIO(csv_bytes), "text/csv")},
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
            "hyperparameters": {"lr": 0.05, "max_iter": 100},
            "model_name": "MLflow Tracked Logistic Regression",
        },
        headers=headers,
    )
    assert train_resp.status_code == 200
    assert train_resp.json()["data"]["status"] == "SUCCESS"

    # Verify that an experiment was automatically created for the project
    exp_list_resp = await async_client.get(
        f"/api/v1/experiments?project_id={project_id}",
        headers=headers,
    )
    assert exp_list_resp.status_code == 200
    experiments = exp_list_resp.json()["data"]
    assert len(experiments) >= 1
    exp_id = experiments[0]["id"]

    # Verify that the run was recorded
    runs_resp = await async_client.get(
        f"/api/v1/experiments/{exp_id}/runs",
        headers=headers,
    )
    assert runs_resp.status_code == 200
    runs = runs_resp.json()["data"]
    assert len(runs) >= 1
    assert runs[0]["parameters"]["algorithm"] == "logistic_regression"
    assert "accuracy" in runs[0]["metrics"]
    assert len(runs[0]["artifacts"]) >= 1
