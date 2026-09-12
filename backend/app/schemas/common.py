"""Shared common Pydantic schemas for pagination and health."""

from typing import Generic, List, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1, description="Page number starting at 1")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "0.1.0"
    app_name: str
    environment: str
    timestamp: str


class ReadinessResponse(BaseModel):
    status: str = "ready"
    database: str = "unknown"
    redis: str = "unknown"
    mlflow: str = "unknown"
    timestamp: str
