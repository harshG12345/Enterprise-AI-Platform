"""Standardized enterprise API response envelopes."""

from typing import Any, Dict, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Dict[str, Any] | None = None


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T | None = None
    message: str = "Operation completed successfully"
    request_id: str | None = None


class APIErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail
    request_id: str | None = None


def success_response(
    data: Any = None,
    message: str = "Operation completed successfully",
    request_id: str | None = None,
) -> Dict[str, Any]:
    """Helper to return consistent JSON payload."""
    return {
        "success": True,
        "data": data,
        "message": message,
        "request_id": request_id,
    }


def error_response(
    code: str,
    message: str,
    status_code: int = 400,
    details: Dict[str, Any] | None = None,
    request_id: str | None = None,
) -> Dict[str, Any]:
    """Helper to return consistent error JSON payload."""
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
        },
        "request_id": request_id,
    }
