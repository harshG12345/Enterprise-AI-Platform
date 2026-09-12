"""Celery tasks for asynchronous high-throughput batch predictions."""

import logging
import os
import pickle
import time
import traceback
import uuid
from datetime import UTC, datetime
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from sqlalchemy import select

from app.config.settings import get_settings
from app.core.storage import storage_backend
from app.database.database import get_sync_db
from app.ml.data_loader import DataLoader
from app.models.dataset import Dataset
from app.models.trained_model import TrainedModel
from app.models.training_job import JobStatus, TrainingJob
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)
settings = get_settings()


@celery_app.task(bind=True, name="app.tasks.prediction_tasks.batch_predict_task")
def batch_predict_task(
    self,
    job_id_str: str,
    model_id_str: str,
    project_id_str: str,
    dataset_id_str: str | None = None,
    input_file_path: str | None = None,
    user_id_str: str | None = None,
) -> Dict[str, Any]:
    """Execute high-throughput batch prediction over tabular files in worker process."""
    job_id = uuid.UUID(job_id_str)
    model_id = uuid.UUID(model_id_str)
    project_id = uuid.UUID(project_id_str)
    dataset_id = uuid.UUID(dataset_id_str) if dataset_id_str else None
    user_id = uuid.UUID(user_id_str) if user_id_str else None

    logger.info(f"Starting Celery batch prediction task: job_id={job_id} model_id={model_id}")
    start_time = time.perf_counter()

    with get_sync_db() as db:
        # 1. Update job to RUNNING
        job = db.execute(select(TrainingJob).where(TrainingJob.id == job_id)).scalar_one_or_none()
        if not job:
            logger.error(f"TrainingJob record {job_id} not found")
            return {"status": "FAILED", "error": "Job record not found"}

        job.status = JobStatus.RUNNING
        job.started_at = datetime.now(UTC)
        db.commit()

        try:
            # 2. Retrieve Model Metadata and Artifact
            model_record = db.execute(select(TrainedModel).where(TrainedModel.id == model_id)).scalar_one_or_none()
            if not model_record:
                raise ValueError(f"Trained model {model_id} not found")

            # Determine absolute artifact path
            artifact_abs_path = os.path.join(settings.MODEL_DIR, f"{model_id}.pkl")
            if not os.path.exists(artifact_abs_path):
                artifact_abs_path = storage_backend.get_absolute_path(model_record.artifact_path)

            if not os.path.exists(artifact_abs_path):
                raise FileNotFoundError(f"Model artifact file not found at {artifact_abs_path}")

            with open(artifact_abs_path, "rb") as f:
                artifact_data = pickle.load(f)

            trained_model = artifact_data.get("model")
            feature_names: List[str] = artifact_data.get("feature_names", [])
            task_type: str = artifact_data.get("task_type", "classification")

            if not trained_model:
                raise ValueError("Model object missing in serialized artifact")

            # 3. Load Batch Dataset
            if dataset_id:
                dataset_record = db.execute(select(Dataset).where(Dataset.id == dataset_id)).scalar_one_or_none()
                if not dataset_record:
                    raise ValueError(f"Dataset {dataset_id} not found")
                file_to_load = storage_backend.get_absolute_path(dataset_record.storage_path)
            elif input_file_path:
                file_to_load = (
                    input_file_path
                    if os.path.isabs(input_file_path)
                    else storage_backend.get_absolute_path(input_file_path)
                )
            else:
                raise ValueError("No dataset_id or input_file_path provided for batch prediction")

            if not os.path.exists(file_to_load):
                raise FileNotFoundError(f"Input batch file not found at {file_to_load}")

            df = DataLoader.load_file(file_to_load)
            total_rows = len(df)
            if total_rows == 0:
                raise ValueError("Input batch file is empty")

            # 4. Validate and Align Feature Columns
            missing_features = [f for f in feature_names if f not in df.columns]
            if missing_features:
                raise ValueError(
                    f"Input batch data is missing {len(missing_features)} required feature(s): {missing_features[:5]}"
                )

            # Construct X matrix
            X_df = df[feature_names].copy()
            for col in feature_names:
                X_df[col] = pd.to_numeric(X_df[col], errors="coerce").fillna(0.0)
            X_mat = X_df.to_numpy(dtype=np.float64)

            # 5. Execute Vectorized Model Prediction
            predictions = trained_model.predict(X_mat)

            output_df = df.copy()
            output_df["predicted_value"] = predictions

            # If classification, add probability columns if available
            if task_type == "classification" and hasattr(trained_model, "predict_proba"):
                try:
                    probs = trained_model.predict_proba(X_mat)
                    if probs is not None and probs.ndim == 2:
                        for class_idx in range(probs.shape[1]):
                            output_df[f"probability_class_{class_idx}"] = np.round(probs[:, class_idx], 4)
                except Exception as prob_err:
                    logger.warning(f"Could not compute probabilities for batch: {prob_err}")

            # 6. Save Batch Output Results File
            rel_output_path = os.path.join("data", "predictions", f"batch_predictions_{job_id}.csv").replace("\\", "/")
            output_abs_path = storage_backend.get_absolute_path(rel_output_path)
            os.makedirs(os.path.dirname(output_abs_path), exist_ok=True)

            output_df.to_csv(output_abs_path, index=False)

            duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

            # 7. Update Job Status to SUCCESS
            job.status = JobStatus.SUCCESS
            job.completed_at = datetime.now(UTC)
            job.error_message = None
            db.commit()

            logger.info(
                f"Batch prediction completed successfully: job_id={job_id} rows={total_rows} in {duration_ms}ms"
            )
            return {
                "job_id": str(job_id),
                "status": "SUCCESS",
                "total_rows": total_rows,
                "output_file": rel_output_path,
                "duration_ms": duration_ms,
            }

        except Exception as exc:
            logger.error(f"Batch prediction failed: {exc}\n{traceback.format_exc()}")
            duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            job.status = JobStatus.FAILED
            job.completed_at = datetime.now(UTC)
            job.duration_seconds = duration_ms / 1000.0
            job.error_message = str(exc)
            db.commit()

            return {
                "job_id": str(job_id),
                "status": "FAILED",
                "error": str(exc),
            }
