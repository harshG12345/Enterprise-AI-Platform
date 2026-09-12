"""Unit and integration tests for Preprocessing & Feature Engineering Engine."""

import io
import uuid

import numpy as np
import pandas as pd
import pytest
from httpx import AsyncClient

from app.ml.preprocessor import PreprocessingPipelineBuilder
from app.ml.transformers import (
    CyclicalDatetimeEncoder,
    FrequencyEncoder,
    TargetMeanEncoder,
)
from app.schemas.preprocessor import (
    CategoricalEncoderStrategy,
    CategoricalFeatureConfig,
    FeatureSelectionConfig,
    NumericalFeatureConfig,
    NumericalImputerStrategy,
    NumericalScalerStrategy,
    PreprocessingConfig,
    TrainTestSplitConfig,
)


def test_zero_data_leakage_scaling(tmp_path):
    """Verify that scalers fit strictly on train split and apply train parameters to test split."""
    # Train has mean 10, std 2; Test has mean 100, std 20
    train_vals = np.array([8.0, 10.0, 12.0])  # mean=10, std=2
    test_vals = np.array([10.0, 12.0, 14.0])

    df_train = pd.DataFrame({"feat": train_vals})
    df_test = pd.DataFrame({"feat": test_vals})

    cfg = NumericalFeatureConfig(
        column_name="feat",
        imputer=NumericalImputerStrategy.MEDIAN,
        scaler=NumericalScalerStrategy.STANDARD,
    )

    fitted_block = PreprocessingPipelineBuilder._fit_numerical_feature(df_train["feat"], cfg)
    assert fitted_block["scale_params"]["mean"] == 10.0
    assert pytest.approx(fitted_block["scale_params"]["std"], abs=1e-2) == 1.63299

    # Transform test values using train parameters
    trans_test = PreprocessingPipelineBuilder._transform_numerical_feature(df_test["feat"], fitted_block)
    # (10 - 10)/std = 0, (12 - 10)/std = 1.22
    assert pytest.approx(trans_test[0], abs=1e-2) == 0.0
    assert trans_test[1] > 0.0


def test_zero_data_leakage_imputation(tmp_path):
    """Verify that missing values in test set are filled with train median."""
    train_vals = [10.0, 20.0, 30.0]  # median = 20.0
    test_vals = [np.nan, 50.0]

    df_train = pd.DataFrame({"num": train_vals})
    df_test = pd.DataFrame({"num": test_vals})

    cfg = NumericalFeatureConfig(
        column_name="num",
        imputer=NumericalImputerStrategy.MEDIAN,
        scaler=NumericalScalerStrategy.NONE,
    )

    fitted_block = PreprocessingPipelineBuilder._fit_numerical_feature(df_train["num"], cfg)
    assert fitted_block["impute_val"] == 20.0

    trans_test = PreprocessingPipelineBuilder._transform_numerical_feature(df_test["num"], fitted_block)
    assert trans_test[0] == 20.0
    assert trans_test[1] == 50.0


def test_categorical_encoders():
    """Verify One-Hot, Frequency, and Target Mean encoders with unseen test values."""
    # 1. Frequency Encoder
    train_cats = ["apple", "apple", "banana", "cherry"]  # apple: 0.5, banana: 0.25, cherry: 0.25
    test_cats = ["apple", "unknown_fruit"]

    fe = FrequencyEncoder(handle_unknown=0.0)
    fe.fit(pd.DataFrame({"fruit": train_cats}))
    trans = fe.transform(pd.DataFrame({"fruit": test_cats}))

    assert trans[0, 0] == 0.5
    assert trans[1, 0] == 0.0

    # 2. Target Mean Encoder
    y_train = np.array([1.0, 1.0, 0.0, 0.0])  # global mean = 0.5
    te = TargetMeanEncoder(smoothing=1.0)
    te.fit(pd.DataFrame({"fruit": train_cats}), y_train)
    trans_te = te.transform(pd.DataFrame({"fruit": test_cats}))

    assert trans_te[0, 0] > 0.5  # apple has high target mean
    assert trans_te[1, 0] == 0.5  # unknown fruit gets global mean


def test_cyclical_datetime_encoder():
    """Verify trigonometric sine and cosine extraction for cyclical temporal features."""
    dates = pd.to_datetime(["2026-01-01", "2026-07-01", "2026-12-31"])
    encoder = CyclicalDatetimeEncoder(
        extracted_parts=["year", "month", "dayofweek", "is_weekend"],
        cyclical_encoding=True,
    )
    encoder.fit(dates)
    trans = encoder.transform(dates)

    assert trans.shape[0] == 3
    # Output includes year, month, month_sin, month_cos, dayofweek, dayofweek_sin, dayofweek_cos, is_weekend
    assert trans.shape[1] == 8

    # Verify all cyclical values bounded in [-1.0, 1.0]
    sin_cos_vals = trans[:, [2, 3, 5, 6]]
    assert np.all(sin_cos_vals >= -1.0)
    assert np.all(sin_cos_vals <= 1.0)


