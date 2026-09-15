"""Notification Service managing notification lifecycles, read states, and system alerts."""

import math
import uuid
from datetime import UTC, datetime
from typing import List, Optional, Tuple

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthorizationException, NotFoundException
from app.models.notification import Notification, NotificationCategory, NotificationType
from app.models.user import User, UserRole
from app.schemas.notification import NotificationCreate


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_notification(
        self,
        payload: NotificationCreate,
        user_id: uuid.UUID,
    ) -> Notification:
        """Create and persist a new notification for a specific user."""
        notification = Notification(
            id=uuid.uuid4(),
            user_id=user_id,
            title=payload.title.strip(),
            message=payload.message.strip(),
            type=payload.type,
            category=payload.category,
            link=payload.link.strip() if payload.link else None,
            is_read=False,
            created_at=datetime.now(UTC),
        )
        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)
        return notification

    async def get_user_notifications(
        self,
        user_id: uuid.UUID,
        unread_only: bool = False,
        category: Optional[NotificationCategory] = None,
        notification_type: Optional[NotificationType] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Notification], int, int, int]:
        """Fetch paginated notifications with filters for a user.

        Returns:
            (items, total_count, unread_count, total_pages)
        """
        # Base query for user notifications
        base_query = select(Notification).where(Notification.user_id == user_id)

        if unread_only:
            base_query = base_query.where(Notification.is_read.is_(False))
        if category:
            base_query = base_query.where(Notification.category == category)
        if notification_type:
            base_query = base_query.where(Notification.type == notification_type)

        # Count total matching items
        count_stmt = select(func.count()).select_from(base_query.subquery())
        total_result = await self.db.execute(count_stmt)
        total_count = total_result.scalar() or 0

        # Count total unread items for badge
        unread_stmt = (
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_id == user_id, Notification.is_read.is_(False))
        )
        unread_result = await self.db.execute(unread_stmt)
        unread_count = unread_result.scalar() or 0

        # Calculate pagination offsets
        total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1
        offset = (page - 1) * page_size

        # Fetch ordered paginated items
        items_stmt = (
            base_query.order_by(Notification.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        items_result = await self.db.execute(items_stmt)
        items = list(items_result.scalars().all())

        return items, total_count, unread_count, total_pages

    async def get_unread_count(self, user_id: uuid.UUID) -> int:
        """Fast query for active unread notifications count."""
        stmt = (
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_id == user_id, Notification.is_read.is_(False))
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def mark_as_read(
        self,
        notification_id: uuid.UUID,
        user: User,
    ) -> Notification:
        """Mark a single notification as read."""
        stmt = select(Notification).where(Notification.id == notification_id)
        result = await self.db.execute(stmt)
        notification = result.scalar_one_or_none()

        if not notification:
            raise NotFoundException("Notification not found")

        if notification.user_id != user.id and user.role != UserRole.ADMIN:
            raise AuthorizationException("Access denied to this notification")

        notification.is_read = True
        notification.read_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(notification)
        return notification

    async def mark_all_as_read(self, user_id: uuid.UUID) -> int:
        """Batch update all unread notifications for a user to read status."""
        stmt = (
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read.is_(False))
            .values(is_read=True, read_at=datetime.now(UTC))
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount

    async def delete_notification(
        self,
        notification_id: uuid.UUID,
        user: User,
    ) -> bool:
        """Delete a single notification."""
        stmt = select(Notification).where(Notification.id == notification_id)
        result = await self.db.execute(stmt)
        notification = result.scalar_one_or_none()

        if not notification:
            raise NotFoundException("Notification not found")

        if notification.user_id != user.id and user.role != UserRole.ADMIN:
            raise AuthorizationException("Access denied to delete this notification")

        await self.db.delete(notification)
        await self.db.commit()
        return True

    async def clear_all_notifications(self, user_id: uuid.UUID) -> int:
        """Delete all notifications for a user."""
        stmt = delete(Notification).where(Notification.user_id == user_id)
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount

    async def seed_demo_notifications(self, user_id: uuid.UUID) -> List[Notification]:
        """Seed realistic notifications for live demo presentations."""
        demo_items = [
            NotificationCreate(
                title="Critical Data Drift Detected",
                message="Monthly Charges feature in Production Churn Model drifted with PSI = 0.285 (threshold > 0.25). Immediate retraining recommended.",
                type=NotificationType.WARNING,
                category=NotificationCategory.DRIFT,
                link="/monitoring",
            ),
            NotificationCreate(
                title="XGBoost Classifier Training Succeeded",
                message="Training job completed with 5-Fold Cross Validation. Validation ROC-AUC: 0.884, F1-Score: 0.792.",
                type=NotificationType.SUCCESS,
                category=NotificationCategory.TRAINING,
                link="/models",
            ),
            NotificationCreate(
                title="Model Promoted to Production",
                message="XGBoost Customer Churn Predictor v1.0 has been approved and promoted to active Production serving.",
                type=NotificationType.SUCCESS,
                category=NotificationCategory.MODEL,
                link="/models",
            ),
            NotificationCreate(
                title="Dataset Ingestion & EDA Ready",
                message="Dataset 'Telco Customer Churn Baseline' (1,200 rows, 9 columns) parsed successfully. Correlation matrix & outlier profiles generated.",
                type=NotificationType.INFO,
                category=NotificationCategory.DATASET,
                link="/eda",
            ),
            NotificationCreate(
                title="System Cluster Health OK",
                message="All 9 microservice containers (PostgreSQL, Redis, Celery, MLflow, Prometheus, Grafana) reporting healthy status.",
                type=NotificationType.INFO,
                category=NotificationCategory.SYSTEM,
                link="/",
            ),
        ]

        created = []
        for item in demo_items:
            notif = await self.create_notification(item, user_id)
            created.append(notif)

        return created
