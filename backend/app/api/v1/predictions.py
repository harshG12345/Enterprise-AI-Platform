"""REST API router for Real-Time and Asynchronous Batch Prediction Engine."""

import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user
from app.core.responses import APIResponse
from app.database.database import get_db
from app.models.user import User
from app.schemas.prediction import (
    BatchPredictionLaunchRequest,
    BatchPredictionLaunchResponse,
    PredictionHistoryItem,
    PredictionTelemetryStats,
    RealtimePredictionRequest,
    RealtimePredictionResponse,
)
from app.services.prediction_service import PredictionService

router = APIRouter(prefix="/predictions", tags=["Predictions & Inference Engine"])


@router.post(
    "/realtime",
    response_model=APIResponse[RealtimePredictionResponse],
    status_code=status.HTTP_200_OK,
    summary="Execute real-time single record prediction",
)
async def predict_realtime(
    payload: RealtimePredictionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Run low-latency model inference on single tabular input record."""
    service = PredictionService(db)
    prediction = await service.predict_realtime(payload=payload, user=current_user)
    return APIResponse(
        success=True,
        data=prediction,
        message=f"Prediction executed in {prediction.latency_ms} ms",
    )


@router.post(
    "/models/{model_id}/predict",
    response_model=APIResponse[RealtimePredictionResponse],
    status_code=status.HTTP_200_OK,
    summary="Execute real-time prediction for specific model",
)
async def predict_for_model(
    model_id: uuid.UUID,
    features: Dict[str, Any],
    include_probabilities: bool = Query(True, description="Include probability scores for classification"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Direct REST inference endpoint targeting specific model ID."""
    service = PredictionService(db)
    payload = RealtimePredictionRequest(
        model_id=model_id,
        features=features,
        include_probabilities=include_probabilities,
    )
    prediction = await service.predict_realtime(payload=payload, user=current_user)
    return APIResponse(
        success=True,
        data=prediction,
        message=f"Prediction executed in {prediction.latency_ms} ms",
    )


@router.post(
    "/batch",
    response_model=APIResponse[BatchPredictionLaunchResponse],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Launch background batch inference job on registered dataset",
)
async def launch_batch_prediction(
    payload: BatchPredictionLaunchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Queue asynchronous batch prediction workflow via Celery."""
    service = PredictionService(db)
    response = await service.launch_batch_prediction(payload=payload, user=current_user)
    return APIResponse(
        success=True,
        data=response,
        message="Batch prediction job accepted and scheduled for execution",
    )


@router.post(
    "/batch/upload",
    response_model=APIResponse[BatchPredictionLaunchResponse],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload file and launch background batch inference job",
)
async def launch_batch_prediction_upload(
    model_id: uuid.UUID = Form(...),
    project_id: uuid.UUID = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Stream tabular file upload and trigger asynchronous batch prediction."""
    service = PredictionService(db)
    response = await service.launch_batch_prediction_upload(
        model_id=model_id, project_id=project_id, file=file, user=current_user
    )
    return APIResponse(
        success=True,
        data=response,
        message="Batch file uploaded and inference queued successfully",
    )


@router.get(
    "/batch/{job_id}/download",
    summary="Download generated batch prediction CSV results",
)
async def download_batch_results(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Download result CSV with predictions and confidence scores."""
    service = PredictionService(db)
    file_path = await service.get_batch_output_file_path(job_id=job_id, user=current_user)
    return FileResponse(
        path=file_path,
        filename=f"batch_predictions_{job_id}.csv",
        media_type="text/csv",
    )


@router.get(
    "",
    response_model=APIResponse[List[PredictionHistoryItem]],
    status_code=status.HTTP_200_OK,
    summary="Retrieve prediction inference telemetry logs",
)
async def get_prediction_history(
    project_id: uuid.UUID | None = Query(None, description="Filter predictions by project"),
    model_id: uuid.UUID | None = Query(None, description="Filter predictions by model"),
    limit: int = Query(50, ge=1, le=200, description="Max logs to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve historical inference events with input payloads, predictions, and latencies."""
    service = PredictionService(db)
    history = await service.get_prediction_history(
        project_id=project_id, model_id=model_id, limit=limit, user=current_user
    )
    return APIResponse(
        success=True,
        data=history,
        message=f"Retrieved {len(history)} prediction log entry(ies)",
    )


@router.get(
    "/stats",
    response_model=APIResponse[PredictionTelemetryStats],
    status_code=status.HTTP_200_OK,
    summary="Get inference throughput and latency telemetry",
)
async def get_prediction_stats(
    project_id: uuid.UUID | None = Query(None, description="Filter stats by project"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get aggregated inference metrics including total predictions, average latency, and P95 latency."""
    service = PredictionService(db)
    stats = await service.get_prediction_stats(project_id=project_id, user=current_user)
    return APIResponse(
        success=True,
        data=stats,
        message="Inference statistics calculated successfully",
    )
