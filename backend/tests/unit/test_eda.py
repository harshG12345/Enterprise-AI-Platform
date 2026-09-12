"""Unit tests for Exploratory Data Analysis (EDA) engine and REST API."""

import io
import uuid

import numpy as np
import pandas as pd
import pytest
from httpx import AsyncClient

from app.ml.eda import EDAEngine
from app.schemas.eda import EDAResponse


@pytest.mark.asyncio
async def test_eda_engine_numerical_moments():
    """Verify accuracy of descriptive statistics, quantiles, and moments."""
    # Data with known properties
    data = {
        "feature_a": [10.0, 20.0, 30.0, 40.0, 50.0],
        "feature_b": [1.0, 2.0, 3.0, 4.0, 5.0],
        "category_x": ["A", "B", "A", "A", "C"],
    }
    df = pd.DataFrame(data)

    report: EDAResponse = EDAEngine.analyze_dataset(
        df=df,
        dataset_id="test-id",
        dataset_name="test_data.csv",
    )

    assert report.overview.total_rows == 5
    assert report.overview.total_columns == 3
    assert report.overview.numerical_columns_count == 2
    assert report.overview.categorical_columns_count == 1

    feat_a = next(f for f in report.numerical_features if f.column_name == "feature_a")
    assert feat_a.mean == 30.0
    assert feat_a.median == 30.0
    assert feat_a.min == 10.0
    assert feat_a.max == 50.0
    assert feat_a.q25 == 20.0
    assert feat_a.q75 == 40.0
    assert feat_a.iqr == 20.0
    assert feat_a.outliers_iqr_count == 0


@pytest.mark.asyncio
async def test_eda_engine_outliers_and_skew():
    """Verify IQR and Z-score outlier detection and skewness calculations."""
    # Create distribution with an extreme outlier
    values = [10.0, 11.0, 10.5, 9.8, 10.2, 10.1, 10.3, 9.9, 10.0, 1000.0]
    df = pd.DataFrame({"metric": values})

    report = EDAEngine.analyze_dataset(
        df=df,
        dataset_id="test-outlier-id",
        dataset_name="outliers.csv",
    )

    metric_stat = report.numerical_features[0]
    assert metric_stat.outliers_iqr_count >= 1
    assert 1000.0 in metric_stat.boxplot.outliers_sample
    assert metric_stat.skewness > 1.5  # Heavily right skewed

    # Verify high skew warning generated
    skew_warning = next((w for w in report.health_warnings if w.code == "HIGH_SKEW"), None)
    assert skew_warning is not None
    assert skew_warning.column == "metric"


@pytest.mark.asyncio
async def test_eda_engine_categorical_cardinality():
    """Verify frequency breakdown, uniqueness ratio, and high cardinality flagging."""
    # 60 distinct categories in 100 rows
    categories = [f"CAT_{i}" for i in range(60)] + ["CAT_0"] * 40
    df = pd.DataFrame({"high_card_col": categories, "single_val": ["CONSTANT"] * 100})

    report = EDAEngine.analyze_dataset(
        df=df,
        dataset_id="test-cat-id",
        dataset_name="categories.csv",
    )

    cat_stat = next(c for c in report.categorical_features if c.column_name == "high_card_col")
    assert cat_stat.unique_count == 60
    assert cat_stat.top_value == "CAT_0"
    assert cat_stat.top_frequency == 41
    assert cat_stat.is_high_cardinality is True

    # Check for HIGH_CARDINALITY and CONSTANT_COLUMN health warnings
    warn_codes = [w.code for w in report.health_warnings]
    assert "HIGH_CARDINALITY" in warn_codes
    assert "CONSTANT_COLUMN" in warn_codes


