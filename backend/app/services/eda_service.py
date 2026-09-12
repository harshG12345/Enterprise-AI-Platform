"""Service handling Exploratory Data Analysis computations and reporting."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AuthorizationException, NotFoundException
from app.core.storage import storage_backend
from app.ml.data_loader import DataLoader
from app.ml.eda import EDAEngine
from app.models.dataset import Dataset
from app.models.user import User, UserRole
from app.schemas.eda import EDAResponse


class EDAService:
    """Orchestrates dataset loading and analytical profiling."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_eda_report(self, dataset_id: uuid.UUID, user: User) -> EDAResponse:
        """Fetch dataset, load tabular data from storage, and compute full EDA statistics."""
        stmt = select(Dataset).options(selectinload(Dataset.project)).where(Dataset.id == dataset_id)
        result = await self.db.execute(stmt)
        dataset = result.scalar_one_or_none()

        if not dataset:
            raise NotFoundException(f"Dataset with ID '{dataset_id}' not found")

        # Check authorization (admin or project owner)
        if user.role != UserRole.ADMIN and dataset.project.owner_id != user.id:
            raise AuthorizationException("You do not have permission to view analysis for this dataset")

        # Load file into DataFrame
        abs_path = storage_backend.get_absolute_path(dataset.storage_path)
        df = DataLoader.load_file(abs_path)

        # Compute full EDA report
        report = EDAEngine.analyze_dataset(
            df=df,
            dataset_id=str(dataset.id),
            dataset_name=dataset.filename,
        )

        return report
