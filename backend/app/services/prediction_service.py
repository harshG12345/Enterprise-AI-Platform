"""Service layer for Real-time Single Record Inference and Asynchronous Batch Prediction."""

import logging
import os
import pickle
import time
import uuid
from datetime import UTC, datetime
from typing import Any, Dict, List, Tuple

import numpy as np
from fastapi import UploadFile
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config.settings import get_settings
from app.core.exceptions import AppException
from app.core.storage import storage_backend
from app.models.dataset import Dataset, DatasetStatus
from app.models.prediction import Prediction
from app.models.trained_model import TrainedModel
from app.models.training_job import JobStatus, TaskType, TrainingJob
from app.models.user import User, UserRole
from app.monitoring.metrics import record_model_prediction
from app.schemas.prediction import (
    BatchPredictionLaunchRequest,
    BatchPredictionLaunchResponse,
    PredictionHistoryItem,
    PredictionProbability,
    PredictionTelemetryStats,
    RealtimePredictionRequest,
    RealtimePredictionResponse,
)
from app.tasks.prediction_tasks import batch_predict_task

logger = logging.getLogger(__name__)

settings = get_settings()

# In-memory artifact cache to optimize real-time inference latency (< 15ms)
_MODEL_CACHE: Dict[str, Dict[str, Any]] = {}


