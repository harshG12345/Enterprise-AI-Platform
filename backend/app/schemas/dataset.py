"""Pydantic schemas for Dataset uploads, metadata summaries, and previews."""

import uuid
from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict

from app.models.dataset import DatasetStatus


class ColumnMetadata(BaseModel):
    name: str
    dtype: str
    inferred_type: str
    missing_count: int
    missing_percentage: float
    unique_count: int


class DatasetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    filename: str
    file_size: int
    row_count: int | None = None
    column_count: int | None = None
    status: DatasetStatus
    created_at: datetime
    updated_at: datetime


class DatasetDetailResponse(DatasetResponse):
    schema_metadata: Dict[str, Any] | None = None
    columns: List[ColumnMetadata] = []
    memory_bytes: int | None = None


class DatasetPreviewResponse(BaseModel):
    columns: List[str]
    rows: List[Dict[str, Any]]
    total_rows: int
    page: int
    page_size: int
    total_pages: int


class DatasetListResponse(BaseModel):
    items: List[DatasetResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
