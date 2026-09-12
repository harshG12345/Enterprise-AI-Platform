"""REST API router for MLflow Experiment Tracking, Runs, and Comparisons."""

import uuid
from typing import List

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user
from app.core.responses import APIResponse
from app.database.database import get_db
from app.models.user import User
from app.schemas.experiment import (
    ArtifactItem,
    ExperimentCreate,
    ExperimentResponse,
    MetricHistoryItem,
    RunComparisonRequest,
    RunComparisonResponse,
    RunCreate,
    RunDetailResponse,
)
from app.services.experiment_service import ExperimentService

router = APIRouter(prefix="/experiments", tags=["MLflow Experiment Tracking"])


@router.post(
    "",
    response_model=APIResponse[ExperimentResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create MLflow experiment workspace",
)
async def create_experiment(
    payload: ExperimentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Register a new experiment workspace for tracking runs."""
    service = ExperimentService(db)
    response = await service.create_experiment(payload=payload, user=current_user)
    return APIResponse(
        success=True,
        data=response,
        message="Experiment created successfully",
    )


@router.get(
    "",
    response_model=APIResponse[List[ExperimentResponse]],
    status_code=status.HTTP_200_OK,
    summary="List MLflow experiments",
)
async def list_experiments(
    project_id: uuid.UUID | None = Query(None, description="Optional project filter"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve experiments accessible by user."""
    service = ExperimentService(db)
    experiments = await service.list_experiments(project_id=project_id, user=current_user)
    return APIResponse(
        success=True,
        data=experiments,
        message=f"Retrieved {len(experiments)} experiment(s)",
    )


@router.get(
    "/{experiment_id}",
    response_model=APIResponse[ExperimentResponse],
    status_code=status.HTTP_200_OK,
    summary="Get MLflow experiment details",
)
async def get_experiment(
    experiment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve detailed information about a specific experiment."""
    service = ExperimentService(db)
    experiment = await service.get_experiment(experiment_id=experiment_id, user=current_user)
    return APIResponse(
        success=True,
        data=experiment,
        message="Experiment details retrieved successfully",
    )


@router.post(
    "/{experiment_id}/runs",
    response_model=APIResponse[RunDetailResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Initialize MLflow tracking run",
)
async def create_run(
    experiment_id: uuid.UUID,
    payload: RunCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Start and initialize a new MLflow tracking run under an experiment."""
    payload.experiment_id = experiment_id
    service = ExperimentService(db)
    run_detail = await service.create_run(payload=payload, user=current_user)
    return APIResponse(
        success=True,
        data=run_detail,
        message="MLflow run initialized successfully",
    )


@router.get(
    "/{experiment_id}/runs",
    response_model=APIResponse[List[RunDetailResponse]],
    status_code=status.HTTP_200_OK,
    summary="List runs for an experiment",
)
async def list_runs(
    experiment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve all runs associated with an experiment."""
    service = ExperimentService(db)
    runs = await service.list_runs(experiment_id=experiment_id, user=current_user)
    return APIResponse(
        success=True,
        data=runs,
        message=f"Retrieved {len(runs)} run(s)",
    )


@router.get(
    "/runs/{run_id}",
    response_model=APIResponse[RunDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="Get single MLflow run details",
)
async def get_run_details(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Fetch complete parameters, metrics, tags, and artifacts for a run."""
    service = ExperimentService(db)
    run_detail = await service.get_run(run_id=run_id, user=current_user)
    return APIResponse(
        success=True,
        data=run_detail,
        message="Run details retrieved successfully",
    )


@router.get(
    "/runs/{run_id}/metrics/{metric_key}",
    response_model=APIResponse[List[MetricHistoryItem]],
    status_code=status.HTTP_200_OK,
    summary="Get metric time series history",
)
async def get_metric_history(
    run_id: str,
    metric_key: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve step-wise learning curve data for a specific metric."""
    service = ExperimentService(db)
    history = await service.get_metric_history(run_id=run_id, metric_key=metric_key, user=current_user)
    return APIResponse(
        success=True,
        data=history,
        message=f"Retrieved {len(history)} metric point(s)",
    )


@router.get(
    "/runs/{run_id}/artifacts",
    response_model=APIResponse[List[ArtifactItem]],
    status_code=status.HTTP_200_OK,
    summary="List run artifact repository contents",
)
async def list_run_artifacts(
    run_id: str,
    path: str = Query("", description="Sub-directory path in artifacts"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Browse files and folders saved in a run's artifact repository."""
    service = ExperimentService(db)
    artifacts = await service.list_run_artifacts(run_id=run_id, path=path, user=current_user)
    return APIResponse(
        success=True,
        data=artifacts,
        message=f"Retrieved {len(artifacts)} artifact(s)",
    )


@router.post(
    "/compare",
    response_model=APIResponse[RunComparisonResponse],
    status_code=status.HTTP_200_OK,
    summary="Compare parameters, metrics, and duration across runs",
)
async def compare_runs(
    payload: RunComparisonRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Generate side-by-side run comparison matrix."""
    service = ExperimentService(db)
    comparison = await service.compare_runs(run_ids=payload.run_ids, user=current_user)
    return APIResponse(
        success=True,
        data=comparison,
        message=f"Compared {len(comparison.runs)} run(s) successfully",
    )