def test_end_to_end_pipeline_execution(tmp_path):
    """Verify execution of full PreprocessingPipelineBuilder with feature selection."""
    data = {
        "age": [20, 25, 30, 35, 40, 45, 50, 55, 60, 65],
        "income": [30000, 35000, 40000, 50000, 60000, 70000, 80000, 90000, 100000, 120000],
        "constant_col": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],  # zero variance
        "city": ["NY", "LA", "NY", "SF", "LA", "NY", "SF", "NY", "LA", "SF"],
        "target": [0, 0, 0, 0, 1, 1, 1, 1, 1, 1],
    }
    df = pd.DataFrame(data)

    config = PreprocessingConfig(
        target_column="target",
        problem_type="classification",
        numerical_features=[
            NumericalFeatureConfig(column_name="age", scaler=NumericalScalerStrategy.STANDARD),
            NumericalFeatureConfig(column_name="income", scaler=NumericalScalerStrategy.MINMAX),
            NumericalFeatureConfig(column_name="constant_col", scaler=NumericalScalerStrategy.STANDARD),
        ],
        categorical_features=[
            CategoricalFeatureConfig(column_name="city", encoder=CategoricalEncoderStrategy.ONEHOT),
        ],
        feature_selection=FeatureSelectionConfig(variance_threshold=0.0),  # Drop constant_col
        split_config=TrainTestSplitConfig(test_size=0.2, stratify=True, random_state=42),
    )

    response, bundle = PreprocessingPipelineBuilder.execute_pipeline(
        df=df,
        config=config,
        dataset_id="test-ds-id",
        dataset_name="test_pipeline.csv",
        output_dir=str(tmp_path),
    )

    assert response.train_shape[0] == 8
    assert response.test_shape[0] == 2
    assert "constant_col" in response.dropped_features
    assert "age" in response.transformed_feature_names
    assert "income" in response.transformed_feature_names
    assert any("city_" in f for f in response.transformed_feature_names)
    assert len(response.train_preview) == 8


async def create_user_and_project(async_client: AsyncClient) -> tuple[str, str, str]:
    """Helper to create user and project, returning (token, user_id, project_id)."""
    email = f"preprocess_user_{uuid.uuid4().hex[:8]}@enterprise-ai.io"
    password = "SecurePassword123!"
    reg_res = await async_client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Pipeline Engineer", "password": password, "role": "DATA_SCIENTIST"},
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
        json={"name": "Preprocessing Project", "description": "Workspace for pipeline tests"},
    )
    project_id = proj_res.json()["data"]["id"]
    return token, user_id, project_id


@pytest.mark.asyncio
async def test_preprocessor_api_endpoints(async_client: AsyncClient):
    """Verify validation, execution, and listing endpoints for preprocessing."""
    token, _, project_id = await create_user_and_project(async_client)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Upload CSV
    csv_content = b"age,income,department,churn\n22,40000,Sales,0\n35,60000,Engineering,0\n45,85000,Engineering,1\n29,50000,Marketing,0\n52,110000,Sales,1\n31,55000,Sales,0\n"
    files = {"file": ("employee_churn.csv", io.BytesIO(csv_content), "text/csv")}
    data = {"project_id": project_id}
    upload_res = await async_client.post(
        "/api/v1/datasets/upload",
        headers=headers,
        data=data,
        files=files,
    )
    assert upload_res.status_code == 201
    dataset_id = upload_res.json()["data"]["id"]

    # 2. Validate Preprocessing Config
    pipe_config = {
        "target_column": "churn",
        "problem_type": "classification",
        "numerical_features": [
            {
                "column_name": "age",
                "imputer": "median",
                "scaler": "standard",
                "power_transform": "none",
                "clip_outliers": False,
                "lower_percentile": 0.01,
                "upper_percentile": 0.99,
            },
            {
                "column_name": "income",
                "imputer": "mean",
                "scaler": "minmax",
                "power_transform": "none",
                "clip_outliers": False,
                "lower_percentile": 0.01,
                "upper_percentile": 0.99,
            },
        ],
        "categorical_features": [
            {
                "column_name": "department",
                "imputer": "most_frequent",
                "imputer_fill_value": "missing",
                "encoder": "onehot",
                "max_categories": 10,
                "handle_unknown": "ignore",
            },
        ],
        "datetime_features": [],
        "feature_selection": {"variance_threshold": None, "correlation_threshold": None, "drop_features": []},
        "split_config": {"test_size": 0.33, "val_size": 0.0, "stratify": False, "random_state": 42, "shuffle": True},
    }

    val_res = await async_client.post(
        f"/api/v1/datasets/{dataset_id}/preprocess/validate",
        headers=headers,
        json=pipe_config,
    )
    assert val_res.status_code == 200
    assert val_res.json()["data"]["valid"] is True

    # 3. Execute Preprocessing Pipeline
    exec_res = await async_client.post(
        f"/api/v1/datasets/{dataset_id}/preprocess",
        headers=headers,
        json=pipe_config,
    )
    assert exec_res.status_code == 200
    exec_data = exec_res.json()["data"]
    assert exec_data["dataset_id"] == dataset_id
    assert exec_data["target_column"] == "churn"
    assert exec_data["transformed_feature_count"] >= 3
    assert len(exec_data["train_preview"]) > 0

    # 4. List saved pipelines for dataset
    list_res = await async_client.get(
        f"/api/v1/datasets/{dataset_id}/pipelines",
        headers=headers,
    )
    assert list_res.status_code == 200
    pipelines = list_res.json()["data"]
    assert len(pipelines) >= 1
    assert any(p["pipeline_id"] == exec_data["pipeline_id"] for p in pipelines)
