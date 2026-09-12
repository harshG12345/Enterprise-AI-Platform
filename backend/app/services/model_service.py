"""Service layer for Model Registry, Version Governance, Promotion Lifecycle, Leaderboards, and Comparisons."""

import os
import pickle
import uuid
from typing import Any, Dict, List

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config.settings import get_settings
from app.core.exceptions import AuthorizationException, NotFoundException
from app.models.audit_log import AuditLog
from app.models.project import Project
from app.models.trained_model import ModelStatus, TrainedModel
from app.models.user import User, UserRole
from app.schemas.model import (
    AuditHistoryItem,
    ModelComparisonResponse,
    ModelDetailResponse,
    ModelLeaderboardItem,
    ModelPromotionRequest,
    ModelResponse,
)

settings = get_settings()


class ModelService:
    """Orchestrates model registry exploration, lifecycle state transitions, and audit governance."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.model_dir = settings.MODEL_DIR

    async def _verify_project_access(self, project_id: uuid.UUID, user: User) -> Project:
        """Verify project exists and user has authorization."""
        stmt = select(Project).where(Project.id == project_id)
        result = await self.db.execute(stmt)
        project = result.scalar_one_or_none()
        if not project:
            raise NotFoundException(f"Project with ID '{project_id}' not found")
        if user.role != UserRole.ADMIN and project.owner_id != user.id:
            raise AuthorizationException("You do not have permission to access models in this project")
        return project

    async def _get_authorized_model(self, model_id: uuid.UUID, user: User) -> TrainedModel:
        """Fetch model with loaded relationships and verify authorization."""
        stmt = (
            select(TrainedModel)
            .options(
                selectinload(TrainedModel.project),
                selectinload(TrainedModel.dataset),
                selectinload(TrainedModel.experiment),
            )
            .where(TrainedModel.id == model_id)
        )
        result = await self.db.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            raise NotFoundException(f"Model with ID '{model_id}' not found")
        if user.role != UserRole.ADMIN and model.project.owner_id != user.id:
            raise AuthorizationException("You do not have permission to access this model")
        return model

    async def _log_audit_event(
        self,
        action: str,
        user_id: uuid.UUID,
        resource_id: str,
        metadata: dict | None = None,
    ) -> None:
        """Create audit log record."""
        audit = AuditLog(
            id=uuid.uuid4(),
            user_id=user_id,
            action=action,
            resource_type="MODEL",
            resource_id=resource_id,
            metadata_json=metadata or {},
        )
        self.db.add(audit)
        await self.db.commit()

    def _read_artifact_metadata(self, model: TrainedModel) -> Dict[str, Any]:
        """Safely load serializable artifact metadata from local disk if present."""
        filename = f"{model.id}.pkl"
        artifact_path = os.path.join(self.model_dir, filename)
        if not os.path.exists(artifact_path):
            return {}
        try:
            with open(artifact_path, "rb") as f:
                data = pickle.load(f)
            if isinstance(data, dict):
                return {
                    "algorithm": data.get("algorithm"),
                    "target_column": data.get("target_column"),
                    "feature_names": data.get("feature_names", []),
                    "hyperparameters": data.get("hyperparameters", {}),
                    "confusion_matrix": data.get("confusion_matrix"),
                    "feature_importances": data.get("feature_importances", []),
                }
        except Exception:
            pass
        return {}

    async def list_models(
        self,
        project_id: uuid.UUID | None,
        task_type: str | None,
        status_filter: str | None,
        user: User,
    ) -> List[ModelResponse]:
        """List registered models with filters."""
        stmt = (
            select(TrainedModel)
            .options(selectinload(TrainedModel.project), selectinload(TrainedModel.dataset))
            .order_by(desc(TrainedModel.created_at))
        )

        if project_id:
            await self._verify_project_access(project_id, user)
            stmt = stmt.where(TrainedModel.project_id == project_id)
        elif user.role != UserRole.ADMIN:
            stmt = stmt.join(Project).where(Project.owner_id == user.id)

        if task_type:
            stmt = stmt.where(TrainedModel.task_type == task_type.lower())

        if status_filter:
            try:
                enum_status = ModelStatus[status_filter.upper()]
                stmt = stmt.where(TrainedModel.status == enum_status)
            except KeyError:
                pass

        result = await self.db.execute(stmt)
        models = result.scalars().all()

        return [
            ModelResponse(
                id=m.id,
                project_id=m.project_id,
                project_name=m.project.name if m.project else None,
                dataset_id=m.dataset_id,
                dataset_name=m.dataset.filename if m.dataset else None,
                experiment_id=m.experiment_id,
                name=m.name,
                version=m.version,
                task_type=m.task_type,
                framework=m.framework,
                metrics=m.metrics,
                artifact_path=m.artifact_path,
                mlflow_run_id=m.mlflow_run_id,
                status=m.status.value,
                created_at=m.created_at.isoformat(),
            )
            for m in models
        ]

    async def get_model_details(self, model_id: uuid.UUID, user: User) -> ModelDetailResponse:
        """Retrieve complete diagnostic details, metadata, and audit logs for a model."""
        model = await self._get_authorized_model(model_id, user)
        artifact_meta = self._read_artifact_metadata(model)

        # Retrieve audit history for this model
        audit_stmt = (
            select(AuditLog)
            .where(AuditLog.resource_type == "MODEL", AuditLog.resource_id == str(model_id))
            .order_by(desc(AuditLog.created_at))
        )
        audit_res = await self.db.execute(audit_stmt)
        audit_logs = audit_res.scalars().all()

        audit_history = [
            AuditHistoryItem(
                id=a.id,
                action=a.action,
                user_id=a.user_id,
                metadata=a.metadata_json or {},
                created_at=a.created_at.isoformat(),
            )
            for a in audit_logs
        ]

        return ModelDetailResponse(
            id=model.id,
            project_id=model.project_id,
            project_name=model.project.name if model.project else None,
            dataset_id=model.dataset_id,
            dataset_name=model.dataset.filename if model.dataset else None,
            experiment_id=model.experiment_id,
            name=model.name,
            version=model.version,
            task_type=model.task_type,
            framework=model.framework,
            status=model.status.value,
            metrics=model.metrics,
            artifact_path=model.artifact_path,
            mlflow_run_id=model.mlflow_run_id,
            algorithm=artifact_meta.get("algorithm"),
            target_column=artifact_meta.get("target_column"),
            feature_names=artifact_meta.get("feature_names", []),
            hyperparameters=artifact_meta.get("hyperparameters", {}),
            confusion_matrix=artifact_meta.get("confusion_matrix"),
            feature_importances=artifact_meta.get("feature_importances", []),
            audit_history=audit_history,
            created_at=model.created_at.isoformat(),
        )

    async def promote_model(self, model_id: uuid.UUID, payload: ModelPromotionRequest, user: User) -> ModelResponse:
        """Promote model lifecycle stage with RBAC enforcement and audit governance."""
        # Enforce RBAC: only Admin and Data Scientist roles can promote models
        if user.role not in (UserRole.ADMIN, UserRole.DATA_SCIENTIST):
            raise AuthorizationException("Only Data Scientists and Admins are authorized to promote model stages")

        model = await self._get_authorized_model(model_id, user)
        old_status = model.status.value
        target_status = payload.status

        # If promoting to PRODUCTION, ensure previous production model in same project/task is demoted to STAGING
        if target_status == ModelStatus.PRODUCTION:
            demote_stmt = select(TrainedModel).where(
                TrainedModel.project_id == model.project_id,
                TrainedModel.task_type == model.task_type,
                TrainedModel.status == ModelStatus.PRODUCTION,
                TrainedModel.id != model.id,
            )
            demote_res = await self.db.execute(demote_stmt)
            existing_prod_models = demote_res.scalars().all()
            for prod_m in existing_prod_models:
                prod_m.status = ModelStatus.STAGING
                await self._log_audit_event(
                    action="MODEL_STAGE_DEMOTE",
                    user_id=user.id,
                    resource_id=str(prod_m.id),
                    metadata={
                        "reason": "Demoted from PRODUCTION to STAGING by new promotion",
                        "new_prod_model_id": str(model.id),
                    },
                )

        model.status = target_status
        await self.db.commit()

        action_name = (
            f"MODEL_PROMOTE_{target_status.value}"
            if target_status in (ModelStatus.PRODUCTION, ModelStatus.STAGING)
            else "MODEL_STAGE_CHANGE"
        )
        await self._log_audit_event(
            action=action_name,
            user_id=user.id,
            resource_id=str(model.id),
            metadata={
                "previous_status": old_status,
                "new_status": target_status.value,
                "notes": payload.notes,
                "promoted_by": user.email,
            },
        )

        return ModelResponse(
            id=model.id,
            project_id=model.project_id,
            project_name=model.project.name if model.project else None,
            dataset_id=model.dataset_id,
            dataset_name=model.dataset.filename if model.dataset else None,
            experiment_id=model.experiment_id,
            name=model.name,
            version=model.version,
            task_type=model.task_type,
            framework=model.framework,
            metrics=model.metrics,
            artifact_path=model.artifact_path,
            mlflow_run_id=model.mlflow_run_id,
            status=model.status.value,
            created_at=model.created_at.isoformat(),
        )

    async def archive_model(self, model_id: uuid.UUID, user: User) -> ModelResponse:
        """Archive a model version."""
        if user.role not in (UserRole.ADMIN, UserRole.DATA_SCIENTIST):
            raise AuthorizationException("Only Data Scientists and Admins can archive models")

        model = await self._get_authorized_model(model_id, user)
        model.status = ModelStatus.ARCHIVED
        await self.db.commit()

        await self._log_audit_event(
            action="MODEL_ARCHIVE",
            user_id=user.id,
            resource_id=str(model.id),
            metadata={"archived_by": user.email},
        )

        return ModelResponse(
            id=model.id,
            project_id=model.project_id,
            project_name=model.project.name if model.project else None,
            dataset_id=model.dataset_id,
            dataset_name=model.dataset.filename if model.dataset else None,
            experiment_id=model.experiment_id,
            name=model.name,
            version=model.version,
            task_type=model.task_type,
            framework=model.framework,
            metrics=model.metrics,
            artifact_path=model.artifact_path,
            mlflow_run_id=model.mlflow_run_id,
            status=model.status.value,
            created_at=model.created_at.isoformat(),
        )

    async def rollback_model(self, model_id: uuid.UUID, user: User) -> ModelResponse:
        """Rollback a model stage to DEVELOPMENT."""
        if user.role not in (UserRole.ADMIN, UserRole.DATA_SCIENTIST):
            raise AuthorizationException("Only Data Scientists and Admins can rollback models")

        model = await self._get_authorized_model(model_id, user)
        model.status = ModelStatus.DEVELOPMENT
        await self.db.commit()

        await self._log_audit_event(
            action="MODEL_ROLLBACK",
            user_id=user.id,
            resource_id=str(model.id),
            metadata={"rolled_back_to": "DEVELOPMENT", "user": user.email},
        )

        return ModelResponse(
            id=model.id,
            project_id=model.project_id,
            project_name=model.project.name if model.project else None,
            dataset_id=model.dataset_id,
            dataset_name=model.dataset.filename if model.dataset else None,
            experiment_id=model.experiment_id,
            name=model.name,
            version=model.version,
            task_type=model.task_type,
            framework=model.framework,
            metrics=model.metrics,
            artifact_path=model.artifact_path,
            mlflow_run_id=model.mlflow_run_id,
            status=model.status.value,
            created_at=model.created_at.isoformat(),
        )

    async def get_leaderboard(
        self, project_id: uuid.UUID | None, task_type: str | None, user: User
    ) -> List[ModelLeaderboardItem]:
        """Rank models by primary generalization performance score."""
        stmt = (
            select(TrainedModel)
            .options(selectinload(TrainedModel.project))
            .where(TrainedModel.status != ModelStatus.ARCHIVED)
        )

        if project_id:
            await self._verify_project_access(project_id, user)
            stmt = stmt.where(TrainedModel.project_id == project_id)
        elif user.role != UserRole.ADMIN:
            stmt = stmt.join(Project).where(Project.owner_id == user.id)

        if task_type:
            stmt = stmt.where(TrainedModel.task_type == task_type.lower())

        result = await self.db.execute(stmt)
        models = result.scalars().all()

        items = []
        for m in models:
            test_metrics = (m.metrics or {}).get("test", {})
            duration_ms = (m.metrics or {}).get("duration_ms")

            if m.task_type == "classification":
                primary_name = "accuracy"
                primary_val = float(test_metrics.get("accuracy", 0.0))
                sec_name = "f1_score"
                sec_val = float(test_metrics.get("f1_score", 0.0)) if test_metrics.get("f1_score") is not None else None
            else:
                primary_name = "r2_score"
                primary_val = float(test_metrics.get("r2_score", 0.0))
                sec_name = "rmse"
                sec_val = float(test_metrics.get("rmse", 0.0)) if test_metrics.get("rmse") is not None else None

            items.append(
                ModelLeaderboardItem(
                    rank=1,
                    id=m.id,
                    name=m.name,
                    version=m.version,
                    status=m.status.value,
                    task_type=m.task_type,
                    primary_metric_name=primary_name,
                    primary_metric_value=round(primary_val, 4),
                    secondary_metric_name=sec_name,
                    secondary_metric_value=round(sec_val, 4) if sec_val is not None else None,
                    training_duration_ms=duration_ms,
                    created_at=m.created_at.isoformat(),
                )
            )

        # Sort descending by primary metric value
        items.sort(key=lambda x: x.primary_metric_value, reverse=True)
        for idx, it in enumerate(items, start=1):
            it.rank = idx

        return items

    async def compare_models(self, model_ids: List[uuid.UUID], user: User) -> ModelComparisonResponse:
        """Compare multiple registered models side-by-side."""
        details_list = []
        all_metrics_set = set()
        all_hyperparams_set = set()
        hyperparam_dicts = []

        for mid in model_ids:
            try:
                detail = await self.get_model_details(mid, user)
                details_list.append(detail)
                hyperparam_dicts.append(detail.hyperparameters)
                all_hyperparams_set.update(detail.hyperparameters.keys())
                if detail.metrics and "test" in detail.metrics:
                    all_metrics_set.update(detail.metrics["test"].keys())
            except Exception:
                continue

        if not details_list:
            raise NotFoundException("No valid models found for comparison")

        # Metric comparison matrix: metric -> {model_id -> value}
        sorted_metrics = sorted(list(all_metrics_set))
        metric_matrix: Dict[str, Dict[str, float | None]] = {}

        for m in sorted_metrics:
            metric_matrix[m] = {}
            for d in details_list:
                val = d.metrics.get("test", {}).get(m) if d.metrics else None
                metric_matrix[m][str(d.id)] = round(float(val), 4) if val is not None else None

        # Hyperparameter differences
        common_hyperparams = {}
        differing_hyperparams = []

        for k in all_hyperparams_set:
            vals = [p.get(k) for p in hyperparam_dicts]
            if all(v == vals[0] for v in vals) and vals[0] is not None:
                common_hyperparams[k] = vals[0]
            else:
                differing_hyperparams.append(k)

        return ModelComparisonResponse(
            models=details_list,
            all_metrics=sorted_metrics,
            metric_matrix=metric_matrix,
            differing_hyperparameters=differing_hyperparams,
            common_hyperparameters=common_hyperparams,
        )

    async def get_model_artifact_path(self, model_id: uuid.UUID, user: User) -> str:
        """Verify access and return absolute artifact path for download."""
        model = await self._get_authorized_model(model_id, user)
        filename = f"{model.id}.pkl"
        abs_path = os.path.join(self.model_dir, filename)
        if not os.path.exists(abs_path):
            raise NotFoundException("Model artifact binary file not found on storage")
        return abs_path
