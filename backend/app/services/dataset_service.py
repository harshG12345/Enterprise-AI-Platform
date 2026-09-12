"""Service handling dataset upload, validation, storage, and previewing."""

import math
import uuid
from typing import List, Tuple

from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config.settings import get_settings
from app.core.exceptions import AuthorizationException, NotFoundException, ValidationException
from app.core.sanitizer import validate_file_upload
from app.core.storage import storage_backend
from app.ml.data_loader import DataLoader
from app.ml.validator import DatasetValidator
from app.models.audit_log import AuditLog
from app.models.dataset import Dataset, DatasetStatus
from app.models.project import Project
from app.models.user import User, UserRole
from app.schemas.dataset import (
    ColumnMetadata,
    DatasetDetailResponse,
    DatasetPreviewResponse,
    DatasetResponse,
)


class DatasetService:
    def __init__(self, db: AsyncSession):
        self.db = db

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
            resource_type="DATASET",
            resource_id=resource_id,
            metadata_json=metadata or {},
        )
        self.db.add(audit)
        await self.db.commit()

    async def _verify_project_access(self, project_id: uuid.UUID, user: User) -> Project:
        """Verify project exists and user has workspace permissions."""
        stmt = select(Project).where(Project.id == project_id)
        result = await self.db.execute(stmt)
        project = result.scalar_one_or_none()

        if not project:
            raise NotFoundException(f"Project with ID '{project_id}' not found")

        if user.role != UserRole.ADMIN and project.owner_id != user.id:
            raise AuthorizationException("You do not have permission to upload datasets to this project")

        return project

    async def upload_dataset(
        self,
        project_id: uuid.UUID,
        file: UploadFile,
        user: User,
    ) -> Dataset:
        """Save uploaded tabular file, extract schema metadata, and store record."""
        await self._verify_project_access(project_id, user)

        filename = file.filename or "uploaded_dataset.csv"
        file.file.seek(0, 2)  # Seek to end to determine size
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning

        # 1. Security Sanitization & Upload Constraints
        settings = get_settings()
        safe_filename = validate_file_upload(
            filename=filename,
            size_bytes=file_size,
            max_size_bytes=settings.MAX_UPLOAD_SIZE_BYTES,
            content_type=file.content_type,
        )

        # 2. Metadata Validation
        DatasetValidator.validate_file_metadata(filename=safe_filename, file_size=file_size)

        # 3. Secure File Persistence
        storage_path = storage_backend.save_file(
            file_obj=file.file,
            filename=safe_filename,
            subfolder=f"uploads/{project_id}",
        )
        absolute_path = storage_backend.get_absolute_path(storage_path)

        # 3. Load & Extract Schema Metadata
        try:
            df = DataLoader.load_file(absolute_path)
            meta = DataLoader.extract_metadata(df)
            status = DatasetStatus.VALIDATED
        except Exception as e:
            # Clean up saved file on parsing error
            storage_backend.delete_file(storage_path)
            raise ValidationException(f"Dataset parsing failed: {str(e)}") from e

        # 4. Create Database Entity
        dataset = Dataset(
            id=uuid.uuid4(),
            project_id=project_id,
            filename=filename,
            storage_path=storage_path,
            file_size=file_size,
            row_count=meta["row_count"],
            column_count=meta["column_count"],
            schema_metadata=meta,
            status=status,
        )
        self.db.add(dataset)
        await self.db.commit()
        await self.db.refresh(dataset)

        await self._log_audit_event(
            action="DATASET_UPLOAD",
            user_id=user.id,
            resource_id=str(dataset.id),
            metadata={"filename": filename, "rows": meta["row_count"], "cols": meta["column_count"]},
        )
        return dataset

    async def list_datasets(
        self,
        user: User,
        project_id: uuid.UUID | None = None,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
    ) -> Tuple[List[DatasetResponse], int, int]:
        """List accessible datasets with pagination and search filtering."""
        query = select(Dataset).join(Project, Dataset.project_id == Project.id)

        if user.role != UserRole.ADMIN:
            query = query.where(Project.owner_id == user.id)

        if project_id:
            query = query.where(Dataset.project_id == project_id)

        if search:
            query = query.where(Dataset.filename.ilike(f"%{search.strip()}%"))

        count_stmt = select(func.count()).select_from(query.subquery())
        total_count = (await self.db.execute(count_stmt)).scalar() or 0

        offset = (page - 1) * page_size
        query = query.order_by(Dataset.created_at.desc()).offset(offset).limit(page_size)
        result = await self.db.execute(query)
        datasets = result.scalars().all()

        total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1
        items = [DatasetResponse.model_validate(d) for d in datasets]

        return items, total_count, total_pages

    async def get_dataset_by_id(self, dataset_id: uuid.UUID, user: User) -> DatasetDetailResponse:
        """Fetch dataset by ID and return full metadata breakdown."""
        stmt = select(Dataset).options(selectinload(Dataset.project)).where(Dataset.id == dataset_id)
        result = await self.db.execute(stmt)
        dataset = result.scalar_one_or_none()

        if not dataset:
            raise NotFoundException(f"Dataset with ID '{dataset_id}' not found")

        if user.role != UserRole.ADMIN and dataset.project.owner_id != user.id:
            raise AuthorizationException("You do not have permission to view this dataset")

        columns_data: List[ColumnMetadata] = []
        memory_bytes = None
        if dataset.schema_metadata and "columns" in dataset.schema_metadata:
            columns_data = [ColumnMetadata(**col) for col in dataset.schema_metadata.get("columns", [])]
            memory_bytes = dataset.schema_metadata.get("memory_bytes")

        return DatasetDetailResponse(
            id=dataset.id,
            project_id=dataset.project_id,
            filename=dataset.filename,
            file_size=dataset.file_size,
            row_count=dataset.row_count,
            column_count=dataset.column_count,
            status=dataset.status,
            schema_metadata=dataset.schema_metadata,
            columns=columns_data,
            memory_bytes=memory_bytes,
            created_at=dataset.created_at,
            updated_at=dataset.updated_at,
        )

    async def get_preview(
        self,
        dataset_id: uuid.UUID,
        user: User,
        page: int = 1,
        page_size: int = 50,
    ) -> DatasetPreviewResponse:
        """Load and return paginated dataset rows with JSON sanitization."""
        stmt = select(Dataset).options(selectinload(Dataset.project)).where(Dataset.id == dataset_id)
        result = await self.db.execute(stmt)
        dataset = result.scalar_one_or_none()

        if not dataset:
            raise NotFoundException(f"Dataset with ID '{dataset_id}' not found")

        if user.role != UserRole.ADMIN and dataset.project.owner_id != user.id:
            raise AuthorizationException("You do not have permission to preview this dataset")

        abs_path = storage_backend.get_absolute_path(dataset.storage_path)
        df = DataLoader.load_file(abs_path)
        rows, total_rows, total_pages = DataLoader.get_paginated_preview(
            df=df,
            page=page,
            page_size=page_size,
        )

        return DatasetPreviewResponse(
            columns=[str(c) for c in df.columns],
            rows=rows,
            total_rows=total_rows,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def delete_dataset(self, dataset_id: uuid.UUID, user: User) -> None:
        """Delete dataset file from storage and database record."""
        stmt = select(Dataset).options(selectinload(Dataset.project)).where(Dataset.id == dataset_id)
        result = await self.db.execute(stmt)
        dataset = result.scalar_one_or_none()

        if not dataset:
            raise NotFoundException(f"Dataset with ID '{dataset_id}' not found")

        if user.role != UserRole.ADMIN and dataset.project.owner_id != user.id:
            raise AuthorizationException("Only the project owner or an administrator can delete this dataset")

        # Delete physical file
        storage_backend.delete_file(dataset.storage_path)

        await self.db.delete(dataset)
        await self.db.commit()

        await self._log_audit_event(
            action="DATASET_DELETE",
            user_id=user.id,
            resource_id=str(dataset.id),
        )
