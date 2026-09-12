"""Pydantic schemas for Celery Background Jobs and Status Polling."""

import uuid
from typing import Any, Dict

from pydantic import BaseModel


class JobStatusResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    project_name: str | None = None
    dataset_id: uuid.UUID
    dataset_name: str | None = None
    user_id: uuid.UUID
    status: str
    target_column: str
    task_type: str
    celery_task_id: str | None = None
    error_message: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    created_at: str
    model_id: uuid.UUID | None = None
    metrics: Dict[str, Any] | None = None
    artifact_path: str | None = None


class AsyncTrainingLaunchResponse(BaseModel):
    job_id: uuid.UUID
    status: str
    message: str
