"""REST API router for Model Observability, Statistical Drift Analysis, and Health Telemetry."""

import uuid
from typing import List

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user
from app.core.responses import APIResponse
from app.database.database import get_db
from app.models.user import User
from app.schemas.monitoring import (
    CustomDriftAnalysisRequest,
    ModelDriftAnalysisResponse,
    ModelMonitoringOverview,
)
from app.services.monitoring_service import MonitoringService

router = APIRouter(prefix="/monitoring", tags=["Monitoring & Statistical Drift Engine"])


@router.get(
    "/overview",
    response_model=APIResponse[List[ModelMonitoringOverview]],
    status_code=status.HTTP_200_OK,
    summary="Get model observability health overview",
)
async def get_monitoring_overview(
    project_id: uuid.UUID | None = Query(None, description="Filter models by project"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve health indicators, inference volume, and status for models."""
    service = MonitoringService(db)
    overview = await service.get_monitoring_overview(project_id=project_id, user=current_user)
    return APIResponse(
        success=True,
        data=overview,
        message=f"Monitoring overview retrieved for {len(overview)} model(s)",
    )


@router.get(
    "/models/{model_id}/drift",
    response_model=APIResponse[ModelDriftAnalysisResponse],
    status_code=status.HTTP_200_OK,
    summary="Compute statistical data drift for model",
)
async def get_model_drift(
    model_id: uuid.UUID,
    alpha: float = Query(0.05, ge=0.001, le=0.5, description="Significance level for KS/Chi-Square test"),
    psi_threshold: float = Query(0.2, ge=0.01, le=1.0, description="PSI alert threshold"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Calculate KS-test, PSI, Wasserstein distance, and distribution histograms for model features."""
    service = MonitoringService(db)
    analysis = await service.analyze_model_drift(
        model_id=model_id,
        current_dataset_id=None,
        alpha=alpha,
        psi_threshold=psi_threshold,
        user=current_user,
    )
    return APIResponse(
        success=True,
        data=analysis,
        message=f"Drift analysis computed: Health status is {analysis.health_status}",
    )


@router.post(
    "/models/{model_id}/drift/analyze",
    response_model=APIResponse[ModelDriftAnalysisResponse],
    status_code=status.HTTP_200_OK,
    summary="Execute drift analysis against specific evaluation dataset",
)
async def analyze_custom_drift(
    model_id: uuid.UUID,
    payload: CustomDriftAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Run statistical distribution comparison between model baseline and an uploaded/selected dataset."""
    service = MonitoringService(db)
    analysis = await service.analyze_model_drift(
        model_id=model_id,
        current_dataset_id=payload.current_dataset_id,
        alpha=payload.alpha,
        psi_threshold=payload.psi_threshold,
        user=current_user,
    )
    return APIResponse(
        success=True,
        data=analysis,
        message=f"Custom drift analysis completed: Status is {analysis.health_status}",
    )
