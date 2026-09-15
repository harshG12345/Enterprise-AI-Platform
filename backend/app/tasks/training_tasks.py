"""Asynchronous Celery training tasks adhering strictly to serialization and DB isolation rules."""

import logging
import os
import pickle
import traceback
import uuid
from datetime import UTC, datetime
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from sqlalchemy import select

from app.config.settings import get_settings
from app.core.storage import storage_backend
from app.database.database import get_sync_db
from app.ml.data_loader import DataLoader
from app.ml.tracker import mlflow_tracker
from app.ml.trainer import ModelTrainer
from app.models.audit_log import AuditLog
from app.models.dataset import Dataset
from app.models.experiment import Experiment
from app.models.trained_model import ModelStatus, TrainedModel
from app.models.training_job import JobStatus, TrainingJob
from app.schemas.training import CrossValidationConfig
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)
settings = get_settings()


def _prepare_data_from_raw_sync(
    df: pd.DataFrame, target_col: str, task_type: str
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, List[str]]:
    """Clean, split, and vectorize tabular data in worker process with zero data leakage."""
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataset")

    # 1. Target column extraction
    y_series = df[target_col].copy()
    if task_type == "classification":
        unique_labels = sorted(y_series.dropna().unique().tolist())
        label_map = {lbl: idx for idx, lbl in enumerate(unique_labels)}
        y_clean = y_series.map(label_map).fillna(0).to_numpy(dtype=int)
    else:
        y_clean = pd.to_numeric(y_series, errors="coerce").fillna(0.0).to_numpy(dtype=float)

    # 2. Features DataFrame
    X_df = df.drop(columns=[target_col]).copy()
    n_samples = len(X_df)
    if n_samples < 5:
        raise ValueError("Dataset has too few rows for ML training (minimum 5 rows required)")

    # 3. Random Train-Test Split (80/20) with reproducible seed
    rng = np.random.RandomState(42)
    indices = np.arange(n_samples)
    rng.shuffle(indices)

    test_size = max(1, int(round(n_samples * 0.2)))
    train_idx = indices[:-test_size]
    test_idx = indices[-test_size:]

    X_train_df = X_df.iloc[train_idx].reset_index(drop=True)
    X_test_df = X_df.iloc[test_idx].reset_index(drop=True)
    y_train = y_clean[train_idx]
    y_test = y_clean[test_idx]

    # 4. Feature Vectorization (Fitted strictly on train split)
    train_cols_list: List[np.ndarray] = []
    test_cols_list: List[np.ndarray] = []
    feature_names: List[str] = []

    for col in X_df.columns:
        is_num = pd.api.types.is_numeric_dtype(X_df[col])
        if is_num:
            tr_vals = pd.to_numeric(X_train_df[col], errors="coerce")
            median_val = float(tr_vals.median()) if pd.notna(tr_vals.median()) else 0.0
            tr_clean = tr_vals.fillna(median_val).to_numpy(dtype=float)
            te_clean = pd.to_numeric(X_test_df[col], errors="coerce").fillna(median_val).to_numpy(dtype=float)

            mean_val = float(np.mean(tr_clean))
            std_val = float(np.std(tr_clean))
            std_val = std_val if std_val > 1e-8 else 1.0

            tr_scaled = (tr_clean - mean_val) / std_val
            te_scaled = (te_clean - mean_val) / std_val

            train_cols_list.append(tr_scaled.reshape(-1, 1))
            test_cols_list.append(te_scaled.reshape(-1, 1))
            feature_names.append(col)
        else:
            # Frequency encoding for categoricals
            tr_str = X_train_df[col].astype(str).fillna("missing")
            te_str = X_test_df[col].astype(str).fillna("missing")
            freq_map = tr_str.value_counts(normalize=True).to_dict()

            tr_enc = tr_str.map(freq_map).fillna(0.0).to_numpy(dtype=float)
            te_enc = te_str.map(freq_map).fillna(0.0).to_numpy(dtype=float)

            train_cols_list.append(tr_enc.reshape(-1, 1))
            test_cols_list.append(te_enc.reshape(-1, 1))
            feature_names.append(f"{col}_freq")

    if not train_cols_list:
        raise ValueError("No usable feature columns found in dataset")

    X_train = np.hstack(train_cols_list)
    X_test = np.hstack(test_cols_list)

    return X_train, y_train, X_test, y_test, feature_names


