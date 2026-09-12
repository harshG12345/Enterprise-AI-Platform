"""Pydantic schemas for authentication requests and responses."""

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., json_schema_extra={"example": "jane.doe@enterprise-ai.io"})
    full_name: str = Field(..., min_length=2, max_length=100, json_schema_extra={"example": "Jane Doe"})
    password: str = Field(..., min_length=8, json_schema_extra={"example": "SecurePass123!"})
    role: UserRole | None = Field(default=UserRole.USER)


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., json_schema_extra={"example": "jane.doe@enterprise-ai.io"})
    password: str = Field(..., json_schema_extra={"example": "SecurePass123!"})


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., json_schema_extra={"example": "OldSecurePass123!"})
    new_password: str = Field(..., min_length=8, json_schema_extra={"example": "NewSecurePass456!"})


class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(..., json_schema_extra={"example": "jane.doe@enterprise-ai.io"})
