"""Audit Logs REST API endpoint for compliance, security, and governance tracking."""

import math
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user
from app.core.responses import APIResponse
from app.database.database import get_db
from app.models.audit_log import AuditLog
from app.models.user import User, UserRole
from app.schemas.audit_log import AuditLogListResponse, AuditLogResponse

router = APIRouter(prefix="/audit-logs", tags=["Audit & Governance"])


@router.get(
    "",
    response_model=APIResponse[AuditLogListResponse],
    summary="List System Audit Logs",
    description="Retrieve paginated audit logs for the current user or platform (Admins).",
)
async def list_audit_logs(
    action: Optional[str] = Query(None, description="Filter by audit action type"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[AuditLogListResponse]:
    """Fetch paginated audit log events with RBAC scope."""
    base_query = select(AuditLog)

    # Standard users only see their own audit events; Admins see all events
    if current_user.role != UserRole.ADMIN:
        base_query = base_query.where(AuditLog.user_id == current_user.id)

    if action:
        base_query = base_query.where(AuditLog.action == action)
    if resource_type:
        base_query = base_query.where(AuditLog.resource_type == resource_type)

    # Count total
    count_stmt = select(func.count()).select_from(base_query.subquery())
    total_res = await db.execute(count_stmt)
    total_count = total_res.scalar() or 0

    total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1
    offset = (page - 1) * page_size

    # Fetch items
    items_stmt = (
        base_query.order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    items_res = await db.execute(items_stmt)
    items = items_res.scalars().all()

    data = AuditLogListResponse(
        items=[AuditLogResponse.model_validate(item) for item in items],
        total=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )

    return APIResponse(
        success=True,
        data=data,
        message="Audit logs retrieved successfully",
    )
