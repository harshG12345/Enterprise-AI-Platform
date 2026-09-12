"""Prediction Model."""

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Dict, Optional

from sqlalchemy import JSON, DateTime, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import GUID, Base

if TYPE_CHECKING:
    from app.models.trained_model import TrainedModel
    from app.models.user import User


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    model_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("trained_models.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    input_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    prediction: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        index=True,
    )

    # Relationships
    model: Mapped["TrainedModel"] = relationship("TrainedModel", back_populates="predictions")
    user: Mapped[Optional["User"]] = relationship("User", back_populates="predictions")
