"""Service layer for MLflow Experiment Tracking, Run Management, and Run Comparisons."""

import uuid
from datetime import UTC, datetime
from typing import Any, Dict, List

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AuthorizationException, NotFoundException, ValidationException
from app.ml.tracker import mlflow_tracker
from app.models.audit_log import AuditLog
from app.models.experiment import Experiment
from app.models.project import Project
from app.models.user import User, UserRole
from app.schemas.experiment import (
    ArtifactItem,
    ExperimentCreate,
    ExperimentResponse,
    MetricHistoryItem,
    RunComparisonItem,
    RunComparisonResponse,
    RunCreate,
    RunDetailResponse,
)


class ExperimentService:
    """Orchestrates MLflow experiments, run lifecycles, and run comparison matrices."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.tracker = mlflow_tracker

    async def _verify_project_access(self, project_id: uuid.UUID, user: User) -> Project:
        """Verify project exists and user has authorization."""
        stmt = select(Project).where(Project.id == project_id)
        result = await self.db.execute(stmt)
        project = result.scalar_one_or_none()
        if not project:
            raise NotFoundException(f"Project with ID '{project_id}' not found")
        if user.role != UserRole.ADMIN and project.owner_id != user.id:
            raise AuthorizationException("You do not have permission to access experiments in this project")
        return project

    async def _get_authorized_experiment(self, experiment_id: uuid.UUID, user: User) -> Experiment:
        """Fetch experiment and assert authorization."""
        stmt = select(Experiment).options(selectinload(Experiment.project)).where(Experiment.id == experiment_id)
        result = await self.db.execute(stmt)
        exp = result.scalar_one_or_none()
        if not exp:
            raise NotFoundException(f"Experiment with ID '{experiment_id}' not found")
        if user.role != UserRole.ADMIN and exp.project.owner_id != user.id:
            raise AuthorizationException("You do not have permission to access this experiment")
        return exp

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
            resource_type="EXPERIMENT",
            resource_id=resource_id,
            metadata_json=metadata or {},
        )
        self.db.add(audit)
        await self.db.commit()

    async def create_experiment(self, payload: ExperimentCreate, user: User) -> ExperimentResponse:
        """Create experiment in database and initialize MLflow tracking workspace."""
        await self._verify_project_access(payload.project_id, user)

        # Check duplicate name in same project
        stmt = select(Experiment).where(
            Experiment.project_id == payload.project_id,
            Experiment.name == payload.name,
        )
        existing = (await self.db.execute(stmt)).scalar_one_or_none()
        if existing:
            raise ValidationException(f"Experiment with name '{payload.name}' already exists in this project")

        exp_id = uuid.uuid4()
        mlflow_exp_id = self.tracker.create_experiment(
            name=f"{payload.project_id}_{payload.name}",
            tags=payload.tags,
        )

        experiment = Experiment(
            id=exp_id,
            project_id=payload.project_id,
            dataset_id=payload.dataset_id,
            name=payload.name,
            mlflow_experiment_id=mlflow_exp_id,
            created_at=datetime.now(UTC),
        )
        self.db.add(experiment)
        await self.db.commit()

        await self._log_audit_event(
            action="CREATE_EXPERIMENT",
            user_id=user.id,
            resource_id=str(exp_id),
            metadata={"name": payload.name, "mlflow_id": mlflow_exp_id},
        )

        return ExperimentResponse(
            id=exp_id,
            project_id=payload.project_id,
            dataset_id=payload.dataset_id,
            name=payload.name,
            mlflow_experiment_id=mlflow_exp_id,
            run_count=0,
            created_at=experiment.created_at.isoformat(),
        )

    async def list_experiments(self, project_id: uuid.UUID | None, user: User) -> List[ExperimentResponse]:
        """List experiments filtered by project."""
        stmt = select(Experiment).options(selectinload(Experiment.project)).order_by(desc(Experiment.created_at))
        if project_id:
            await self._verify_project_access(project_id, user)
            stmt = stmt.where(Experiment.project_id == project_id)
        elif user.role != UserRole.ADMIN:
            stmt = stmt.join(Project).where(Project.owner_id == user.id)

        result = await self.db.execute(stmt)
        experiments = result.scalars().all()

        responses = []
        for exp in experiments:
            run_count = 0
            if exp.mlflow_experiment_id:
                runs = self.tracker.list_runs(exp.mlflow_experiment_id)
                run_count = len(runs)
            responses.append(
                ExperimentResponse(
                    id=exp.id,
                    project_id=exp.project_id,
                    dataset_id=exp.dataset_id,
                    name=exp.name,
                    mlflow_experiment_id=exp.mlflow_experiment_id,
                    run_count=run_count,
                    created_at=exp.created_at.isoformat(),
                )
            )
        return responses

    async def get_experiment(self, experiment_id: uuid.UUID, user: User) -> ExperimentResponse:
        """Get experiment details."""
        exp = await self._get_authorized_experiment(experiment_id, user)
        run_count = 0
        if exp.mlflow_experiment_id:
            runs = self.tracker.list_runs(exp.mlflow_experiment_id)
            run_count = len(runs)

        return ExperimentResponse(
            id=exp.id,
            project_id=exp.project_id,
            dataset_id=exp.dataset_id,
            name=exp.name,
            mlflow_experiment_id=exp.mlflow_experiment_id,
            run_count=run_count,
            created_at=exp.created_at.isoformat(),
        )

    async def create_run(self, payload: RunCreate, user: User) -> RunDetailResponse:
        """Initialize a new MLflow tracking run."""
        exp = await self._get_authorized_experiment(payload.experiment_id, user)
        mlflow_exp_id = exp.mlflow_experiment_id or str(exp.id)

        run_id = self.tracker.start_run(
            experiment_id=mlflow_exp_id,
            run_name=payload.run_name,
            tags=payload.tags,
        )

        if payload.parameters:
            self.tracker.log_params(run_id, payload.parameters)

        raw_run = self.tracker.get_run(run_id)
        if not raw_run:
            raise NotFoundException("Failed to initialize run")

        return self._format_run_response(raw_run, exp.id)

    async def get_run(self, run_id: str, user: User) -> RunDetailResponse:
        """Get full details of an individual run."""
        raw_run = self.tracker.get_run(run_id)
        if not raw_run:
            raise NotFoundException(f"Run with ID '{run_id}' not found")

        # Verify authorization via experiment
        exp_mlflow_id = raw_run.get("experiment_id")
        stmt = (
            select(Experiment)
            .options(selectinload(Experiment.project))
            .where((Experiment.mlflow_experiment_id == exp_mlflow_id) | (Experiment.id == exp_mlflow_id))
        )
        result = await self.db.execute(stmt)
        exp = result.scalar_one_or_none()

        if exp and user.role != UserRole.ADMIN and exp.project.owner_id != user.id:
            raise AuthorizationException("You do not have permission to view this run")

        exp_uuid = exp.id if exp else uuid.uuid4()
        return self._format_run_response(raw_run, exp_uuid)

    async def list_runs(self, experiment_id: uuid.UUID, user: User) -> List[RunDetailResponse]:
        """List all runs for an experiment."""
        exp = await self._get_authorized_experiment(experiment_id, user)
        mlflow_exp_id = exp.mlflow_experiment_id or str(exp.id)
        raw_runs = self.tracker.list_runs(mlflow_exp_id)

        return [self._format_run_response(r, exp.id) for r in raw_runs]

    async def compare_runs(self, run_ids: List[str], user: User) -> RunComparisonResponse:
        """Compute parameter differences and metric comparison matrix across runs."""
        runs_data: List[RunComparisonItem] = []
        all_param_keys = set()
        all_metric_keys = set()
        param_dicts = []

        for r_id in run_ids:
            raw = self.tracker.get_run(r_id)
            if not raw:
                continue

            # Verify access
            exp_mlflow_id = raw.get("experiment_id")
            stmt = (
                select(Experiment)
                .options(selectinload(Experiment.project))
                .where((Experiment.mlflow_experiment_id == exp_mlflow_id) | (Experiment.id == exp_mlflow_id))
            )
            exp = (await self.db.execute(stmt)).scalar_one_or_none()
            if exp and user.role != UserRole.ADMIN and exp.project.owner_id != user.id:
                continue

            created_str = (
                datetime.fromtimestamp(raw.get("start_time", 0.0), UTC).isoformat()
                if raw.get("start_time")
                else datetime.now(UTC).isoformat()
            )

            item = RunComparisonItem(
                run_id=raw["run_id"],
                run_name=raw.get("run_name", raw["run_id"][:8]),
                status=raw.get("status", "FINISHED"),
                duration_ms=raw.get("duration_ms"),
                parameters=raw.get("parameters", {}),
                metrics=raw.get("metrics", {}),
                tags=raw.get("tags", {}),
                created_at=created_str,
            )
            runs_data.append(item)
            param_dicts.append(raw.get("parameters", {}))
            all_param_keys.update(raw.get("parameters", {}).keys())
            all_metric_keys.update(raw.get("metrics", {}).keys())

        if not runs_data:
            raise NotFoundException("No valid runs found for comparison")

        # Identify common vs differing parameters
        common_parameters = {}
        differing_parameters = []

        for k in all_param_keys:
            vals = [p.get(k) for p in param_dicts]
            if all(v == vals[0] for v in vals) and vals[0] is not None:
                common_parameters[k] = vals[0]
            else:
                differing_parameters.append(k)

        # Build metric comparison matrix: metric -> {run_id -> value}
        metric_matrix: Dict[str, Dict[str, float | None]] = {}
        sorted_metrics = sorted(list(all_metric_keys))

        for m in sorted_metrics:
            metric_matrix[m] = {}
            for r in runs_data:
                metric_matrix[m][r.run_id] = r.metrics.get(m)

        return RunComparisonResponse(
            runs=runs_data,
            common_parameters=common_parameters,
            differing_parameters=differing_parameters,
            all_metrics=sorted_metrics,
            metric_matrix=metric_matrix,
        )

    async def get_metric_history(self, run_id: str, metric_key: str, user: User) -> List[MetricHistoryItem]:
        """Fetch metric curve progression for a run."""
        await self.get_run(run_id, user)
        raw_history = self.tracker.get_metric_history(run_id, metric_key)
        return [
            MetricHistoryItem(
                step=item["step"],
                value=item["value"],
                timestamp=item["timestamp"],
            )
            for item in raw_history
        ]

    async def list_run_artifacts(self, run_id: str, path: str, user: User) -> List[ArtifactItem]:
        """List artifacts for a run."""
        await self.get_run(run_id, user)
        raw_artifacts = self.tracker.list_artifacts(run_id, path)
        return [
            ArtifactItem(
                path=a["path"],
                is_dir=a["is_dir"],
                file_size_bytes=a["file_size_bytes"],
            )
            for a in raw_artifacts
        ]

    def _format_run_response(self, raw: Dict[str, Any], exp_id: uuid.UUID) -> RunDetailResponse:
        """Transform raw tracker dict to typed RunDetailResponse."""
        start_ts = raw.get("start_time")
        end_ts = raw.get("end_time")

        started_str = datetime.fromtimestamp(start_ts, UTC).isoformat() if start_ts else datetime.now(UTC).isoformat()
        end_str = datetime.fromtimestamp(end_ts, UTC).isoformat() if end_ts else None

        artifacts = [
            ArtifactItem(
                path=a["path"],
                is_dir=a["is_dir"],
                file_size_bytes=a["file_size_bytes"],
            )
            for a in raw.get("artifacts", [])
        ]

        return RunDetailResponse(
            run_id=raw["run_id"],
            experiment_id=exp_id,
            run_name=raw.get("run_name", raw["run_id"][:8]),
            status=raw.get("status", "FINISHED"),
            started_at=started_str,
            end_time=end_str,
            duration_ms=raw.get("duration_ms"),
            parameters=raw.get("parameters", {}),
            metrics=raw.get("metrics", {}),
            tags=raw.get("tags", {}),
            artifacts=artifacts,
        )
