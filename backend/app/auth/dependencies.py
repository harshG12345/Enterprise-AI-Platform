"""FastAPI dependencies for JWT authentication and user extraction."""

import uuid

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import decode_jwt_token
from app.core.exceptions import AuthenticationException
from app.database.database import get_db
from app.models.user import User
from app.services.user_service import UserService

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False,
)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and authenticate current user from Bearer JWT token."""
    if not token:
        raise AuthenticationException("Authentication credentials were not provided")

    payload = decode_jwt_token(token)
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise AuthenticationException("Invalid authentication token payload")

    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError as e:
        raise AuthenticationException("Invalid user identifier in token") from e

    user_service = UserService(db)
    user = await user_service.get_by_id(user_uuid)
    if not user:
        raise AuthenticationException("User corresponding to this token does not exist")

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Verify current authenticated user is active."""
    if not current_user.is_active:
        raise AuthenticationException("Inactive user account")
    return current_user
