"""Notifications REST API endpoints for user alert and monitoring events."""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user
from app.core.responses import APIResponse
from app.database.database import get_db
from app.models.notification import NotificationCategory, NotificationType
from app.models.user import User
from app.schemas.notification import (
    NotificationBatchActionResponse,
    NotificationCreate,
    NotificationListResponse,
    NotificationResponse,
    UnreadCountResponse,
)
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get(
    "",
    response_model=APIResponse[NotificationListResponse],
    summary="List User Notifications",
)
async def list_notifications(
    unread_only: bool = Query(False, description="Filter only unread notifications"),
    category: Optional[NotificationCategory] = Query(None, description="Filter by domain category"),
    notification_type: Optional[NotificationType] = Query(None, description="Filter by visual severity"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[NotificationListResponse]:
    """Retrieve paginated notifications for the current authenticated user."""
    service = NotificationService(db)
    items, total, unread_count, total_pages = await service.get_user_notifications(
        user_id=current_user.id,
        unread_only=unread_only,
        category=category,
        notification_type=notification_type,
        page=page,
        page_size=page_size,
    )

    data = NotificationListResponse(
        items=[NotificationResponse.model_validate(item) for item in items],
        total=total,
        unread_count=unread_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )

    return APIResponse(
        success=True,
        data=data,
        message="Notifications retrieved successfully",
    )


@router.get(
    "/unread-count",
    response_model=APIResponse[UnreadCountResponse],
    summary="Get Unread Notification Count",
)
async def get_unread_count(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[UnreadCountResponse]:
    """Get fast count of unread notifications for badge indicators."""
    service = NotificationService(db)
    count = await service.get_unread_count(current_user.id)
    return APIResponse(
        success=True,
        data=UnreadCountResponse(unread_count=count),
        message="Unread count retrieved",
    )


@router.post(
    "",
    response_model=APIResponse[NotificationResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Notification",
)
async def create_notification(
    payload: NotificationCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[NotificationResponse]:
    """Create a new notification for current user (or system triggers)."""
    service = NotificationService(db)
    notification = await service.create_notification(payload, current_user.id)
    return APIResponse(
        success=True,
        data=NotificationResponse.model_validate(notification),
        message="Notification created successfully",
    )


@router.post(
    "/seed-demo",
    response_model=APIResponse[List[NotificationResponse]],
    status_code=status.HTTP_201_CREATED,
    summary="Seed Demo Notifications",
)
async def seed_demo_notifications(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[NotificationResponse]]:
    """Seed sample notifications for live demo presentations and showcases."""
    service = NotificationService(db)
    notifications = await service.seed_demo_notifications(current_user.id)
    return APIResponse(
        success=True,
        data=[NotificationResponse.model_validate(n) for n in notifications],
        message="Demo notifications seeded successfully",
    )


@router.patch(
    "/{notification_id}/read",
    response_model=APIResponse[NotificationResponse],
    summary="Mark Notification as Read",
)
async def mark_notification_read(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[NotificationResponse]:
    """Mark a single notification as read."""
    service = NotificationService(db)
    notification = await service.mark_as_read(notification_id, current_user)
    return APIResponse(
        success=True,
        data=NotificationResponse.model_validate(notification),
        message="Notification marked as read",
    )


@router.post(
    "/mark-all-read",
    response_model=APIResponse[NotificationBatchActionResponse],
    summary="Mark All Notifications as Read",
)
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[NotificationBatchActionResponse]:
    """Mark all unread notifications for the current user as read."""
    service = NotificationService(db)
    affected = await service.mark_all_as_read(current_user.id)
    return APIResponse(
        success=True,
        data=NotificationBatchActionResponse(
            success=True,
            message=f"Marked {affected} notifications as read",
            affected_count=affected,
        ),
        message="All notifications marked as read",
    )


@router.delete(
    "/{notification_id}",
    response_model=APIResponse[NotificationBatchActionResponse],
    summary="Delete Notification",
)
async def delete_notification(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[NotificationBatchActionResponse]:
    """Delete a specific notification."""
    service = NotificationService(db)
    await service.delete_notification(notification_id, current_user)
    return APIResponse(
        success=True,
        data=NotificationBatchActionResponse(
            success=True,
            message="Notification deleted",
            affected_count=1,
        ),
        message="Notification deleted successfully",
    )


@router.delete(
    "",
    response_model=APIResponse[NotificationBatchActionResponse],
    summary="Clear All Notifications",
)
async def clear_all_notifications(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[NotificationBatchActionResponse]:
    """Clear and delete all notifications for the current user."""
    service = NotificationService(db)
    affected = await service.clear_all_notifications(current_user.id)
    return APIResponse(
        success=True,
        data=NotificationBatchActionResponse(
            success=True,
            message=f"Cleared {affected} notifications",
            affected_count=affected,
        ),
        message="All notifications cleared successfully",
    )
