"""REST API router for tabular data preprocessing and feature engineering."""

import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user
from app.core.responses import APIResponse
from app.database.database import get_db
from app.models.user import User
from app.schemas.preprocessor import (
    PipelineSummaryItem,
    PreprocessingConfig,
    PreprocessingResponse,
)
from app.services.preprocessor_service import PreprocessorService

router = APIRouter(prefix="/datasets", tags=["Preprocessing & Feature Engineering"])


@router.post(
    "/{dataset_id}/preprocess/validate",
    response_model=APIResponse[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Validate preprocessing configuration against dataset schema",
)
async def validate_preprocessing_config(
    dataset_id: uuid.UUID,
    config: PreprocessingConfig,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Verify that columns in config match dataset schema."""
    service = PreprocessorService(db)
    validation_res = await service.validate_config(dataset_id=dataset_id, config=config, user=current_user)
    return APIResponse(
        success=True,
        data=validation_res,
        message="Preprocessing configuration validated successfully",
    )


@router.post(
    "/{dataset_id}/preprocess",
    response_model=APIResponse[PreprocessingResponse],
    status_code=status.HTTP_200_OK,
    summary="Execute preprocessing pipeline with Zero Data Leakage",
)
async def execute_preprocessing_pipeline(
    dataset_id: uuid.UUID,
    config: PreprocessingConfig,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Fit transformations strictly on train split and return transformed preview."""
    service = PreprocessorService(db)
    response = await service.execute_preprocessing(dataset_id=dataset_id, config=config, user=current_user)
    return APIResponse(
        success=True,
        data=response,
        message="Preprocessing pipeline executed and persisted successfully",
    )


@router.get(
    "/{dataset_id}/pipelines",
    response_model=APIResponse[List[PipelineSummaryItem]],
    status_code=status.HTTP_200_OK,
    summary="List saved preprocessing pipelines for a dataset",
)
async def list_dataset_pipelines(
    dataset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve all saved pipeline artifacts for a dataset."""
    service = PreprocessorService(db)
    items = await service.list_pipelines(dataset_id=dataset_id, user=current_user)
    return APIResponse(
        success=True,
        data=items,
        message=f"Retrieved {len(items)} pipeline(s)",
    )
