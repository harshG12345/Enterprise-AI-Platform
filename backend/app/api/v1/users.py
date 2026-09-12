"""User profile and user management endpoints."""

from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user
from app.auth.permissions import require_admin
from app.core.responses import APIResponse
from app.database.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=APIResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Current User Profile",
)
async def get_me(
    current_user: User = Depends(get_current_active_user),
) -> APIResponse[UserResponse]:
    """Return profile metadata for current authenticated user."""
    return APIResponse(
        success=True,
        data=UserResponse.model_validate(current_user),
        message="User profile retrieved successfully",
    )


@router.get(
    "",
    response_model=APIResponse[List[UserResponse]],
    status_code=status.HTTP_200_OK,
    summary="List All Users (Admin Only)",
)
async def list_users(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[UserResponse]]:
    """Return all registered users in the platform."""
    stmt = select(User).order_by(User.created_at.desc())
    result = await db.execute(stmt)
    users = result.scalars().all()

    return APIResponse(
        success=True,
        data=[UserResponse.model_validate(u) for u in users],
        message="Users list retrieved successfully",
    )
