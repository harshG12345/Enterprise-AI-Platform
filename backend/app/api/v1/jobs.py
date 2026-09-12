"""REST API router for Asynchronous Celery Jobs and Status Polling."""

import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user
from app.core.responses import APIResponse
from app.database.database import get_db
from app.models.user import User
from app.schemas.job import JobStatusResponse
from app.services.training_service import TrainingService

router = APIRouter(prefix="/jobs", tags=["Asynchronous Background Jobs"])


@router.get(
    "/{job_id}",
    response_model=APIResponse[JobStatusResponse],
    status_code=status.HTTP_200_OK,
    summary="Get real-time job status and diagnostic metrics",
)
async def get_job_status(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Poll execution state, worker progress, error message, or completed model artifact."""
    service = TrainingService(db)
    job_data = await service.get_job_status(job_id=job_id, user=current_user)
    return APIResponse(
        success=True,
        data=job_data,
        message=f"Job status is {job_data['status']}",
    )


@router.get(
    "",
    response_model=APIResponse[List[Dict[str, Any]]],
    status_code=status.HTTP_200_OK,
    summary="List asynchronous background jobs",
)
async def list_jobs(
    project_id: uuid.UUID | None = Query(None, description="Filter jobs by project"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve all background jobs accessible by user."""
    service = TrainingService(db)
    jobs = await service.list_training_jobs(project_id=project_id, user=current_user)
    return APIResponse(
        success=True,
        data=jobs,
        message=f"Retrieved {len(jobs)} background job(s)",
    )
