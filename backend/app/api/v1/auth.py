"""Authentication endpoints for registration, login, and password management."""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user
from app.core.responses import APIResponse
from app.database.database import get_db
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=APIResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register New User",
)
async def register(
    payload: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[UserResponse]:
    """Create a new user account with Argon2 password hashing."""
    auth_service = AuthService(db)
    client_ip = request.client.host if request.client else None
    user = await auth_service.register(payload, ip_address=client_ip)

    return APIResponse(
        success=True,
        data=UserResponse.model_validate(user),
        message="User registered successfully",
    )


@router.post(
    "/login",
    response_model=APIResponse[TokenResponse],
    status_code=status.HTTP_200_OK,
    summary="User Login",
)
async def login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[TokenResponse]:
    """Authenticate user credentials and return signed JWT access token."""
    auth_service = AuthService(db)
    client_ip = request.client.host if request.client else None
    token_data = await auth_service.authenticate(payload, ip_address=client_ip)

    return APIResponse(
        success=True,
        data=token_data,
        message="Authentication successful",
    )


@router.post(
    "/change-password",
    response_model=APIResponse[None],
    status_code=status.HTTP_200_OK,
    summary="Change Password",
)
async def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[None]:
    """Update current authenticated user's password."""
    auth_service = AuthService(db)
    client_ip = request.client.host if request.client else None
    await auth_service.change_password(
        user=current_user,
        current_password=payload.current_password,
        new_password=payload.new_password,
        ip_address=client_ip,
    )
    return APIResponse(
        success=True,
        data=None,
        message="Password updated successfully",
    )


@router.post(
    "/forgot-password",
    response_model=APIResponse[None],
    status_code=status.HTTP_200_OK,
    summary="Request Password Reset",
)
async def forgot_password(
    payload: ForgotPasswordRequest,
) -> APIResponse[None]:
    """Initiate password recovery flow safely."""
    # Production: dispatch password reset token via email
    return APIResponse(
        success=True,
        data=None,
        message="If this email is registered, password recovery instructions have been sent.",
    )
