"""Pydantic schemas for Model Registry, Lifecycle Governance, Leaderboard, and Comparisons."""

import uuid
from typing import Any, Dict, List

from pydantic import BaseModel, Field

from app.models.trained_model import ModelStatus


class ModelPromotionRequest(BaseModel):
    status: ModelStatus = Field(..., description="Target lifecycle stage: DEVELOPMENT, STAGING, PRODUCTION, ARCHIVED")
    notes: str | None = Field(None, max_length=1000, description="Audit rationale for stage transition")


class ModelResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    project_name: str | None = None
    dataset_id: uuid.UUID | None = None
    dataset_name: str | None = None
    experiment_id: uuid.UUID | None = None
    name: str
    version: str
    task_type: str
    framework: str
    metrics: Dict[str, Any] | None = None
    artifact_path: str
    mlflow_run_id: str | None = None
    status: str
    created_at: str


class AuditHistoryItem(BaseModel):
    id: uuid.UUID
    action: str
    user_id: uuid.UUID
    metadata: Dict[str, Any]
    created_at: str


class ModelDetailResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    project_name: str | None = None
    dataset_id: uuid.UUID | None = None
    dataset_name: str | None = None
    experiment_id: uuid.UUID | None = None
    name: str
    version: str
    task_type: str
    framework: str
    status: str
    metrics: Dict[str, Any] | None = None
    artifact_path: str
    mlflow_run_id: str | None = None
    algorithm: str | None = None
    target_column: str | None = None
    feature_names: List[str] = Field(default_factory=list)
    hyperparameters: Dict[str, Any] = Field(default_factory=dict)
    confusion_matrix: Dict[str, Any] | None = None
    feature_importances: List[Dict[str, Any]] = Field(default_factory=list)
    audit_history: List[AuditHistoryItem] = Field(default_factory=list)
    created_at: str


class ModelLeaderboardItem(BaseModel):
    rank: int
    id: uuid.UUID
    name: str
    version: str
    status: str
    task_type: str
    primary_metric_name: str
    primary_metric_value: float
    secondary_metric_name: str | None = None
    secondary_metric_value: float | None = None
    training_duration_ms: float | None = None
    created_at: str


class ModelComparisonRequest(BaseModel):
    model_ids: List[uuid.UUID] = Field(..., min_length=1, max_length=10)


class ModelComparisonResponse(BaseModel):
    models: List[ModelDetailResponse]
    all_metrics: List[str]
    metric_matrix: Dict[str, Dict[str, float | None]]  # metric -> {model_id -> value}
    differing_hyperparameters: List[str]
    common_hyperparameters: Dict[str, Any]
