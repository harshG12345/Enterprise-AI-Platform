"""Dataset Model & Status Enum."""

import enum
import uuid
from typing import TYPE_CHECKING, Any, Dict, List

from sqlalchemy import JSON, BigInteger, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import GUID, Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.experiment import Experiment
    from app.models.project import Project
    from app.models.trained_model import TrainedModel
    from app.models.training_job import TrainingJob


class DatasetStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    VALIDATED = "VALIDATED"
    ERROR = "ERROR"


class Dataset(Base, TimestampMixin):
    __tablename__ = "datasets"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    project_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    column_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    schema_metadata: Mapped[Dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    status: Mapped[DatasetStatus] = mapped_column(
        Enum(DatasetStatus), default=DatasetStatus.PENDING, nullable=False, index=True
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="datasets")
    experiments: Mapped[List["Experiment"]] = relationship(
        "Experiment", back_populates="dataset", cascade="all, delete-orphan"
    )
    training_jobs: Mapped[List["TrainingJob"]] = relationship(
        "TrainingJob", back_populates="dataset", cascade="all, delete-orphan"
    )
    trained_models: Mapped[List["TrainedModel"]] = relationship(
        "TrainedModel", back_populates="dataset", cascade="all, delete-orphan"
    )
