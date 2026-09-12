"""Dataset REST API router for multipart uploads, previews, and metadata."""

import uuid

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user
from app.core.responses import APIResponse
from app.database.database import get_db
from app.models.user import User
from app.schemas.dataset import (
    DatasetDetailResponse,
    DatasetListResponse,
    DatasetPreviewResponse,
    DatasetResponse,
)
from app.services.dataset_service import DatasetService

router = APIRouter(prefix="/datasets", tags=["Datasets"])


@router.post(
    "/upload",
    response_model=APIResponse[DatasetResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload Tabular Dataset",
)
async def upload_dataset(
    project_id: uuid.UUID = Form(..., description="Target Project Workspace UUID"),
    file: UploadFile = File(..., description="Tabular data file (CSV or XLSX format)"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[DatasetResponse]:
    """Upload, validate, inspect, and register tabular dataset."""
    service = DatasetService(db)
    dataset = await service.upload_dataset(project_id=project_id, file=file, user=current_user)

    return APIResponse(
        success=True,
        data=DatasetResponse.model_validate(dataset),
        message="Dataset uploaded and validated successfully",
    )


@router.get(
    "",
    response_model=APIResponse[DatasetListResponse],
    status_code=status.HTTP_200_OK,
    summary="List Datasets",
)
async def list_datasets(
    project_id: uuid.UUID | None = Query(None, description="Filter by project ID"),
    page: int = Query(1, ge=1, description="Page index"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    search: str | None = Query(None, description="Filename search filter"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[DatasetListResponse]:
    """List accessible datasets with pagination and filters."""
    service = DatasetService(db)
    items, total, total_pages = await service.list_datasets(
        user=current_user,
        project_id=project_id,
        page=page,
        page_size=page_size,
        search=search,
    )

    return APIResponse(
        success=True,
        data=DatasetListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        ),
        message="Datasets retrieved successfully",
    )


@router.get(
    "/{dataset_id}",
    response_model=APIResponse[DatasetDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Dataset Details",
)
async def get_dataset(
    dataset_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[DatasetDetailResponse]:
    """Retrieve full schema metadata, column statistics, and dimensions for a dataset."""
    service = DatasetService(db)
    detail = await service.get_dataset_by_id(dataset_id=dataset_id, user=current_user)

    return APIResponse(
        success=True,
        data=detail,
        message="Dataset details retrieved successfully",
    )


@router.get(
    "/{dataset_id}/preview",
    response_model=APIResponse[DatasetPreviewResponse],
    status_code=status.HTTP_200_OK,
    summary="Preview Dataset Rows",
)
async def get_dataset_preview(
    dataset_id: uuid.UUID,
    page: int = Query(1, ge=1, description="Preview page number"),
    page_size: int = Query(50, ge=1, le=200, description="Preview rows per page"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[DatasetPreviewResponse]:
    """Return paginated preview rows safely formatted for browser inspection."""
    service = DatasetService(db)
    preview = await service.get_preview(
        dataset_id=dataset_id,
        user=current_user,
        page=page,
        page_size=page_size,
    )

    return APIResponse(
        success=True,
        data=preview,
        message="Dataset preview generated successfully",
    )


@router.delete(
    "/{dataset_id}",
    response_model=APIResponse[None],
    status_code=status.HTTP_200_OK,
    summary="Delete Dataset",
)
async def delete_dataset(
    dataset_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[None]:
    """Delete dataset physical file and metadata record."""
    service = DatasetService(db)
    await service.delete_dataset(dataset_id=dataset_id, user=current_user)

    return APIResponse(
        success=True,
        data=None,
        message="Dataset deleted successfully",
    )
