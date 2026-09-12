"""Pydantic schemas for Real-time and Batch Prediction Engine."""

import uuid
from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field


class RealtimePredictionRequest(BaseModel):
    """Payload for real-time single record inference."""

    model_config = ConfigDict(protected_namespaces=())

    model_id: uuid.UUID = Field(..., description="ID of the trained model to perform inference with")
    features: Dict[str, Any] = Field(..., description="Key-value mapping of input feature names to values")
    include_probabilities: bool = Field(
        True, description="Whether to include class probabilities for classification models"
    )


class PredictionProbability(BaseModel):
    """Class prediction probability score."""

    class_name: str
    probability: float


class RealtimePredictionResponse(BaseModel):
    """Structured response for real-time inference."""

    model_config = ConfigDict(protected_namespaces=())

    prediction_id: uuid.UUID
    model_id: uuid.UUID
    model_name: str
    model_version: str
    task_type: str
    predicted_value: Any
    probabilities: List[PredictionProbability] | None = None
    latency_ms: float
    timestamp: datetime


class BatchPredictionLaunchRequest(BaseModel):
    """Payload to launch asynchronous batch inference over a dataset."""

    model_config = ConfigDict(protected_namespaces=())

    model_id: uuid.UUID = Field(..., description="ID of the trained model")
    project_id: uuid.UUID = Field(..., description="Project workspace ID")
    dataset_id: uuid.UUID | None = Field(None, description="Pre-existing dataset ID to predict on")
    output_format: str = Field("csv", description="Desired output format ('csv' or 'json')")


class BatchPredictionLaunchResponse(BaseModel):
    """Immediate response after queuing batch prediction job."""

    model_config = ConfigDict(protected_namespaces=())

    job_id: uuid.UUID
    celery_task_id: str
    model_id: uuid.UUID
    status: str
    message: str


class PredictionHistoryItem(BaseModel):
    """Historical real-time inference telemetry log entry."""

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: uuid.UUID
    model_id: uuid.UUID
    model_name: str | None = None
    task_type: str | None = None
    user_id: uuid.UUID | None = None
    input_data: Dict[str, Any]
    prediction: Dict[str, Any]
    latency_ms: float
    created_at: datetime


class PredictionTelemetryStats(BaseModel):
    """Aggregated prediction latency and throughput metrics."""

    total_predictions: int
    average_latency_ms: float
    p95_latency_ms: float
    predictions_by_model: Dict[str, int]
