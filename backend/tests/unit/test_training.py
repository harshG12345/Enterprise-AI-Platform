"""Unit and integration tests for ML Training & Cross-Validation Engine."""

import io
import uuid

import numpy as np
import pandas as pd
import pytest
from httpx import AsyncClient

from app.ml.models import (
    GradientBoostingModel,
    LogisticRegressionModel,
)
from app.ml.trainer import ModelTrainer
from app.schemas.training import (
    CrossValidationConfig,
)


def test_algorithms_catalog():
    """Verify that all classification and regression algorithms are registered with schemas."""
    algos = ModelTrainer.list_available_algorithms()
    assert len(algos) >= 10
    names = [a.algorithm for a in algos]
    assert "random_forest_classifier" in names
    assert "gradient_boosting_classifier" in names
    assert "logistic_regression" in names
    assert "random_forest_regressor" in names
    assert "linear_regression" in names

    for a in algos:
        assert len(a.name) > 0
        assert a.task_type in ("classification", "regression")
        assert isinstance(a.default_hyperparameters, dict)
        assert isinstance(a.hyperparameter_schema, dict)


def test_random_forest_classification_metrics():
    """Verify RandomForestClassifier training, feature importances, and evaluation metrics."""
    np.random.seed(42)
    # 100 samples, 4 features
    X = np.random.randn(100, 4)
    # Informative target based on feature 0 and 1
    y = ((X[:, 0] * 2.0 + X[:, 1] * 1.5) > 0).astype(int)

    X_tr, X_te = X[:80], X[80:]
    y_tr, y_te = y[:80], y[80:]
    feat_names = ["feat_a", "feat_b", "feat_c", "feat_d"]

    res = ModelTrainer.train_and_evaluate(
        algorithm="random_forest_classifier",
        hyperparameters={"n_estimators": 20, "max_depth": 5},
        X_train=X_tr,
        y_train=y_tr,
        X_test=X_te,
        y_test=y_te,
        feature_names=feat_names,
        task_type="classification",
        cv_config=CrossValidationConfig(n_splits=3),
    )

    assert res["train_metrics"].accuracy is not None
    assert res["train_metrics"].accuracy >= 0.70
    assert res["test_metrics"].accuracy is not None
    assert res["test_metrics"].f1_score is not None
    assert res["test_metrics"].roc_auc is not None
    assert res["confusion_matrix"] is not None
    assert len(res["confusion_matrix"].matrix) == 2
    assert len(res["roc_curve"]) > 0
    assert len(res["feature_importances"]) == 4
    # Top features should be feat_a or feat_b
    assert res["feature_importances"][0].feature in ["feat_a", "feat_b"]
    assert res["cv_summary"] is not None
    assert len(res["cv_summary"].folds) == 3


def test_gradient_boosting_classification():
    """Verify GradientBoostingClassifier training and probability output."""
    np.random.seed(42)
    X = np.random.randn(60, 3)
    y = (X[:, 0] > 0).astype(int)

    model = GradientBoostingModel(n_estimators=15, learning_rate=0.1, max_depth=3, task_type="classification")
    model.fit(X, y)

    preds = model.predict(X)
    probs = model.predict_proba(X)
    assert len(preds) == 60
    assert probs.shape == (60, 2)
    assert np.all((probs >= 0.0) & (probs <= 1.0))
    acc = np.mean(preds == y)
    assert acc >= 0.80


def test_logistic_regression():
    """Verify LogisticRegression model fitting and gradient descent convergence."""
    np.random.seed(42)
    X = np.random.randn(80, 2)
    y = (X[:, 0] + X[:, 1] > 0).astype(int)

    model = LogisticRegressionModel(lr=0.1, max_iter=200, C=1.0)
    model.fit(X, y)

    preds = model.predict(X)
    probs = model.predict_proba(X)
    acc = np.mean(preds == y)
    assert acc >= 0.75
    assert probs.shape == (80, 2)


