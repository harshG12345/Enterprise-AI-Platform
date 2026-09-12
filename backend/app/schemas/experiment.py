"""Pydantic schemas for MLflow Experiment Tracking, Runs, Metrics, and Comparisons."""

import uuid
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class ExperimentCreate(BaseModel):
    project_id: uuid.UUID
    name: str = Field(..., min_length=1, max_length=255)
    dataset_id: uuid.UUID | None = None
    tags: Dict[str, str] = Field(default_factory=dict)


class ExperimentResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    dataset_id: uuid.UUID | None = None
    name: str
    mlflow_experiment_id: str | None = None
    run_count: int = 0
    created_at: str


class MetricValue(BaseModel):
    key: str
    value: float
    step: int = 0
    timestamp: float


class MetricHistoryItem(BaseModel):
    step: int
    value: float
    timestamp: str


class RunCreate(BaseModel):
    experiment_id: uuid.UUID
    run_name: str | None = None
    tags: Dict[str, str] = Field(default_factory=dict)
    parameters: Dict[str, Any] = Field(default_factory=dict)


class ArtifactItem(BaseModel):
    path: str
    is_dir: bool = False
    file_size_bytes: int = 0


class RunDetailResponse(BaseModel):
    run_id: str
    experiment_id: uuid.UUID
    run_name: str
    status: str  # 'RUNNING' | 'FINISHED' | 'FAILED' | 'KILLED'
    started_at: str
    end_time: str | None = None
    duration_ms: float | None = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    metrics: Dict[str, float] = Field(default_factory=dict)
    tags: Dict[str, str] = Field(default_factory=dict)
    artifacts: List[ArtifactItem] = Field(default_factory=list)


class RunComparisonRequest(BaseModel):
    run_ids: List[str] = Field(..., min_length=1, max_length=10)


class RunComparisonItem(BaseModel):
    run_id: str
    run_name: str
    status: str
    duration_ms: float | None = None
    parameters: Dict[str, Any]
    metrics: Dict[str, float]
    tags: Dict[str, str]
    created_at: str


class RunComparisonResponse(BaseModel):
    runs: List[RunComparisonItem]
    common_parameters: Dict[str, Any]
    differing_parameters: List[str]
    all_metrics: List[str]
    metric_matrix: Dict[str, Dict[str, float | None]]  # metric -> {run_id -> value}
