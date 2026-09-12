"""Service handling Project workspace lifecycle and access control."""

import math
import uuid
from typing import List, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AuthorizationException, NotFoundException
from app.models.audit_log import AuditLog
from app.models.dataset import Dataset
from app.models.experiment import Experiment
from app.models.project import Project
from app.models.trained_model import TrainedModel
from app.models.user import User, UserRole
from app.schemas.project import ProjectCreate, ProjectDetailResponse, ProjectResponse, ProjectUpdate


class ProjectService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _log_audit_event(
        self,
        action: str,
        user_id: uuid.UUID,
        resource_id: str,
        metadata: dict | None = None,
    ) -> None:
        """Create audit log record."""
        audit_entry = AuditLog(
            id=uuid.uuid4(),
            user_id=user_id,
            action=action,
            resource_type="PROJECT",
            resource_id=resource_id,
            metadata_json=metadata or {},
        )
        self.db.add(audit_entry)
        await self.db.commit()

    async def create_project(self, payload: ProjectCreate, user: User) -> Project:
        """Create a new project workspace under current user."""
        project = Project(
            id=uuid.uuid4(),
            name=payload.name.strip(),
            description=payload.description.strip() if payload.description else None,
            owner_id=user.id,
        )
        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)

        await self._log_audit_event(
            action="PROJECT_CREATE",
            user_id=user.id,
            resource_id=str(project.id),
            metadata={"name": project.name},
        )
        return project

    async def list_projects(
        self,
        user: User,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
    ) -> Tuple[List[ProjectResponse], int, int]:
        """List accessible projects with pagination and item counts."""
        query = select(Project).options(selectinload(Project.owner))

        # Non-admins only view their own projects
        if user.role != UserRole.ADMIN:
            query = query.where(Project.owner_id == user.id)

        if search:
            search_term = f"%{search.strip()}%"
            query = query.where(
                or_(
                    Project.name.ilike(search_term),
                    Project.description.ilike(search_term),
                )
            )

        # Count total matches
        count_stmt = select(func.count()).select_from(query.subquery())
        total_count = (await self.db.execute(count_stmt)).scalar() or 0

        # Paginated items
        offset = (page - 1) * page_size
        query = query.order_by(Project.created_at.desc()).offset(offset).limit(page_size)
        result = await self.db.execute(query)
        projects = result.scalars().all()

        total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1

        # Fetch relation counts for each project
        items: List[ProjectResponse] = []
        for p in projects:
            d_count = (
                await self.db.execute(select(func.count(Dataset.id)).where(Dataset.project_id == p.id))
            ).scalar() or 0

            m_count = (
                await self.db.execute(select(func.count(TrainedModel.id)).where(TrainedModel.project_id == p.id))
            ).scalar() or 0

            e_count = (
                await self.db.execute(select(func.count(Experiment.id)).where(Experiment.project_id == p.id))
            ).scalar() or 0

            items.append(
                ProjectResponse(
                    id=p.id,
                    name=p.name,
                    description=p.description,
                    owner_id=p.owner_id,
                    owner_email=p.owner.email if p.owner else None,
                    owner_name=p.owner.full_name if p.owner else None,
                    dataset_count=d_count,
                    model_count=m_count,
                    experiment_count=e_count,
                    created_at=p.created_at,
                    updated_at=p.updated_at,
                )
            )

        return items, total_count, total_pages

    async def get_project_by_id(self, project_id: uuid.UUID, user: User) -> ProjectDetailResponse:
        """Retrieve project details with children (datasets, models, experiments)."""
        stmt = (
            select(Project)
            .options(
                selectinload(Project.owner),
                selectinload(Project.datasets),
                selectinload(Project.trained_models),
                selectinload(Project.experiments),
            )
            .where(Project.id == project_id)
        )
        result = await self.db.execute(stmt)
        project = result.scalar_one_or_none()

        if not project:
            raise NotFoundException(f"Project with ID '{project_id}' not found")

        if user.role != UserRole.ADMIN and project.owner_id != user.id:
            raise AuthorizationException("You do not have permission to view this project")

        datasets_summary = [
            {
                "id": str(d.id),
                "filename": d.filename,
                "file_size": d.file_size,
                "row_count": d.row_count,
                "column_count": d.column_count,
                "status": d.status.value,
                "created_at": d.created_at.isoformat(),
            }
            for d in project.datasets
        ]

        models_summary = [
            {
                "id": str(m.id),
                "name": m.name,
                "version": m.version,
                "task_type": m.task_type,
                "status": m.status.value,
                "metrics": m.metrics,
                "created_at": m.created_at.isoformat(),
            }
            for m in project.trained_models
        ]

        experiments_summary = [
            {
                "id": str(e.id),
                "name": e.name,
                "mlflow_experiment_id": e.mlflow_experiment_id,
                "created_at": e.created_at.isoformat(),
            }
            for e in project.experiments
        ]

        return ProjectDetailResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            owner_id=project.owner_id,
            owner_email=project.owner.email if project.owner else None,
            owner_name=project.owner.full_name if project.owner else None,
            dataset_count=len(project.datasets),
            model_count=len(project.trained_models),
            experiment_count=len(project.experiments),
            datasets=datasets_summary,
            models=models_summary,
            experiments=experiments_summary,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )

    async def update_project(
        self,
        project_id: uuid.UUID,
        payload: ProjectUpdate,
        user: User,
    ) -> Project:
        """Update project name or description with ownership enforcement."""
        stmt = select(Project).where(Project.id == project_id)
        result = await self.db.execute(stmt)
        project = result.scalar_one_or_none()

        if not project:
            raise NotFoundException(f"Project with ID '{project_id}' not found")

        if user.role != UserRole.ADMIN and project.owner_id != user.id:
            raise AuthorizationException("Only the project owner or an administrator can modify this project")

        if payload.name is not None:
            project.name = payload.name.strip()
        if payload.description is not None:
            project.description = payload.description.strip()

        await self.db.commit()
        await self.db.refresh(project)

        await self._log_audit_event(
            action="PROJECT_UPDATE",
            user_id=user.id,
            resource_id=str(project.id),
            metadata={"name": project.name},
        )
        return project

    async def delete_project(self, project_id: uuid.UUID, user: User) -> None:
        """Delete project workspace and cascaded children with ownership enforcement."""
        stmt = select(Project).where(Project.id == project_id)
        result = await self.db.execute(stmt)
        project = result.scalar_one_or_none()

        if not project:
            raise NotFoundException(f"Project with ID '{project_id}' not found")

        if user.role != UserRole.ADMIN and project.owner_id != user.id:
            raise AuthorizationException("Only the project owner or an administrator can delete this project")

        await self.db.delete(project)
        await self.db.commit()

        await self._log_audit_event(
            action="PROJECT_DELETE",
            user_id=user.id,
            resource_id=str(project.id),
        )