def test_regression_evaluation_metrics():
    """Verify RandomForestRegressor and LinearRegression evaluation metrics and residuals."""
    np.random.seed(42)
    X = np.random.randn(100, 3)
    # y = 3*x0 - 2*x1 + noise
    y = 3.0 * X[:, 0] - 2.0 * X[:, 1] + np.random.randn(100) * 0.2

    X_tr, X_te = X[:80], X[80:]
    y_tr, y_te = y[:80], y[80:]
    feat_names = ["x0", "x1", "x2"]

    res = ModelTrainer.train_and_evaluate(
        algorithm="linear_regression",
        hyperparameters={"alpha": 0.0},
        X_train=X_tr,
        y_train=y_tr,
        X_test=X_te,
        y_test=y_te,
        feature_names=feat_names,
        task_type="regression",
        cv_config=CrossValidationConfig(n_splits=4),
    )

    assert res["test_metrics"].r2_score is not None
    assert res["test_metrics"].r2_score > 0.85
    assert res["test_metrics"].rmse is not None
    assert res["test_metrics"].mae is not None
    assert len(res["residuals_sample"]) > 0
    assert res["cv_summary"] is not None
    assert len(res["cv_summary"].folds) == 4


def test_kfold_cross_validation_out_of_fold():
    """Verify that K-Fold cross validation cleanly splits and scores held-out partitions."""
    np.random.seed(42)
    X = np.random.randn(50, 2)
    y = (X[:, 0] > 0).astype(int)

    cv_summary = ModelTrainer.cross_validate(
        algorithm="decision_tree_classifier",
        hyperparameters={"max_depth": 4},
        X=X,
        y=y,
        cv_config=CrossValidationConfig(n_splits=5, shuffle=True, random_state=42),
        task_type="classification",
    )

    assert len(cv_summary.folds) == 5
    for fold in cv_summary.folds:
        assert fold.train_score >= 0.0
        assert fold.val_score >= 0.0
        assert "accuracy" in fold.metrics
    assert cv_summary.mean_val_score > 0.0


@pytest.mark.asyncio
async def test_training_api_workflow(async_client: AsyncClient):
    """End-to-end API test: register -> login -> create project -> upload dataset -> train model -> list jobs."""
    # 1. Register & Login
    email = f"trainer_{uuid.uuid4().hex[:8]}@enterprise-ai.io"
    password = "SecurePassword123!"
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "ML Engineer", "password": password, "role": "DATA_SCIENTIST"},
    )
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Fetch algorithm catalog
    algo_resp = await async_client.get("/api/v1/training/algorithms", headers=headers)
    assert algo_resp.status_code == 200
    algo_json = algo_resp.json()
    assert algo_json["success"] is True
    assert len(algo_json["data"]) >= 5

    # 3. Create project
    proj_resp = await async_client.post(
        "/api/v1/projects",
        json={"name": "ML Training Test Project", "description": "Phase 8 verification"},
        headers=headers,
    )
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["data"]["id"]

    # 4. Upload dataset
    np.random.seed(42)
    df = pd.DataFrame(
        {
            "age": [25, 45, 35, 50, 23, 60, 40, 30, 22, 55],
            "income": [50000, 100000, 75000, 120000, 45000, 130000, 85000, 60000, 40000, 110000],
            "category": ["A", "B", "A", "C", "A", "C", "B", "A", "B", "C"],
            "target": [0, 1, 0, 1, 0, 1, 1, 0, 0, 1],
        }
    )
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    upload_resp = await async_client.post(
        "/api/v1/datasets/upload",
        data={"project_id": project_id},
        files={"file": ("training_sample.csv", io.BytesIO(csv_bytes), "text/csv")},
        headers=headers,
    )
    assert upload_resp.status_code == 201
    dataset_id = upload_resp.json()["data"]["id"]

    # 5. Trigger Model Training
    train_payload = {
        "project_id": project_id,
        "dataset_id": dataset_id,
        "target_column": "target",
        "task_type": "classification",
        "algorithm": "random_forest_classifier",
        "hyperparameters": {"n_estimators": 10, "max_depth": 4},
        "cv_config": {"n_splits": 2, "shuffle": True, "random_state": 42},
        "model_name": "Test RF Classifier v1",
    }
    train_resp = await async_client.post(
        "/api/v1/training/train",
        json=train_payload,
        headers=headers,
    )
    assert train_resp.status_code == 200
    train_data = train_resp.json()["data"]
    assert train_data["status"] == "SUCCESS"
    assert train_data["algorithm"] == "random_forest_classifier"
    assert train_data["test_metrics"]["accuracy"] is not None
    assert len(train_data["feature_importances"]) > 0
    assert train_data["model_id"] is not None

    # 6. List Training Jobs
    jobs_resp = await async_client.get(
        f"/api/v1/training/jobs?project_id={project_id}",
        headers=headers,
    )
    assert jobs_resp.status_code == 200
    jobs_data = jobs_resp.json()["data"]
    assert len(jobs_data) >= 1
    assert jobs_data[0]["status"] == "SUCCESS"
    assert jobs_data[0]["target_column"] == "target"
