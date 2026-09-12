"""TrainedModel Model & ModelStatus Enum."""

import enum
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import GUID, Base

if TYPE_CHECKING:
    from app.models.dataset import Dataset
    from app.models.experiment import Experiment
    from app.models.prediction import Prediction
    from app.models.project import Project


class ModelStatus(str, enum.Enum):
    NONE = "NONE"
    DEVELOPMENT = "DEVELOPMENT"
    STAGING = "STAGING"
    PRODUCTION = "PRODUCTION"
    ARCHIVED = "ARCHIVED"


class TrainedModel(Base):
    __tablename__ = "trained_models"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    project_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    dataset_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("datasets.id", ondelete="SET NULL"), nullable=True, index=True
    )
    experiment_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("experiments.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(50), nullable=False, default="v1.0.0")
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    framework: Mapped[str] = mapped_column(String(50), default="scikit-learn", nullable=False)
    metrics: Mapped[Dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    artifact_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    mlflow_run_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    status: Mapped[ModelStatus] = mapped_column(
        Enum(ModelStatus), default=ModelStatus.DEVELOPMENT, nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="trained_models")
    dataset: Mapped[Optional["Dataset"]] = relationship("Dataset", back_populates="trained_models")
    experiment: Mapped[Optional["Experiment"]] = relationship("Experiment", back_populates="trained_models")
    predictions: Mapped[List["Prediction"]] = relationship(
        "Prediction", back_populates="model", cascade="all, delete-orphan"
    )
