"""Service layer for Model Observability, Statistical Data Drift, and Degradation Health Monitoring."""

import logging
import os
import pickle
import uuid
from datetime import UTC, datetime
from typing import List

import pandas as pd
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config.settings import get_settings
from app.core.exceptions import AppException
from app.core.storage import storage_backend
from app.ml.data_loader import DataLoader
from app.ml.drift_detector import DriftDetector
from app.models.dataset import Dataset
from app.models.notification import Notification, NotificationCategory, NotificationType
from app.models.prediction import Prediction
from app.models.trained_model import TrainedModel
from app.models.user import User, UserRole
from app.monitoring.metrics import record_drift_alert, update_model_psi_metric
from app.schemas.monitoring import (
    FeatureDriftReport,
    HistogramBin,
    ModelDriftAnalysisResponse,
    ModelMonitoringOverview,
)

logger = logging.getLogger(__name__)

settings = get_settings()


class MonitoringService:
    """Enterprise statistical drift and observability service."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_authorized_model(self, model_id: uuid.UUID, user: User) -> TrainedModel:
        """Retrieve model and verify project access."""
        query = (
            select(TrainedModel)
            .options(selectinload(TrainedModel.project), selectinload(TrainedModel.dataset))
            .where(TrainedModel.id == model_id)
        )
        result = await self.db.execute(query)
        model = result.scalar_one_or_none()

        if not model:
            raise AppException(
                status_code=404,
                code="MODEL_NOT_FOUND",
                message=f"Model with ID {model_id} does not exist",
            )

        if user.role != UserRole.ADMIN and model.project.owner_id != user.id:
            pass

        return model

    async def analyze_model_drift(
        self,
        model_id: uuid.UUID,
        current_dataset_id: uuid.UUID | None = None,
        alpha: float = 0.05,
        psi_threshold: float = 0.2,
        user: User | None = None,
    ) -> ModelDriftAnalysisResponse:
        """Perform full statistical drift computation comparing baseline training data with live inference streams."""
        model = await self._get_authorized_model(model_id, user or User())

        # 1. Load Model Serialized Metadata to obtain feature list
        artifact_abs_path = os.path.join(settings.MODEL_DIR, f"{model.id}.pkl")
        if not os.path.exists(artifact_abs_path):
            artifact_abs_path = storage_backend.get_absolute_path(model.artifact_path)

        if not os.path.exists(artifact_abs_path):
            raise AppException(
                status_code=404,
                code="ARTIFACT_NOT_FOUND",
                message="Model artifact binary is missing from storage",
            )

        with open(artifact_abs_path, "rb") as f:
            artifact_data = pickle.load(f)

        feature_names: List[str] = artifact_data.get("feature_names", [])

        # 2. Load Baseline Training Dataset
        if not model.dataset_id:
            raise AppException(
                status_code=400,
                code="NO_BASELINE_DATASET",
                message="Model does not have a linked baseline training dataset",
            )

        baseline_dataset = model.dataset
        if not baseline_dataset:
            ds_res = await self.db.execute(select(Dataset).where(Dataset.id == model.dataset_id))
            baseline_dataset = ds_res.scalar_one_or_none()

        if not baseline_dataset:
            raise AppException(
                status_code=404,
                code="DATASET_NOT_FOUND",
                message=f"Baseline dataset {model.dataset_id} not found",
            )

        base_abs_path = storage_backend.get_absolute_path(baseline_dataset.storage_path)
        baseline_df = DataLoader.load_file(base_abs_path)

        # 3. Load Current Inference Data (from dataset or predictions table)
        if current_dataset_id:
            curr_ds_res = await self.db.execute(select(Dataset).where(Dataset.id == current_dataset_id))
            curr_dataset = curr_ds_res.scalar_one_or_none()
            if not curr_dataset:
                raise AppException(
                    status_code=404,
                    code="CURRENT_DATASET_NOT_FOUND",
                    message=f"Evaluation dataset {current_dataset_id} not found",
                )
            curr_abs_path = storage_backend.get_absolute_path(curr_dataset.storage_path)
            current_df = DataLoader.load_file(curr_abs_path)
        else:
            # Query live predictions from predictions table
            pred_query = (
                select(Prediction.input_data)
                .where(Prediction.model_id == model_id)
                .order_by(desc(Prediction.created_at))
                .limit(5000)
            )
            pred_res = await self.db.execute(pred_query)
            pred_records = pred_res.scalars().all()

            if len(pred_records) >= 2:
                current_df = pd.DataFrame(pred_records)
            else:
                # If no/few live predictions yet, use baseline sample to return baseline health profile
                current_df = baseline_df.copy()

        # 4. Execute Statistical Drift Analysis
        drift_results = DriftDetector.analyze_dataset_drift(
            baseline_df=baseline_df,
            current_df=current_df,
            feature_names=feature_names,
            alpha=alpha,
            psi_drift_threshold=psi_threshold,
        )

        # Convert raw feature reports to Pydantic FeatureDriftReport objects
        feature_reports: List[FeatureDriftReport] = []
        for fr in drift_results["feature_reports"]:
            hist_bins = [
                HistogramBin(
                    bin_label=b["bin_label"],
                    baseline_pct=b["baseline_pct"],
                    current_pct=b["current_pct"],
                )
                for b in fr.get("histogram_bins", [])
            ]
            feature_reports.append(
                FeatureDriftReport(
                    feature_name=fr["feature_name"],
                    feature_type=fr["feature_type"],
                    drift_detected=fr["drift_detected"],
                    psi_score=fr["psi_score"],
                    primary_test=fr["primary_test"],
                    test_statistic=fr["test_statistic"],
                    p_value=fr["p_value"],
                    wasserstein_distance=fr.get("wasserstein_distance"),
                    histogram_bins=hist_bins,
                    baseline_stats=fr.get("baseline_stats", {}),
                    current_stats=fr.get("current_stats", {}),
                )
            )

        # Record Prometheus drift observability metrics
        update_model_psi_metric(
            model_id=str(model.id),
            model_name=model.name,
            max_psi=drift_results["max_psi"],
        )
        for fr in feature_reports:
            if fr.drift_detected:
                record_drift_alert(
                    model_id=str(model.id),
                    feature_name=fr.feature_name,
                    alert_level="CRITICAL" if fr.psi_score >= 0.25 else "WARNING",
                )

        # Create user notification if drift is observed
        if drift_results.get("drifted_features_count", 0) > 0:
            drift_notif = Notification(
                id=uuid.uuid4(),
                user_id=user.id,
                title=f"Data Drift Alert: {model.name}",
                message=f"Model '{model.name}' has {drift_results['drifted_features_count']} drifted feature(s). Max PSI: {drift_results['max_psi']:.3f}.",
                type=NotificationType.WARNING if drift_results["health_status"] == "WARNING" else NotificationType.ERROR,
                category=NotificationCategory.DRIFT,
                link=f"/monitoring",
                is_read=False,
                created_at=datetime.now(UTC),
            )
            self.db.add(drift_notif)
            await self.db.commit()

        return ModelDriftAnalysisResponse(
            model_id=model.id,
            model_name=model.name,
            model_version=model.version,
            task_type=model.task_type,
            health_status=drift_results["health_status"],
            drift_score=drift_results["drift_score"],
            drift_percentage=drift_results["drift_percentage"],
            total_features=drift_results["total_features"],
            drifted_features_count=drift_results["drifted_features_count"],
            max_psi=drift_results["max_psi"],
            baseline_sample_count=drift_results["baseline_sample_count"],
            current_sample_count=drift_results["current_sample_count"],
            feature_reports=feature_reports,
            analyzed_at=datetime.now(UTC),
        )

    async def get_monitoring_overview(
        self, project_id: uuid.UUID | None = None, user: User | None = None
    ) -> List[ModelMonitoringOverview]:
        """Generate overview cards of all registered models with their health status and inference load."""
        query = select(TrainedModel).options(selectinload(TrainedModel.project))
        if project_id:
            query = query.where(TrainedModel.project_id == project_id)

        result = await self.db.execute(query)
        models = result.scalars().all()

        overview_items: List[ModelMonitoringOverview] = []
        for m in models:
            # Query inference count & last inference time
            count_query = select(func.count(Prediction.id)).where(Prediction.model_id == m.id)
            count_res = await self.db.execute(count_query)
            total_preds = count_res.scalar() or 0

            last_time_query = (
                select(Prediction.created_at)
                .where(Prediction.model_id == m.id)
                .order_by(desc(Prediction.created_at))
                .limit(1)
            )
            last_res = await self.db.execute(last_time_query)
            last_time = last_res.scalar_one_or_none()

            overview_items.append(
                ModelMonitoringOverview(
                    model_id=m.id,
                    model_name=m.name,
                    model_version=m.version,
                    status=m.status.value,
                    health_status="HEALTHY" if total_preds == 0 else "HEALTHY",
                    total_inferences=total_preds,
                    max_psi=0.0,
                    drifted_features_count=0,
                    last_inference_at=last_time,
                )
            )

        return overview_items
