"""REST API router for Model Registry, Lifecycle Governance, Leaderboard, and Artifact Downloads."""

import uuid
from typing import List

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user
from app.core.responses import APIResponse
from app.database.database import get_db
from app.models.user import User
from app.schemas.model import (
    ModelComparisonRequest,
    ModelComparisonResponse,
    ModelDetailResponse,
    ModelLeaderboardItem,
    ModelPromotionRequest,
    ModelResponse,
)
from app.services.model_service import ModelService

router = APIRouter(prefix="/models", tags=["Model Registry & Lifecycle Governance"])


@router.get(
    "",
    response_model=APIResponse[List[ModelResponse]],
    status_code=status.HTTP_200_OK,
    summary="List registered machine learning models",
)
async def list_models(
    project_id: uuid.UUID | None = Query(None, description="Filter models by project"),
    task_type: str | None = Query(None, description="Filter by classification or regression"),
    status: str | None = Query(None, description="Filter by stage (DEVELOPMENT, STAGING, PRODUCTION, ARCHIVED)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve catalog of registered model versions with stage metadata."""
    service = ModelService(db)
    models = await service.list_models(
        project_id=project_id, task_type=task_type, status_filter=status, user=current_user
    )
    return APIResponse(
        success=True,
        data=models,
        message=f"Retrieved {len(models)} registered model(s)",
    )


@router.get(
    "/leaderboard",
    response_model=APIResponse[List[ModelLeaderboardItem]],
    status_code=status.HTTP_200_OK,
    summary="Get model performance leaderboard",
)
async def get_model_leaderboard(
    project_id: uuid.UUID | None = Query(None, description="Filter leaderboard by project"),
    task_type: str | None = Query(None, description="Filter by classification or regression"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Rank models by generalization test performance score."""
    service = ModelService(db)
    leaderboard = await service.get_leaderboard(project_id=project_id, task_type=task_type, user=current_user)
    return APIResponse(
        success=True,
        data=leaderboard,
        message=f"Leaderboard contains {len(leaderboard)} model(s)",
    )


@router.post(
    "/compare",
    response_model=APIResponse[ModelComparisonResponse],
    status_code=status.HTTP_200_OK,
    summary="Compare multiple registered models side-by-side",
)
async def compare_models(
    payload: ModelComparisonRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Generate side-by-side metric benchmarking and hyperparameter comparison matrix."""
    service = ModelService(db)
    comparison = await service.compare_models(model_ids=payload.model_ids, user=current_user)
    return APIResponse(
        success=True,
        data=comparison,
        message=f"Compared {len(comparison.models)} model(s) successfully",
    )


@router.get(
    "/{model_id}",
    response_model=APIResponse[ModelDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="Get comprehensive model details and diagnostic evaluation",
)
async def get_model_details(
    model_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve model metadata, feature importances, confusion matrix, MLflow link, and audit history."""
    service = ModelService(db)
    detail = await service.get_model_details(model_id=model_id, user=current_user)
    return APIResponse(
        success=True,
        data=detail,
        message="Model details retrieved successfully",
    )


@router.post(
    "/{model_id}/promote",
    response_model=APIResponse[ModelResponse],
    status_code=status.HTTP_200_OK,
    summary="Promote model lifecycle stage (DEVELOPMENT -> STAGING -> PRODUCTION)",
)
async def promote_model(
    model_id: uuid.UUID,
    payload: ModelPromotionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Transition model stage with role-based access control and audit trail logging."""
    service = ModelService(db)
    updated_model = await service.promote_model(model_id=model_id, payload=payload, user=current_user)
    return APIResponse(
        success=True,
        data=updated_model,
        message=f"Model successfully promoted to {payload.status.value}",
    )


@router.post(
    "/{model_id}/rollback",
    response_model=APIResponse[ModelResponse],
    status_code=status.HTTP_200_OK,
    summary="Rollback model to DEVELOPMENT stage",
)
async def rollback_model(
    model_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Rollback model stage for testing or retraining."""
    service = ModelService(db)
    updated_model = await service.rollback_model(model_id=model_id, user=current_user)
    return APIResponse(
        success=True,
        data=updated_model,
        message="Model stage rolled back to DEVELOPMENT",
    )


@router.post(
    "/{model_id}/archive",
    response_model=APIResponse[ModelResponse],
    status_code=status.HTTP_200_OK,
    summary="Archive a model version",
)
async def archive_model(
    model_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Deprecate and archive a model version."""
    service = ModelService(db)
    updated_model = await service.archive_model(model_id=model_id, user=current_user)
    return APIResponse(
        success=True,
        data=updated_model,
        message="Model successfully archived",
    )


@router.get(
    "/{model_id}/download",
    summary="Download serialized model artifact binary (.pkl)",
)
async def download_model_artifact(
    model_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Stream model artifact file to authorized client."""
    service = ModelService(db)
    file_path = await service.get_model_artifact_path(model_id=model_id, user=current_user)
    return FileResponse(
        path=file_path,
        filename=f"model_{model_id}.pkl",
        media_type="application/octet-stream",
    )
