"""Service layer for preprocessing pipeline orchestration, execution, and artifact storage."""

import os
import pickle
import uuid
from typing import Any, Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config.settings import get_settings
from app.core.exceptions import AuthorizationException, NotFoundException, ValidationException
from app.core.storage import storage_backend
from app.ml.data_loader import DataLoader
from app.ml.preprocessor import PreprocessingPipelineBuilder
from app.models.dataset import Dataset
from app.models.user import User, UserRole
from app.schemas.preprocessor import (
    PipelineSummaryItem,
    PreprocessingConfig,
    PreprocessingResponse,
)

settings = get_settings()


class PreprocessorService:
    """Orchestrates pipeline configuration validation, transformation, and serialization."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.pipelines_dir = os.path.join(settings.UPLOAD_DIR, "pipelines")
        os.makedirs(self.pipelines_dir, exist_ok=True)

    async def _get_authorized_dataset(self, dataset_id: uuid.UUID, user: User) -> Dataset:
        """Fetch dataset and assert read authorization."""
        stmt = select(Dataset).options(selectinload(Dataset.project)).where(Dataset.id == dataset_id)
        result = await self.db.execute(stmt)
        dataset = result.scalar_one_or_none()

        if not dataset:
            raise NotFoundException(f"Dataset with ID '{dataset_id}' not found")

        if user.role != UserRole.ADMIN and dataset.project.owner_id != user.id:
            raise AuthorizationException("You do not have permission to access this dataset")

        return dataset

    async def validate_config(self, dataset_id: uuid.UUID, config: PreprocessingConfig, user: User) -> Dict[str, Any]:
        """Validate that all columns in config exist in dataset."""
        dataset = await self._get_authorized_dataset(dataset_id, user)
        abs_path = storage_backend.get_absolute_path(dataset.storage_path)
        df = DataLoader.load_file(abs_path)
        existing_cols = set(df.columns)

        missing_cols = []
        if config.target_column and config.target_column not in existing_cols:
            missing_cols.append(f"Target column '{config.target_column}'")

        for num in config.numerical_features:
            if num.column_name not in existing_cols:
                missing_cols.append(f"Numerical column '{num.column_name}'")

        for cat in config.categorical_features:
            if cat.column_name not in existing_cols:
                missing_cols.append(f"Categorical column '{cat.column_name}'")

        for dt in config.datetime_features:
            if dt.column_name not in existing_cols:
                missing_cols.append(f"Datetime column '{dt.column_name}'")

        if missing_cols:
            raise ValidationException(f"Invalid columns in configuration: {', '.join(missing_cols)}")

        return {
            "valid": True,
            "columns_configured": len(config.numerical_features)
            + len(config.categorical_features)
            + len(config.datetime_features),
            "target_column": config.target_column,
            "problem_type": config.problem_type,
        }

    async def execute_preprocessing(
        self,
        dataset_id: uuid.UUID,
        config: PreprocessingConfig,
        user: User,
    ) -> PreprocessingResponse:
        """Load tabular data, fit transformation pipeline on train split, and persist artifact."""
        dataset = await self._get_authorized_dataset(dataset_id, user)
        abs_path = storage_backend.get_absolute_path(dataset.storage_path)
        df = DataLoader.load_file(abs_path)

        # Execute transformation with zero leakage
        response, _ = PreprocessingPipelineBuilder.execute_pipeline(
            df=df,
            config=config,
            dataset_id=str(dataset.id),
            dataset_name=dataset.filename,
            output_dir=self.pipelines_dir,
        )

        return response

    async def list_pipelines(self, dataset_id: uuid.UUID, user: User) -> List[PipelineSummaryItem]:
        """List all saved pipeline artifacts for a dataset."""
        await self._get_authorized_dataset(dataset_id, user)
        items: List[PipelineSummaryItem] = []

        if not os.path.exists(self.pipelines_dir):
            return items

        for fname in os.listdir(self.pipelines_dir):
            if fname.startswith("pipeline_") and fname.endswith(".pkl"):
                fpath = os.path.join(self.pipelines_dir, fname)
                try:
                    with open(fpath, "rb") as f:
                        data = pickle.load(f)
                    if data.get("dataset_id") == str(dataset_id):
                        cfg = data.get("config", {})
                        items.append(
                            PipelineSummaryItem(
                                pipeline_id=data.get("pipeline_id", ""),
                                dataset_id=str(dataset_id),
                                target_column=data.get("target_column"),
                                problem_type=data.get("problem_type"),
                                transformed_feature_count=len(data.get("feature_names", [])),
                                train_rows=0,
                                test_rows=0,
                                created_at=data.get("created_at", ""),
                            )
                        )
                except Exception:
                    continue

        return items
