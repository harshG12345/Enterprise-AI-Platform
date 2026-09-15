"""Service layer for model training execution, cross-validation, and model persistence."""

import os
import pickle
import uuid
from datetime import UTC, datetime
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config.settings import get_settings
from app.core.exceptions import AuthorizationException, NotFoundException, ValidationException
from app.core.storage import storage_backend
from app.ml.data_loader import DataLoader
from app.ml.trainer import ModelTrainer
from app.models.audit_log import AuditLog
from app.models.dataset import Dataset
from app.models.notification import Notification, NotificationCategory, NotificationType
from app.models.project import Project
from app.models.trained_model import ModelStatus, TrainedModel
from app.models.training_job import JobStatus, TaskType, TrainingJob
from app.models.user import User, UserRole
from app.schemas.training import (
    AlgorithmInfo,
    TrainingJobCreate,
    TrainingJobDetailResponse,
)

settings = get_settings()


class TrainingService:
    """Orchestrates model training, cross validation, artifact storage, and DB persistence."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.model_dir = settings.MODEL_DIR
        self.pipelines_dir = os.path.join(settings.UPLOAD_DIR, "pipelines")
        os.makedirs(self.model_dir, exist_ok=True)

    async def _verify_project_access(self, project_id: uuid.UUID, user: User) -> Project:
        """Verify project exists and user has authorization."""
        stmt = select(Project).where(Project.id == project_id)
        result = await self.db.execute(stmt)
        project = result.scalar_one_or_none()
        if not project:
            raise NotFoundException(f"Project with ID '{project_id}' not found")
        if user.role != UserRole.ADMIN and project.owner_id != user.id:
            raise AuthorizationException("You do not have permission to perform training in this project")
        return project

    async def _get_authorized_dataset(self, dataset_id: uuid.UUID, user: User) -> Dataset:
        """Fetch dataset and assert authorization."""
        stmt = select(Dataset).options(selectinload(Dataset.project)).where(Dataset.id == dataset_id)
        result = await self.db.execute(stmt)
        dataset = result.scalar_one_or_none()
        if not dataset:
            raise NotFoundException(f"Dataset with ID '{dataset_id}' not found")
        if user.role != UserRole.ADMIN and dataset.project.owner_id != user.id:
            raise AuthorizationException("You do not have permission to access this dataset")
        return dataset

    async def _log_audit_event(
        self,
        action: str,
        user_id: uuid.UUID,
        resource_id: str,
        metadata: dict | None = None,
    ) -> None:
        """Create audit log entry."""
        audit = AuditLog(
            id=uuid.uuid4(),
            user_id=user_id,
            action=action,
            resource_type="TRAINING_JOB",
            resource_id=resource_id,
            metadata_json=metadata or {},
        )
        self.db.add(audit)
        await self.db.commit()

    def list_algorithms(self) -> List[AlgorithmInfo]:
        """Return available model algorithms and their schemas."""
        return ModelTrainer.list_available_algorithms()

    def _prepare_data_from_raw(
        self, df: pd.DataFrame, target_col: str, task_type: str
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, List[str]]:
        """Clean, split, and vectorize tabular data with zero data leakage."""
        if target_col not in df.columns:
            raise ValidationException(f"Target column '{target_col}' not found in dataset")

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
            raise ValidationException("Dataset has too few rows for ML training (minimum 5 rows required)")

        # 3. Stratified or random Train-Test Split (80/20)
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
                # Categorical column (Frequency encoding)
                tr_str = X_train_df[col].astype(str).fillna("missing")
                te_str = X_test_df[col].astype(str).fillna("missing")
                freq_map = tr_str.value_counts(normalize=True).to_dict()

                tr_enc = tr_str.map(freq_map).fillna(0.0).to_numpy(dtype=float)
                te_enc = te_str.map(freq_map).fillna(0.0).to_numpy(dtype=float)

                train_cols_list.append(tr_enc.reshape(-1, 1))
                test_cols_list.append(te_enc.reshape(-1, 1))
                feature_names.append(f"{col}_freq")

        if not train_cols_list:
            raise ValidationException("No usable feature columns found in dataset")

        X_train = np.hstack(train_cols_list)
        X_test = np.hstack(test_cols_list)

        return X_train, y_train, X_test, y_test, feature_names

    async def train_model(self, payload: TrainingJobCreate, user: User) -> TrainingJobDetailResponse:
        """Execute full training lifecycle, cross validation, artifact persistence, and audit logging."""
        await self._verify_project_access(payload.project_id, user)
        dataset = await self._get_authorized_dataset(payload.dataset_id, user)

        job_id = uuid.uuid4()
        task_type_enum = (
            TaskType.CLASSIFICATION if payload.task_type.lower() == "classification" else TaskType.REGRESSION
        )

        # 1. Register TrainingJob in DB
        job = TrainingJob(
            id=job_id,
            project_id=payload.project_id,
            dataset_id=payload.dataset_id,
            user_id=user.id,
            status=JobStatus.RUNNING,
            target_column=payload.target_column,
            task_type=task_type_enum,
            started_at=datetime.now(UTC),
        )
        self.db.add(job)
        await self.db.commit()

        try:
            # 2. Load dataset
            abs_path = storage_backend.get_absolute_path(dataset.storage_path)
            df = DataLoader.load_file(abs_path)

            # 3. Vectorize features & target with zero leakage
            X_train, y_train, X_test, y_test, feature_names = self._prepare_data_from_raw(
                df=df, target_col=payload.target_column, task_type=payload.task_type.lower()
            )

            # 4. Train model & compute evaluation diagnostics
            train_results = ModelTrainer.train_and_evaluate(
                algorithm=payload.algorithm.value,
                hyperparameters=payload.hyperparameters,
                X_train=X_train,
                y_train=y_train,
                X_test=X_test,
                y_test=y_test,
                feature_names=feature_names,
                task_type=payload.task_type.lower(),
                cv_config=payload.cv_config,
            )

            # 5. Serialize Model Artifact
            model_id = uuid.uuid4()
            model_filename = f"{model_id}.pkl"
            artifact_rel_path = os.path.join("data", "models", model_filename).replace("\\", "/")
            artifact_abs_path = os.path.join(self.model_dir, model_filename)

            model_name = (
                payload.model_name
                if payload.model_name
                else f"{payload.algorithm.value}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
            )

            artifact_data = {
                "model_id": str(model_id),
                "job_id": str(job_id),
                "project_id": str(payload.project_id),
                "dataset_id": str(payload.dataset_id),
                "name": model_name,
                "algorithm": payload.algorithm.value,
                "task_type": payload.task_type.lower(),
                "target_column": payload.target_column,
                "feature_names": feature_names,
                "hyperparameters": payload.hyperparameters,
                "model": train_results["model"],
                "train_metrics": train_results["train_metrics"].model_dump(),
                "test_metrics": train_results["test_metrics"].model_dump(),
                "created_at": datetime.now(UTC).isoformat(),
            }

            with open(artifact_abs_path, "wb") as f:
                pickle.dump(artifact_data, f)

            # 6. MLflow Tracking & Artifact Logging
            from app.ml.tracker import mlflow_tracker
            from app.models.experiment import Experiment

            # Ensure default experiment exists for project
            exp_stmt = select(Experiment).where(
                Experiment.project_id == payload.project_id,
                Experiment.name == "Model Training Runs",
            )
            exp_res = await self.db.execute(exp_stmt)
            experiment = exp_res.scalar_one_or_none()

            if not experiment:
                exp_uuid = uuid.uuid4()
                mlflow_exp_id = mlflow_tracker.create_experiment(name=f"{payload.project_id}_Model Training Runs")
                experiment = Experiment(
                    id=exp_uuid,
                    project_id=payload.project_id,
                    dataset_id=payload.dataset_id,
                    name="Model Training Runs",
                    mlflow_experiment_id=mlflow_exp_id,
                    created_at=datetime.now(UTC),
                )
                self.db.add(experiment)
                await self.db.flush()

            mlflow_exp_id = experiment.mlflow_experiment_id or str(experiment.id)
            run_id = mlflow_tracker.start_run(
                experiment_id=mlflow_exp_id,
                run_name=model_name,
                tags={
                    "user_id": str(user.id),
                    "project_id": str(payload.project_id),
                    "dataset_id": str(payload.dataset_id),
                    "algorithm": payload.algorithm.value,
                    "task_type": payload.task_type.lower(),
                },
            )

            # Log parameters & metrics to MLflow run
            log_params = dict(payload.hyperparameters)
            log_params.update(
                {
                    "algorithm": payload.algorithm.value,
                    "target_column": payload.target_column,
                    "task_type": payload.task_type.lower(),
                }
            )
            mlflow_tracker.log_params(run_id, log_params)

            metrics_to_log = {k: v for k, v in train_results["test_metrics"].model_dump().items() if v is not None}
            if train_results["cv_summary"]:
                metrics_to_log["cv_mean_score"] = train_results["cv_summary"].mean_val_score
                metrics_to_log["cv_std_score"] = train_results["cv_summary"].std_val_score
            mlflow_tracker.log_metrics(run_id, metrics_to_log)

            # Log artifacts to MLflow run
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

            # 7. Create TrainedModel record
            metrics_payload = {
                "train": train_results["train_metrics"].model_dump(),
                "test": train_results["test_metrics"].model_dump(),
                "cv": train_results["cv_summary"].model_dump() if train_results["cv_summary"] else None,
                "duration_ms": train_results["duration_ms"],
            }

            trained_model = TrainedModel(
                id=model_id,
                project_id=payload.project_id,
                dataset_id=payload.dataset_id,
                experiment_id=experiment.id,
                mlflow_run_id=run_id,
                name=model_name,
                version="v1.0.0",
                task_type=payload.task_type.lower(),
                framework="custom-numpy-engine",
                metrics=metrics_payload,
                artifact_path=artifact_rel_path,
                status=ModelStatus.DEVELOPMENT,
                created_at=datetime.now(UTC),
            )
            self.db.add(trained_model)

            # 7. Update TrainingJob status
            job.status = JobStatus.SUCCESS
            job.completed_at = datetime.now(UTC)
            await self.db.commit()

            # 8. Audit logging
            await self._log_audit_event(
                action="TRAIN_MODEL",
                user_id=user.id,
                resource_id=str(job_id),
                metadata={
                    "model_id": str(model_id),
                    "algorithm": payload.algorithm.value,
                    "metrics": train_results["test_metrics"].model_dump(),
                },
            )

            # 9. User Notification
            notif = Notification(
                id=uuid.uuid4(),
                user_id=user.id,
                title=f"Training Completed: {payload.model_name or payload.algorithm.value}",
                message=f"Model training succeeded with {payload.algorithm.value} algorithm. Task: {payload.task_type}.",
                type=NotificationType.SUCCESS,
                category=NotificationCategory.TRAINING,
                link=f"/models/{model_id}",
                is_read=False,
                created_at=datetime.now(UTC),
            )
            self.db.add(notif)
            await self.db.commit()

            return TrainingJobDetailResponse(
                id=job_id,
                project_id=payload.project_id,
                dataset_id=payload.dataset_id,
                model_id=model_id,
                status=JobStatus.SUCCESS.value,
                algorithm=payload.algorithm.value,
                task_type=payload.task_type.lower(),
                target_column=payload.target_column,
                hyperparameters=payload.hyperparameters,
                train_metrics=train_results["train_metrics"],
                test_metrics=train_results["test_metrics"],
                cv_summary=train_results["cv_summary"],
                feature_importances=train_results["feature_importances"],
                confusion_matrix=train_results["confusion_matrix"],
                roc_curve=train_results["roc_curve"],
                residuals_sample=train_results["residuals_sample"],
                training_duration_ms=train_results["duration_ms"],
                artifact_path=artifact_rel_path,
                created_at=job.created_at.isoformat(),
            )

        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now(UTC)
            await self.db.commit()
            raise e

    async def start_async_training(self, payload: TrainingJobCreate, user: User) -> Dict[str, Any]:
        """Queue training task into Celery with strict parameter serialization."""
        await self._verify_project_access(payload.project_id, user)
        dataset = await self._get_authorized_dataset(payload.dataset_id, user)

        job_id = uuid.uuid4()
        task_type_enum = (
            TaskType.CLASSIFICATION if payload.task_type.lower() == "classification" else TaskType.REGRESSION
        )

        job = TrainingJob(
            id=job_id,
            project_id=payload.project_id,
            dataset_id=payload.dataset_id,
            user_id=user.id,
            status=JobStatus.PENDING,
            target_column=payload.target_column,
            task_type=task_type_enum,
            created_at=datetime.now(UTC),
        )
        self.db.add(job)
        await self.db.commit()

        # Enqueue Celery Task with serializable arguments only
        from app.tasks.training_tasks import train_model_async_task

        cv_dict = payload.cv_config.model_dump() if payload.cv_config else None
        celery_task = train_model_async_task.delay(
            job_id_str=str(job_id),
            project_id_str=str(payload.project_id),
            dataset_id_str=str(payload.dataset_id),
            user_id_str=str(user.id),
            target_column=payload.target_column,
            task_type=payload.task_type.lower(),
            algorithm=payload.algorithm.value,
            hyperparameters=payload.hyperparameters,
            model_name=payload.model_name,
            cv_config_dict=cv_dict,
        )

        job.celery_task_id = celery_task.id
        await self.db.commit()

        await self._log_audit_event(
            action="ASYNC_TRAIN_MODEL_QUEUED",
            user_id=user.id,
            resource_id=str(job_id),
            metadata={
                "celery_task_id": celery_task.id,
                "algorithm": payload.algorithm.value,
                "task_type": payload.task_type.lower(),
            },
        )

        return {
            "job_id": str(job_id),
            "celery_task_id": celery_task.id,
            "status": JobStatus.PENDING.value,
            "message": "Training job queued for asynchronous worker execution",
        }

    async def get_job_status(self, job_id: uuid.UUID, user: User) -> Dict[str, Any]:
        """Fetch real-time status, execution metrics, and associated model artifact for a training job."""
        stmt = (
            select(TrainingJob)
            .options(selectinload(TrainingJob.project), selectinload(TrainingJob.dataset))
            .where(TrainingJob.id == job_id)
        )
        result = await self.db.execute(stmt)
        job = result.scalar_one_or_none()

        if not job:
            raise NotFoundException(f"TrainingJob with ID '{job_id}' not found")

        if user.role != UserRole.ADMIN and job.user_id != user.id and job.project.owner_id != user.id:
            raise AuthorizationException("You do not have permission to view this job")

        # Query for associated trained model if completed
        model_id = None
        metrics = None
        artifact_path = None

        if job.status == JobStatus.SUCCESS:
            model_stmt = (
                select(TrainedModel)
                .where(TrainedModel.project_id == job.project_id)
                .order_by(desc(TrainedModel.created_at))
            )
            model_res = await self.db.execute(model_stmt)
            models = model_res.scalars().all()
            for m in models:
                if job.started_at and m.created_at >= job.started_at:
                    model_id = str(m.id)
                    metrics = m.metrics
                    artifact_path = m.artifact_path
                    break

        return {
            "id": str(job.id),
            "project_id": str(job.project_id),
            "project_name": job.project.name if job.project else "",
            "dataset_id": str(job.dataset_id),
            "dataset_name": job.dataset.filename if job.dataset else "",
            "user_id": str(job.user_id),
            "status": job.status.value,
            "target_column": job.target_column,
            "task_type": job.task_type.value,
            "celery_task_id": job.celery_task_id,
            "error_message": job.error_message,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "created_at": job.created_at.isoformat(),
            "model_id": model_id,
            "metrics": metrics,
            "artifact_path": artifact_path,
        }

    async def list_training_jobs(self, project_id: uuid.UUID | None, user: User) -> List[Dict[str, Any]]:
        """List training jobs filtered by project or accessible by user."""
        stmt = (
            select(TrainingJob)
            .options(selectinload(TrainingJob.project), selectinload(TrainingJob.dataset))
            .order_by(desc(TrainingJob.created_at))
        )
        if project_id:
            await self._verify_project_access(project_id, user)
            stmt = stmt.where(TrainingJob.project_id == project_id)
        elif user.role != UserRole.ADMIN:
            stmt = stmt.where(TrainingJob.user_id == user.id)

        result = await self.db.execute(stmt)
        jobs = result.scalars().all()

        return [
            {
                "id": str(j.id),
                "project_id": str(j.project_id),
                "project_name": j.project.name if j.project else "",
                "dataset_id": str(j.dataset_id),
                "dataset_name": j.dataset.filename if j.dataset else "",
                "target_column": j.target_column,
                "task_type": j.task_type.value,
                "status": j.status.value,
                "error_message": j.error_message,
                "started_at": j.started_at.isoformat() if j.started_at else None,
                "completed_at": j.completed_at.isoformat() if j.completed_at else None,
                "created_at": j.created_at.isoformat(),
            }
            for j in jobs
        ]
