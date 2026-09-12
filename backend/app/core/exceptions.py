"""Domain custom exceptions for clean, safe error handling."""

from typing import Any, Dict


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_SERVER_ERROR",
        status_code: int = 500,
        details: Dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class NotFoundException(AppException):
    """Resource not found exception."""

    def __init__(self, message: str = "Resource not found", details: Dict[str, Any] | None = None):
        super().__init__(message=message, code="NOT_FOUND", status_code=404, details=details)


class AuthenticationException(AppException):
    """Authentication failure exception."""

    def __init__(self, message: str = "Invalid credentials", details: Dict[str, Any] | None = None):
        super().__init__(message=message, code="UNAUTHENTICATED", status_code=401, details=details)


class AuthorizationException(AppException):
    """Permission denied exception."""

    def __init__(self, message: str = "Permission denied", details: Dict[str, Any] | None = None):
        super().__init__(message=message, code="PERMISSION_DENIED", status_code=403, details=details)


class ValidationException(AppException):
    """Data or schema validation exception."""

    def __init__(self, message: str = "Validation failed", details: Dict[str, Any] | None = None):
        super().__init__(message=message, code="VALIDATION_ERROR", status_code=422, details=details)


class ConflictException(AppException):
    """Resource conflict (e.g. duplicate key) exception."""

    def __init__(self, message: str = "Resource conflict", details: Dict[str, Any] | None = None):
        super().__init__(message=message, code="CONFLICT", status_code=409, details=details)


class MLException(AppException):
    """Machine learning processing or pipeline execution failure."""

    def __init__(self, message: str = "Machine learning operation failed", details: Dict[str, Any] | None = None):
        super().__init__(message=message, code="ML_OPERATION_ERROR", status_code=400, details=details)
