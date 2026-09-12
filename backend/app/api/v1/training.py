"""REST API router for ML Model Training and Cross-Validation."""

import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user
from app.core.responses import APIResponse
from app.database.database import get_db
from app.models.user import User
from app.schemas.training import (
    AlgorithmInfo,
    TrainingJobCreate,
    TrainingJobDetailResponse,
)
from app.services.training_service import TrainingService

router = APIRouter(prefix="/training", tags=["Machine Learning Training"])


@router.get(
    "/algorithms",
    response_model=APIResponse[List[AlgorithmInfo]],
    status_code=status.HTTP_200_OK,
    summary="List available ML algorithms and their hyperparameter schemas",
)
async def list_training_algorithms(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve catalog of supported classification and regression algorithms."""
    service = TrainingService(db)
    algorithms = service.list_algorithms()
    return APIResponse(
        success=True,
        data=algorithms,
        message=f"Retrieved {len(algorithms)} ML algorithms",
    )


@router.post(
    "/train",
    response_model=APIResponse[TrainingJobDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="Train ML model with K-Fold Cross Validation and generate full diagnostic evaluation",
)
async def train_model(
    payload: TrainingJobCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Execute model training with zero data leakage and return comprehensive metrics."""
    service = TrainingService(db)
    response = await service.train_model(payload=payload, user=current_user)
    return APIResponse(
        success=True,
        data=response,
        message="Model trained and evaluated successfully",
    )


@router.post(
    "",
    response_model=APIResponse[Dict[str, Any]],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue asynchronous ML model training task into Celery worker",
)
@router.post(
    "/train-async",
    response_model=APIResponse[Dict[str, Any]],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue asynchronous ML model training task into Celery worker",
)
async def train_model_async(
    payload: TrainingJobCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Dispatch background training job to Celery worker pool and return job_id for polling."""
    service = TrainingService(db)
    response = await service.start_async_training(payload=payload, user=current_user)
    return APIResponse(
        success=True,
        data=response,
        message="Model training job queued successfully",
    )


@router.get(
    "/jobs",
    response_model=APIResponse[List[Dict[str, Any]]],
    status_code=status.HTTP_200_OK,
    summary="List training jobs with status and timestamps",
)
async def list_training_jobs(
    project_id: uuid.UUID | None = Query(None, description="Optional project filter"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve historical training jobs."""
    service = TrainingService(db)
    jobs = await service.list_training_jobs(project_id=project_id, user=current_user)
    return APIResponse(
        success=True,
        data=jobs,
        message=f"Retrieved {len(jobs)} training job(s)",
    )
