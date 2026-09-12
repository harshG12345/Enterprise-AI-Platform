"""Pydantic schemas for Project management requests and responses."""

import uuid
from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, json_schema_extra={"example": "Credit Risk Prediction"})
    description: str | None = Field(
        None,
        max_length=1000,
        json_schema_extra={"example": "Enterprise classification model for loan default prediction."},
    )


class ProjectUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=100)
    description: str | None = Field(None, max_length=1000)


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: uuid.UUID
    name: str
    description: str | None = None
    owner_id: uuid.UUID
    owner_email: str | None = None
    owner_name: str | None = None
    dataset_count: int = 0
    model_count: int = 0
    experiment_count: int = 0
    created_at: datetime
    updated_at: datetime


class ProjectDetailResponse(ProjectResponse):
    datasets: List[Dict[str, Any]] = []
    models: List[Dict[str, Any]] = []
    experiments: List[Dict[str, Any]] = []


class ProjectListResponse(BaseModel):
    items: List[ProjectResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
