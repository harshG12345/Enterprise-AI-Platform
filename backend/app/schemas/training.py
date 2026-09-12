"""Pydantic schemas for Machine Learning training, cross-validation, and metric evaluation."""

import uuid
from enum import Enum
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class ModelAlgorithm(str, Enum):
    LOGISTIC_REGRESSION = "logistic_regression"
    DECISION_TREE_CLASSIFIER = "decision_tree_classifier"
    RANDOM_FOREST_CLASSIFIER = "random_forest_classifier"
    GRADIENT_BOOSTING_CLASSIFIER = "gradient_boosting_classifier"
    KNN_CLASSIFIER = "knn_classifier"
    LINEAR_REGRESSION = "linear_regression"
    RIDGE_REGRESSION = "ridge_regression"
    LASSO_REGRESSION = "lasso_regression"
    DECISION_TREE_REGRESSOR = "decision_tree_regressor"
    RANDOM_FOREST_REGRESSOR = "random_forest_regressor"
    GRADIENT_BOOSTING_REGRESSOR = "gradient_boosting_regressor"
    KNN_REGRESSOR = "knn_regressor"


class CrossValidationConfig(BaseModel):
    n_splits: int = Field(default=5, ge=2, le=10)
    stratify: bool = True
    shuffle: bool = True
    random_state: int = 42


class TrainingJobCreate(BaseModel):
    project_id: uuid.UUID
    dataset_id: uuid.UUID
    pipeline_id: str | None = None
    target_column: str
    task_type: str  # 'classification' | 'regression'
    algorithm: ModelAlgorithm = ModelAlgorithm.RANDOM_FOREST_CLASSIFIER
    hyperparameters: Dict[str, Any] = Field(default_factory=dict)
    cv_config: CrossValidationConfig | None = Field(default_factory=CrossValidationConfig)
    model_name: str | None = None


class EvaluationMetrics(BaseModel):
    # Classification
    accuracy: float | None = None
    precision: float | None = None
    recall: float | None = None
    f1_score: float | None = None
    roc_auc: float | None = None
    log_loss: float | None = None
    # Regression
    mse: float | None = None
    rmse: float | None = None
    mae: float | None = None
    r2_score: float | None = None
    explained_variance: float | None = None


class ConfusionMatrixData(BaseModel):
    labels: List[str]
    matrix: List[List[int]]
    normalized_matrix: List[List[float]]


class CurvePoint(BaseModel):
    x: float
    y: float
    threshold: float | None = None


class CVFoldResult(BaseModel):
    fold: int
    train_score: float
    val_score: float
    metrics: Dict[str, float]


class CVSummary(BaseModel):
    mean_val_score: float
    std_val_score: float
    folds: List[CVFoldResult]


class FeatureImportanceItem(BaseModel):
    feature: str
    importance: float
    rank: int


class ResidualPoint(BaseModel):
    actual: float
    predicted: float
    residual: float


class TrainingJobDetailResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    dataset_id: uuid.UUID
    model_id: uuid.UUID | None = None
    status: str
    algorithm: str
    task_type: str
    target_column: str
    hyperparameters: Dict[str, Any]
    train_metrics: EvaluationMetrics
    test_metrics: EvaluationMetrics
    cv_summary: CVSummary | None = None
    feature_importances: List[FeatureImportanceItem] = Field(default_factory=list)
    confusion_matrix: ConfusionMatrixData | None = None
    roc_curve: List[CurvePoint] = Field(default_factory=list)
    residuals_sample: List[ResidualPoint] = Field(default_factory=list)
    training_duration_ms: float
    artifact_path: str | None = None
    created_at: str


class AlgorithmInfo(BaseModel):
    algorithm: str
    name: str
    task_type: str
    description: str
    default_hyperparameters: Dict[str, Any]
    hyperparameter_schema: Dict[str, Any]
