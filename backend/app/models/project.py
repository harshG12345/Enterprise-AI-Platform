"""Project Model."""

import uuid
from typing import TYPE_CHECKING, List

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import GUID, Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.dataset import Dataset
    from app.models.experiment import Experiment
    from app.models.trained_model import TrainedModel
    from app.models.training_job import TrainingJob
    from app.models.user import User


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="projects")
    datasets: Mapped[List["Dataset"]] = relationship("Dataset", back_populates="project", cascade="all, delete-orphan")
    experiments: Mapped[List["Experiment"]] = relationship(
        "Experiment", back_populates="project", cascade="all, delete-orphan"
    )
    training_jobs: Mapped[List["TrainingJob"]] = relationship(
        "TrainingJob", back_populates="project", cascade="all, delete-orphan"
    )
    trained_models: Mapped[List["TrainedModel"]] = relationship(
        "TrainedModel", back_populates="project", cascade="all, delete-orphan"
    )
