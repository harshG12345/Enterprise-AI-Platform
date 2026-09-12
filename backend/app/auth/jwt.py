"""JWT Token encoding, decoding, and expiration management."""

from datetime import UTC, datetime, timedelta
from typing import Any, Dict

from jose import JWTError, jwt

from app.config.settings import get_settings
from app.core.exceptions import AuthenticationException

settings = get_settings()


def create_jwt_token(payload: Dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create signed JWT access token."""
    to_encode = payload.copy()
    now = datetime.now(UTC)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)
    to_encode.update({"exp": expire, "iat": now})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_jwt_token(token: str) -> Dict[str, Any]:
    """Decode and validate JWT access token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError as e:
        raise AuthenticationException("Could not validate credentials or token has expired") from e