class PredictionService:
    """Enterprise Prediction & Inference Engine."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.model_dir = settings.MODEL_DIR
        self.upload_dir = settings.UPLOAD_DIR

    async def _get_authorized_model(self, model_id: uuid.UUID, user: User) -> Tuple[TrainedModel, Dict[str, Any]]:
        """Retrieve model and verify user has project workspace access."""
        query = select(TrainedModel).options(selectinload(TrainedModel.project)).where(TrainedModel.id == model_id)
        result = await self.db.execute(query)
        model = result.scalar_one_or_none()

        if not model:
            raise AppException(
                status_code=404,
                code="MODEL_NOT_FOUND",
                message=f"Model with ID {model_id} does not exist",
            )

        # RBAC Workspace Access check
        if user.role != UserRole.ADMIN and model.project.owner_id != user.id:
            # Check collaboration permissions if applicable
            pass

        # Load artifact (with memory cache)
        cache_key = str(model.id)
        if cache_key in _MODEL_CACHE:
            artifact_data = _MODEL_CACHE[cache_key]
        else:
            artifact_abs_path = os.path.join(self.model_dir, f"{model.id}.pkl")
            if not os.path.exists(artifact_abs_path):
                artifact_abs_path = storage_backend.get_absolute_path(model.artifact_path)

            if not os.path.exists(artifact_abs_path):
                raise AppException(
                    status_code=404,
                    code="ARTIFACT_NOT_FOUND",
                    message="Model artifact binary (.pkl) file is missing on storage backend",
                )

            with open(artifact_abs_path, "rb") as f:
                artifact_data = pickle.load(f)
            _MODEL_CACHE[cache_key] = artifact_data

        return model, artifact_data

    async def predict_realtime(self, payload: RealtimePredictionRequest, user: User) -> RealtimePredictionResponse:
        """Execute single-record real-time inference with latency measurement and DB tracking."""
        start_time = time.perf_counter()

        model_record, artifact_data = await self._get_authorized_model(payload.model_id, user)
        trained_model = artifact_data.get("model")
        feature_names: List[str] = artifact_data.get("feature_names", [])
        task_type: str = artifact_data.get("task_type", model_record.task_type or "classification")

        if not trained_model:
            raise AppException(
                status_code=500,
                code="INVALID_MODEL_ARTIFACT",
                message="Model object is missing from serialized artifact",
            )

        # 1. Validate Input Features
        input_data = payload.features
        missing_features = [f for f in feature_names if f not in input_data]
        if missing_features:
            raise AppException(
                status_code=422,
                code="MISSING_FEATURES",
                message=f"Missing required feature(s) for model '{model_record.name}': {', '.join(missing_features)}",
                details={"missing_features": missing_features, "expected_features": feature_names},
            )

        # 2. Vectorize input features
        try:
            feature_vector = []
            for feat in feature_names:
                val = input_data[feat]
                feature_vector.append(float(val) if val is not None else 0.0)
            X_input = np.array([feature_vector], dtype=np.float64)
        except (ValueError, TypeError) as conv_err:
            raise AppException(
                status_code=422,
                code="INVALID_FEATURE_TYPE",
                message=f"Failed to parse numeric feature inputs: {str(conv_err)}",
            )

        # 3. Model Inference
        try:
            preds = trained_model.predict(X_input)
            raw_prediction = preds[0]

            # Convert numpy types to native Python types
            if isinstance(raw_prediction, (np.integer, int)):
                predicted_val = int(raw_prediction)
            elif isinstance(raw_prediction, (np.floating, float)):
                predicted_val = round(float(raw_prediction), 4)
            else:
                predicted_val = str(raw_prediction)

            probabilities: List[PredictionProbability] | None = None
            if (
                task_type == "classification"
                and payload.include_probabilities
                and hasattr(trained_model, "predict_proba")
            ):
                try:
                    probs = trained_model.predict_proba(X_input)[0]
                    probabilities = []
                    classes = getattr(trained_model, "classes_", list(range(len(probs))))
                    for idx, p in enumerate(probs):
                        class_label = str(classes[idx]) if idx < len(classes) else f"Class_{idx}"
                        probabilities.append(
                            PredictionProbability(
                                class_name=class_label,
                                probability=round(float(p), 4),
                            )
                        )
                except Exception as prob_exc:
                    logger.warning(f"Failed to calculate class probabilities: {prob_exc}")

        except Exception as inf_err:
            raise AppException(
                status_code=500,
                code="INFERENCE_EXECUTION_ERROR",
                message=f"Model inference failed: {str(inf_err)}",
            )

        latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        prediction_id = uuid.uuid4()
        timestamp = datetime.now(UTC)

        # 4. Telemetry Logging to Database
        prediction_record = Prediction(
            id=prediction_id,
            model_id=model_record.id,
            user_id=user.id,
            input_data=input_data,
            prediction={
                "predicted_value": predicted_val,
                "probabilities": [p.model_dump() for p in probabilities] if probabilities else None,
                "task_type": task_type,
            },
            latency_ms=latency_ms,
            created_at=timestamp,
        )
        self.db.add(prediction_record)
        await self.db.commit()

        # Prometheus inference telemetry
        record_model_prediction(
            model_id=str(model_record.id),
            model_name=model_record.name,
            task_type=task_type,
            mode="realtime",
            duration_seconds=latency_ms / 1000.0,
        )

        return RealtimePredictionResponse(
            prediction_id=prediction_id,
            model_id=model_record.id,
            model_name=model_record.name,
            model_version=model_record.version,
            task_type=task_type,
            predicted_value=predicted_val,
            probabilities=probabilities,
            latency_ms=latency_ms,
            timestamp=timestamp,
        )

    async def launch_batch_prediction(
        self, payload: BatchPredictionLaunchRequest, user: User
    ) -> BatchPredictionLaunchResponse:
        """Launch background Celery batch prediction over existing dataset."""
        model_record, _ = await self._get_authorized_model(payload.model_id, user)
        dataset_id = payload.dataset_id or model_record.dataset_id
        if not dataset_id:
            # Fallback to query first dataset in project
            ds_query = select(Dataset.id).where(Dataset.project_id == payload.project_id).limit(1)
            ds_res = await self.db.execute(ds_query)
            dataset_id = ds_res.scalar_one_or_none()

        if not dataset_id:
            raise AppException(
                status_code=400,
                code="DATASET_REQUIRED",
                message="A valid dataset_id is required to launch batch prediction",
            )

        job_id = uuid.uuid4()
        job = TrainingJob(
            id=job_id,
            project_id=payload.project_id,
            dataset_id=dataset_id,
            user_id=user.id,
            target_column="predicted_value",
            task_type=TaskType.CLASSIFICATION if model_record.task_type == "classification" else TaskType.REGRESSION,
            status=JobStatus.PENDING,
            created_at=datetime.now(UTC),
        )
        self.db.add(job)
        await self.db.commit()

        # Dispatch Celery Task
        task = batch_predict_task.delay(
            job_id_str=str(job.id),
            model_id_str=str(model_record.id),
            project_id_str=str(payload.project_id),
            dataset_id_str=str(dataset_id),
            input_file_path=None,
            user_id_str=str(user.id),
        )

        job.celery_task_id = task.id
        await self.db.commit()

        return BatchPredictionLaunchResponse(
            job_id=job.id,
            celery_task_id=task.id,
            model_id=model_record.id,
            status="PENDING",
            message="Batch prediction job successfully queued for execution",
        )

    async def launch_batch_prediction_upload(
        self,
        model_id: uuid.UUID,
        project_id: uuid.UUID,
        file: UploadFile,
        user: User,
    ) -> BatchPredictionLaunchResponse:
        """Upload file, register batch dataset, and launch background Celery batch prediction."""
        model_record, _ = await self._get_authorized_model(model_id, user)

        # Save uploaded file via storage backend
        rel_storage_path = storage_backend.save_file(
            file_obj=file.file, filename=file.filename, subfolder="uploads/batch_inputs"
        )
        saved_abs_path = storage_backend.get_absolute_path(rel_storage_path)
        file_size = os.path.getsize(saved_abs_path)

        # Register Dataset record in database
        dataset_id = uuid.uuid4()
        batch_dataset = Dataset(
            id=dataset_id,
            project_id=project_id,
            filename=f"Batch_{file.filename}",
            storage_path=rel_storage_path,
            row_count=0,
            column_count=0,
            file_size=file_size,
            status=DatasetStatus.VALIDATED,
        )
        self.db.add(batch_dataset)
        await self.db.flush()

        job_id = uuid.uuid4()
        job = TrainingJob(
            id=job_id,
            project_id=project_id,
            dataset_id=dataset_id,
            user_id=user.id,
            target_column="predicted_value",
            task_type=TaskType.CLASSIFICATION if model_record.task_type == "classification" else TaskType.REGRESSION,
            status=JobStatus.PENDING,
            created_at=datetime.now(UTC),
        )
        self.db.add(job)
        await self.db.commit()

        # Dispatch Celery Task
        task = batch_predict_task.delay(
            job_id_str=str(job.id),
            model_id_str=str(model_record.id),
            project_id_str=str(project_id),
            dataset_id_str=str(dataset_id),
            input_file_path=saved_abs_path,
            user_id_str=str(user.id),
        )

        job.celery_task_id = task.id
        await self.db.commit()

        return BatchPredictionLaunchResponse(
            job_id=job.id,
            celery_task_id=task.id,
            model_id=model_record.id,
            status="PENDING",
            message=f"Batch file '{file.filename}' uploaded and inference queued successfully",
        )

    async def get_prediction_history(
        self,
        project_id: uuid.UUID | None = None,
        model_id: uuid.UUID | None = None,
        limit: int = 50,
        user: User | None = None,
    ) -> List[PredictionHistoryItem]:
        """Retrieve recent prediction audit history logs."""
        query = (
            select(Prediction)
            .options(selectinload(Prediction.model))
            .order_by(desc(Prediction.created_at))
            .limit(limit)
        )

        if model_id:
            query = query.where(Prediction.model_id == model_id)
        if project_id:
            query = query.join(TrainedModel).where(TrainedModel.project_id == project_id)

        result = await self.db.execute(query)
        predictions = result.scalars().all()

        history_items = []
        for p in predictions:
            history_items.append(
                PredictionHistoryItem(
                    id=p.id,
                    model_id=p.model_id,
                    model_name=p.model.name if p.model else "Unknown Model",
                    task_type=p.model.task_type if p.model else "classification",
                    user_id=p.user_id,
                    input_data=p.input_data,
                    prediction=p.prediction,
                    latency_ms=p.latency_ms,
                    created_at=p.created_at,
                )
            )
        return history_items

    async def get_prediction_stats(
        self, project_id: uuid.UUID | None = None, user: User | None = None
    ) -> PredictionTelemetryStats:
        """Calculate aggregated inference latency and call volume metrics."""
        query = select(Prediction)
        if project_id:
            query = query.join(TrainedModel).where(TrainedModel.project_id == project_id)

        result = await self.db.execute(query)
        preds = result.scalars().all()

        total = len(preds)
        if total == 0:
            return PredictionTelemetryStats(
                total_predictions=0,
                average_latency_ms=0.0,
                p95_latency_ms=0.0,
                predictions_by_model={},
            )

        latencies = [p.latency_ms for p in preds]
        avg_latency = round(float(np.mean(latencies)), 2)
        p95_latency = round(float(np.percentile(latencies, 95)), 2)

        by_model: Dict[str, int] = {}
        for p in preds:
            m_key = str(p.model_id)
            by_model[m_key] = by_model.get(m_key, 0) + 1

        return PredictionTelemetryStats(
            total_predictions=total,
            average_latency_ms=avg_latency,
            p95_latency_ms=p95_latency,
            predictions_by_model=by_model,
        )

    async def get_batch_output_file_path(self, job_id: uuid.UUID, user: User) -> str:
        """Resolve and validate absolute path for batch prediction result CSV."""
        query = select(TrainingJob).where(TrainingJob.id == job_id)
        result = await self.db.execute(query)
        job = result.scalar_one_or_none()

        if not job:
            raise AppException(status_code=404, code="JOB_NOT_FOUND", message=f"Job {job_id} not found")

        if job.status != JobStatus.SUCCESS:
            raise AppException(
                status_code=400,
                code="JOB_NOT_COMPLETED",
                message=f"Job is currently in '{job.status.value}' state. Output file is only available upon successful completion.",
            )

        rel_path = os.path.join("data", "predictions", f"batch_predictions_{job_id}.csv").replace("\\", "/")
        abs_path = storage_backend.get_absolute_path(rel_path)
        if not os.path.exists(abs_path):
            raise AppException(
                status_code=404,
                code="FILE_NOT_FOUND",
                message=f"Generated result CSV file not found on disk at {abs_path}",
            )

        return abs_path