@celery_app.task(
    bind=True,
    name="app.tasks.training_tasks.train_model_async_task",
    max_retries=3,
    default_retry_delay=5,
)
def train_model_async_task(
    self,
    job_id_str: str,
    project_id_str: str,
    dataset_id_str: str,
    user_id_str: str,
    target_column: str,
    task_type: str,
    algorithm: str,
    hyperparameters: Dict[str, Any],
    model_name: str | None = None,
    cv_config_dict: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Execute asynchronous ML model training, cross-validation, MLflow logging, and DB persistence."""
    logger.info(f"Starting Celery training task for job: {job_id_str}")
    job_uuid = uuid.UUID(job_id_str)
    project_uuid = uuid.UUID(project_id_str)
    dataset_uuid = uuid.UUID(dataset_id_str)
    user_uuid = uuid.UUID(user_id_str)

    # Worker creates its own isolated synchronous database session
    db = get_sync_db()

    try:
        # 1. Update job to RUNNING
        job = db.execute(select(TrainingJob).where(TrainingJob.id == job_uuid)).scalar_one_or_none()

        if not job:
            raise ValueError(f"TrainingJob with ID '{job_id_str}' not found in database")

        job.status = JobStatus.RUNNING
        job.started_at = datetime.now(UTC)
        job.celery_task_id = self.request.id or str(uuid.uuid4())
        db.commit()

        # 2. Fetch dataset record
        dataset = db.execute(select(Dataset).where(Dataset.id == dataset_uuid)).scalar_one_or_none()

        if not dataset:
            raise ValueError(f"Dataset with ID '{dataset_id_str}' not found")

        # 3. Load tabular data from storage
        abs_path = storage_backend.get_absolute_path(dataset.storage_path)
        df = DataLoader.load_file(abs_path)

        # 4. Prepare data & feature vectors with zero leakage
        X_train, y_train, X_test, y_test, feature_names = _prepare_data_from_raw_sync(
            df=df, target_col=target_column, task_type=task_type.lower()
        )

        # 5. Parse CV config
        cv_config = CrossValidationConfig(**cv_config_dict) if cv_config_dict else CrossValidationConfig()

        # 6. Execute model training & evaluation
        train_results = ModelTrainer.train_and_evaluate(
            algorithm=algorithm,
            hyperparameters=hyperparameters,
            X_train=X_train,
            y_train=y_train,
            X_test=X_test,
            y_test=y_test,
            feature_names=feature_names,
            task_type=task_type.lower(),
            cv_config=cv_config,
        )

        # 7. Serialize Model Artifact
        model_id = uuid.uuid4()
        model_filename = f"{model_id}.pkl"
        os.makedirs(settings.MODEL_DIR, exist_ok=True)
        artifact_rel_path = os.path.join("data", "models", model_filename).replace("\\", "/")
        artifact_abs_path = os.path.join(settings.MODEL_DIR, model_filename)

        final_model_name = model_name if model_name else f"{algorithm}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"

        artifact_data = {
            "model_id": str(model_id),
            "job_id": str(job_uuid),
            "project_id": str(project_uuid),
            "dataset_id": str(dataset_uuid),
            "name": final_model_name,
            "algorithm": algorithm,
            "task_type": task_type.lower(),
            "target_column": target_column,
            "feature_names": feature_names,
            "hyperparameters": hyperparameters,
            "model": train_results["model"],
            "train_metrics": train_results["train_metrics"].model_dump(),
            "test_metrics": train_results["test_metrics"].model_dump(),
            "created_at": datetime.now(UTC).isoformat(),
        }

        with open(artifact_abs_path, "wb") as f:
            pickle.dump(artifact_data, f)

        # 8. MLflow Tracking & Artifact Logging
        exp_stmt = select(Experiment).where(
            Experiment.project_id == project_uuid,
            Experiment.name == "Model Training Runs",
        )
        experiment = db.execute(exp_stmt).scalar_one_or_none()

        if not experiment:
            exp_uuid = uuid.uuid4()
            mlflow_exp_id = mlflow_tracker.create_experiment(name=f"{project_uuid}_Model Training Runs")
            experiment = Experiment(
                id=exp_uuid,
                project_id=project_uuid,
                dataset_id=dataset_uuid,
                name="Model Training Runs",
                mlflow_experiment_id=mlflow_exp_id,
                created_at=datetime.now(UTC),
            )
            db.add(experiment)
            db.flush()

        mlflow_exp_id = experiment.mlflow_experiment_id or str(experiment.id)
        run_id = mlflow_tracker.start_run(
            experiment_id=mlflow_exp_id,
            run_name=final_model_name,
            tags={
                "user_id": str(user_uuid),
                "project_id": str(project_uuid),
                "dataset_id": str(dataset_uuid),
                "algorithm": algorithm,
                "task_type": task_type.lower(),
            },
        )

        log_params = dict(hyperparameters)
        log_params.update(
            {
                "algorithm": algorithm,
                "target_column": target_column,
                "task_type": task_type.lower(),
            }
        )
        mlflow_tracker.log_params(run_id, log_params)

        metrics_to_log = {k: v for k, v in train_results["test_metrics"].model_dump().items() if v is not None}
        if train_results["cv_summary"]:
            metrics_to_log["cv_mean_score"] = train_results["cv_summary"].mean_val_score
            metrics_to_log["cv_std_score"] = train_results["cv_summary"].std_val_score
        mlflow_tracker.log_metrics(run_id, metrics_to_log)

        # Log artifacts
        mlflow_tracker.log_artifact(run_id, artifact_abs_path)
        if train_results.get("feature_importances"):
            mlflow_tracker.log_dict(
                run_id,
                [fi.model_dump() for fi in train_results["feature_importances"]],
                "feature_importances.json",
            )
        if train_results.get("confusion_matrix"):
            mlflow_tracker.log_dict(
                run_id,
                train_results["confusion_matrix"].model_dump(),
                "confusion_matrix.json",
            )
        mlflow_tracker.end_run(run_id, status="FINISHED")

        # 9. Create TrainedModel in DB
        metrics_payload = {
            "train": train_results["train_metrics"].model_dump(),
            "test": train_results["test_metrics"].model_dump(),
            "cv": train_results["cv_summary"].model_dump() if train_results["cv_summary"] else None,
            "duration_ms": train_results["duration_ms"],
        }

        trained_model = TrainedModel(
            id=model_id,
            project_id=project_uuid,
            dataset_id=dataset_uuid,
            experiment_id=experiment.id,
            mlflow_run_id=run_id,
            name=final_model_name,
            version="v1.0.0",
            task_type=task_type.lower(),
            framework="custom-numpy-engine",
            metrics=metrics_payload,
            artifact_path=artifact_rel_path,
            status=ModelStatus.DEVELOPMENT,
            created_at=datetime.now(UTC),
        )
        db.add(trained_model)

        # 10. Mark TrainingJob SUCCESS
        job.status = JobStatus.SUCCESS
        job.completed_at = datetime.now(UTC)

        # 11. Audit log
        audit = AuditLog(
            id=uuid.uuid4(),
            user_id=user_uuid,
            action="ASYNC_TRAIN_MODEL_SUCCESS",
            resource_type="TRAINING_JOB",
            resource_id=str(job_uuid),
            metadata_json={
                "model_id": str(model_id),
                "algorithm": algorithm,
                "metrics": train_results["test_metrics"].model_dump(),
            },
        )
        db.add(audit)
        db.commit()

        logger.info(f"Training task for job {job_id_str} completed successfully. Model ID: {model_id}")

        return {
            "job_id": str(job_uuid),
            "model_id": str(model_id),
            "status": "SUCCESS",
            "metrics": train_results["test_metrics"].model_dump(),
            "training_duration_ms": train_results["duration_ms"],
        }

    except Exception as exc:
        logger.error(f"Error during training task for job {job_id_str}: {exc}\n{traceback.format_exc()}")
        try:
            job = db.execute(select(TrainingJob).where(TrainingJob.id == job_uuid)).scalar_one_or_none()
            if job:
                job.status = JobStatus.FAILED
                job.error_message = str(exc)
                job.completed_at = datetime.now(UTC)
                db.commit()
        except Exception as db_err:
            logger.error(f"Failed to update failed job status: {db_err}")
            db.rollback()

        raise exc

    finally:
        db.close()