@pytest.mark.asyncio
async def test_eda_engine_missingness_summary():
    """Verify missing count and percentage calculations."""
    df = pd.DataFrame(
        {
            "clean_col": [1, 2, 3, 4, 5],
            "half_missing": [1, np.nan, 3, np.nan, 5],
            "mostly_missing": [np.nan, np.nan, np.nan, np.nan, 5],
        }
    )

    report = EDAEngine.analyze_dataset(
        df=df,
        dataset_id="test-missing-id",
        dataset_name="missing.csv",
    )

    clean_summary = next(m for m in report.missing_summary if m.column_name == "clean_col")
    assert clean_summary.missing_count == 0
    assert clean_summary.missing_percentage == 0.0

    half_summary = next(m for m in report.missing_summary if m.column_name == "half_missing")
    assert half_summary.missing_count == 2
    assert half_summary.missing_percentage == 40.0

    mostly_summary = next(m for m in report.missing_summary if m.column_name == "mostly_missing")
    assert mostly_summary.missing_count == 4
    assert mostly_summary.missing_percentage == 80.0

    # Verify critical missing warning
    critical_warn = next(
        (w for w in report.health_warnings if w.code == "HIGH_MISSING" and w.level == "critical"), None
    )
    assert critical_warn is not None
    assert critical_warn.column == "mostly_missing"


@pytest.mark.asyncio
async def test_eda_engine_correlation_matrices():
    """Verify Pearson and Spearman correlation matrices and collinearity detection."""
    x = np.linspace(1, 50, 50)
    y = 2.0 * x + 5.0  # Perfect positive linear correlation
    z = np.sin(x)

    df = pd.DataFrame({"x": x, "y": y, "z": z})

    report = EDAEngine.analyze_dataset(
        df=df,
        dataset_id="test-corr-id",
        dataset_name="corr.csv",
    )

    assert report.pearson_correlation is not None
    assert report.spearman_correlation is not None

    # Check pairwise pair between x and y
    xy_pair = next(
        p
        for p in report.pearson_correlation.pairwise_pairs
        if (p.feature_x == "x" and p.feature_y == "y") or (p.feature_x == "y" and p.feature_y == "x")
    )
    assert pytest.approx(xy_pair.correlation, abs=1e-3) == 1.0

    # Verify collinearity warning for x and y
    collinear_warn = next((w for w in report.health_warnings if w.code == "HIGH_COLLINEARITY"), None)
    assert collinear_warn is not None
    assert "x" in collinear_warn.columns
    assert "y" in collinear_warn.columns


async def create_user_and_project(async_client: AsyncClient) -> tuple[str, str, str]:
    """Helper to create user and project, returning (token, user_id, project_id)."""
    email = f"eda_user_{uuid.uuid4().hex[:8]}@enterprise-ai.io"
    password = "SecurePassword123!"
    reg_res = await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "EDA Test Engineer", "password": password, "role": "DATA_SCIENTIST"},
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
        json={"name": "EDA Test Project", "description": "Workspace for EDA testing"},
    )
    project_id = proj_res.json()["data"]["id"]
    return token, user_id, project_id


@pytest.mark.asyncio
async def test_eda_api_endpoint(async_client: AsyncClient):
    """Test the GET /api/v1/datasets/{dataset_id}/eda REST endpoint."""
    token, _, project_id = await create_user_and_project(async_client)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Upload a sample CSV
    csv_content = b"age,income,score,gender\n25,50000,85.5,Male\n30,60000,90.0,Female\n35,75000,92.5,Female\n40,80000,88.0,Male\n45,95000,96.0,Female\n"
    files = {"file": ("eda_sample.csv", io.BytesIO(csv_content), "text/csv")}
    data = {"project_id": project_id}
    upload_res = await async_client.post(
        "/api/v1/datasets/upload",
        headers=headers,
        data=data,
        files=files,
    )
    assert upload_res.status_code == 201
    dataset_id = upload_res.json()["data"]["id"]

    # 2. Call GET /api/v1/datasets/{id}/eda
    eda_res = await async_client.get(
        f"/api/v1/datasets/{dataset_id}/eda",
        headers=headers,
    )
    assert eda_res.status_code == 200
    body = eda_res.json()
    assert body["success"] is True
    data = body["data"]

    assert data["dataset_name"] == "eda_sample.csv"
    assert data["overview"]["total_rows"] == 5
    assert data["overview"]["total_columns"] == 4
    assert len(data["numerical_features"]) == 3  # age, income, score
    assert len(data["categorical_features"]) == 1  # gender
    assert data["pearson_correlation"] is not None
