"""Pydantic schemas for Model Observability and Statistical Drift Engine."""

import uuid
from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field


class HistogramBin(BaseModel):
    """Distribution comparison bin."""

    bin_label: str
    baseline_pct: float
    current_pct: float


class FeatureDriftReport(BaseModel):
    """Detailed statistical drift report for a single feature."""

    feature_name: str
    feature_type: str
    drift_detected: bool
    psi_score: float
    primary_test: str
    test_statistic: float
    p_value: float
    wasserstein_distance: float | None = None
    histogram_bins: List[HistogramBin] = Field(default_factory=list)
    baseline_stats: Dict[str, Any] = Field(default_factory=dict)
    current_stats: Dict[str, Any] = Field(default_factory=dict)


class ModelDriftAnalysisResponse(BaseModel):
    """Comprehensive drift analysis response."""

    model_config = ConfigDict(protected_namespaces=())

    model_id: uuid.UUID
    model_name: str
    model_version: str
    task_type: str
    health_status: str  # "HEALTHY" | "WARNING" | "DRIFT_DETECTED"
    drift_score: float
    drift_percentage: float
    total_features: int
    drifted_features_count: int
    max_psi: float
    baseline_sample_count: int
    current_sample_count: int
    feature_reports: List[FeatureDriftReport]
    analyzed_at: datetime


class ModelMonitoringOverview(BaseModel):
    """Model observability overview item."""

    model_config = ConfigDict(protected_namespaces=())

    model_id: uuid.UUID
    model_name: str
    model_version: str
    status: str
    health_status: str
    total_inferences: int
    max_psi: float
    drifted_features_count: int
    last_inference_at: datetime | None = None


class CustomDriftAnalysisRequest(BaseModel):
    """Payload to trigger drift analysis against custom evaluation dataset."""

    current_dataset_id: uuid.UUID | None = Field(
        None, description="Optional evaluation dataset to compare against baseline"
    )
    alpha: float = Field(0.05, ge=0.001, le=0.5, description="Significance level for KS/Chi2 tests")
    psi_threshold: float = Field(0.2, ge=0.01, le=1.0, description="PSI threshold for drift alert")
