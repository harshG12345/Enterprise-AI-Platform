"""Authentication service handling registration, login, and password transitions."""

import uuid
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import create_jwt_token
from app.auth.password import get_password_hash, validate_password_strength, verify_password
from app.config.settings import get_settings
from app.core.exceptions import AuthenticationException, ValidationException
from app.models.audit_log import AuditLog
from app.models.user import User, UserRole
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.services.user_service import UserService

settings = get_settings()


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_service = UserService(db)

    async def _log_audit_event(
        self,
        action: str,
        user_id: uuid.UUID | None,
        resource_id: str | None = None,
        ip_address: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        """Create audit log record."""
        audit_entry = AuditLog(
            id=uuid.uuid4(),
            user_id=user_id,
            action=action,
            resource_type="AUTH",
            resource_id=resource_id,
            ip_address=ip_address,
            metadata_json=metadata or {},
        )
        self.db.add(audit_entry)
        await self.db.commit()

    async def register(self, payload: RegisterRequest, ip_address: str | None = None) -> User:
        """Validate, hash, create, and audit new user registration."""
        validate_password_strength(payload.password)
        hashed_password = get_password_hash(payload.password)

        user = await self.user_service.create_user(
            email=payload.email,
            full_name=payload.full_name,
            password_hash=hashed_password,
            role=payload.role or UserRole.USER,
        )

        await self._log_audit_event(
            action="USER_REGISTER",
            user_id=user.id,
            resource_id=str(user.id),
            ip_address=ip_address,
            metadata={"email": user.email, "role": user.role.value},
        )
        return user

    async def authenticate(self, payload: LoginRequest, ip_address: str | None = None) -> TokenResponse:
        """Validate credentials, issue JWT, and record audit log."""
        user = await self.user_service.get_by_email(payload.email)
        if not user or not verify_password(payload.password, user.password_hash):
            await self._log_audit_event(
                action="AUTH_FAILURE",
                user_id=None,
                ip_address=ip_address,
                metadata={"email": payload.email, "reason": "invalid_credentials"},
            )
            raise AuthenticationException("Invalid email or password")

        if not user.is_active:
            raise AuthenticationException("User account is inactive")

        token_payload = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value,
        }
        access_token = create_jwt_token(
            payload=token_payload,
            expires_delta=timedelta(minutes=settings.JWT_EXPIRATION_MINUTES),
        )

        await self._log_audit_event(
            action="AUTH_LOGIN_SUCCESS",
            user_id=user.id,
            resource_id=str(user.id),
            ip_address=ip_address,
            metadata={"email": user.email},
        )

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.JWT_EXPIRATION_MINUTES * 60,
        )

    async def change_password(
        self,
        user: User,
        current_password: str,
        new_password: str,
        ip_address: str | None = None,
    ) -> None:
        """Validate old password and update to new password hash."""
        if not verify_password(current_password, user.password_hash):
            raise ValidationException("Current password does not match")

        validate_password_strength(new_password)
        user.password_hash = get_password_hash(new_password)
        await self.db.commit()

        await self._log_audit_event(
            action="PASSWORD_CHANGE",
            user_id=user.id,
            resource_id=str(user.id),
            ip_address=ip_address,
        )
