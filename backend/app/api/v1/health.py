import asyncio
import os
from datetime import UTC, datetime

from fastapi import APIRouter, status
from sqlalchemy import text

from app.config.settings import get_settings
from app.core.responses import APIResponse
from app.database.database import AsyncSessionLocal
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
    """Readiness probe endpoint checking real downstream dependencies."""
    db_status = "unknown"
    redis_status = "standby"
    mlflow_status = "standby"

    # 1. Check Database Connectivity
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            db_status = "connected"
    except Exception:
        db_status = "disconnected"

    # 2. Check Redis Connectivity (if configured)
    if settings.REDIS_URL and not settings.is_testing:
        try:
            import redis.asyncio as aioredis

            r = aioredis.from_url(settings.REDIS_URL, socket_timeout=2.0)
            await asyncio.wait_for(r.ping(), timeout=2.0)
            await r.aclose()
            redis_status = "connected"
        except Exception:
            redis_status = "disconnected"
    else:
        redis_status = "connected" if settings.is_testing else "standby"

    # 3. Check MLflow & Storage Directory
    try:
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        os.makedirs(settings.MODEL_DIR, exist_ok=True)
        mlflow_status = "connected"
    except Exception:
        mlflow_status = "degraded"

    is_overall_ready = db_status == "connected"

    data = ReadinessResponse(
        status="ready" if is_overall_ready else "degraded",
        database=db_status,
        redis=redis_status,
        mlflow=mlflow_status,
        timestamp=datetime.now(UTC).isoformat(),
    )
    return APIResponse(
        success=True,
        data=data,
        message="All systems operational and ready for traffic" if is_overall_ready else "Systems operating in degraded mode",
    )
