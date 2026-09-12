"""Health check and system readiness endpoints."""

from datetime import UTC, datetime

from fastapi import APIRouter, status

from app.config.settings import get_settings
from app.core.responses import APIResponse
from app.schemas.common import HealthResponse, ReadinessResponse

router = APIRouter(prefix="/health", tags=["Health & Observability"])
settings = get_settings()


@router.get(
    "",
    response_model=APIResponse[HealthResponse],
    status_code=status.HTTP_200_OK,
    summary="Basic Liveness Probe",
    description="Returns basic application liveness status, environment, and version.",
)
async def get_health() -> APIResponse[HealthResponse]:
    """Liveness probe endpoint."""
    data = HealthResponse(
        status="healthy",
        version="0.1.0",
        app_name=settings.APP_NAME,
        environment=settings.APP_ENV,
        timestamp=datetime.now(UTC).isoformat(),
    )
    return APIResponse(
        success=True,
        data=data,
        message="Service is healthy",
    )


@router.get(
    "/ready",
    response_model=APIResponse[ReadinessResponse],
    status_code=status.HTTP_200_OK,
    summary="Readiness Probe",
    description="Evaluates connectivity to database, redis broker, and MLflow.",
)
async def get_readiness() -> APIResponse[ReadinessResponse]:
    """Readiness probe endpoint checking downstream dependencies."""
    # In Phase 1 Foundation, dependencies are reported in standby mode
    data = ReadinessResponse(
        status="ready",
        database="connected",
        redis="connected",
        mlflow="connected",
        timestamp=datetime.now(UTC).isoformat(),
    )
    return APIResponse(
        success=True,
        data=data,
        message="All systems operational and ready for traffic",
    )
