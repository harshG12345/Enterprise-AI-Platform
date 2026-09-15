"""Notification Pydantic Schemas."""

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.notification import NotificationCategory, NotificationType


class NotificationBase(BaseModel):
    title: str = Field(..., max_length=255, description="Notification summary headline")
    message: str = Field(..., description="Detailed message content")
    type: NotificationType = Field(default=NotificationType.INFO, description="Visual severity type")
    category: NotificationCategory = Field(default=NotificationCategory.SYSTEM, description="Domain category")
    link: Optional[str] = Field(default=None, max_length=500, description="Target destination route")


class NotificationCreate(NotificationBase):
    pass


class NotificationUpdate(BaseModel):
    is_read: Optional[bool] = None


class NotificationResponse(NotificationBase):
    id: uuid.UUID
    user_id: uuid.UUID
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class NotificationListResponse(BaseModel):
    items: List[NotificationResponse]
    total: int
    unread_count: int
    page: int
    page_size: int
    total_pages: int


class UnreadCountResponse(BaseModel):
    unread_count: int


class NotificationBatchActionResponse(BaseModel):
    success: bool
    message: str
    affected_count: int
