"""Password hashing and validation using Argon2 and Bcrypt."""

import re

from passlib.context import CryptContext

from app.core.exceptions import ValidationException

pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    deprecated="auto",
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate secure Argon2 hash for password."""
    return pwd_context.hash(password)


def validate_password_strength(password: str) -> None:
    """Enforce enterprise password complexity policy."""
    if len(password) < 8:
        raise ValidationException("Password must be at least 8 characters long")
    if not re.search(r"[A-Z]", password):
        raise ValidationException("Password must contain at least one uppercase letter")
    if not re.search(r"[a-z]", password):
        raise ValidationException("Password must contain at least one lowercase letter")
    if not re.search(r"\d", password):
        raise ValidationException("Password must contain at least one digit")
