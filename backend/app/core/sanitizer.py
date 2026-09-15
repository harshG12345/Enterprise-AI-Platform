"""Security Sanitizer for Path Traversal Protection and File Upload Validation."""

import os
import re
from typing import Optional, Set

from app.core.exceptions import AppException

# Allowed tabular dataset extensions
ALLOWED_EXTENSIONS: Set[str] = {".csv", ".xlsx", ".xls", ".parquet", ".json"}

# Allowed MIME types
ALLOWED_MIME_TYPES: Set[str] = {
    "text/csv",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/json",
    "application/octet-stream",
    "text/plain",
}


def sanitize_filename(raw_filename: str) -> str:
    """Sanitize uploaded filename to eliminate path traversal, control chars, and illegal symbols.

    Guarantees that the returned string is purely a filename with no directory components.
    """
    if not raw_filename or not raw_filename.strip():
        return "unnamed_dataset.csv"

    # 1. Strip directory components and null bytes
    cleaned = raw_filename.replace("\x00", "").strip()
    cleaned = cleaned.replace("\\", "/")
    cleaned = os.path.basename(cleaned)

    # 2. Prevent hidden dot-files
    if cleaned.startswith("."):
        cleaned = f"dataset_{cleaned.lstrip('.')}"

    # 3. Whitelist allowed characters: alphanumeric, underscores, hyphens, and dots
    sanitized = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", cleaned)

    # 4. Collapse multiple dots and underscores
    sanitized = re.sub(r"\.{2,}", ".", sanitized)
    sanitized = re.sub(r"_{2,}", "_", sanitized)

    if not sanitized or sanitized == ".":
        return "unnamed_dataset.csv"

    return sanitized


def validate_secure_path(base_directory: str, target_path: str) -> str:
    """Validate that target_path resolves strictly within base_directory, preventing directory traversal.

    Returns the canonical absolute path or raises an AppException.
    """
    # Reject null bytes immediately
    if "\x00" in target_path or "\x00" in base_directory:
        raise AppException(
            status_code=400,
            code="PATH_TRAVERSAL_DETECTED",
            message="Null byte detected in file path specification.",
        )

    base_abs = os.path.abspath(os.path.realpath(base_directory))
    target_abs = os.path.abspath(os.path.realpath(os.path.join(base_directory, target_path)))

    # Ensure resolved path is a child of base_directory
    if not target_abs.startswith(base_abs + os.sep) and target_abs != base_abs:
        raise AppException(
            status_code=400,
            code="PATH_TRAVERSAL_DETECTED",
            message="Access denied: Target path resolves outside the designated storage root.",
        )

    return target_abs


def validate_file_upload(
    filename: str,
    size_bytes: int,
    max_size_bytes: int,
    content_type: Optional[str] = None,
) -> str:
    """Validate tabular file upload size, extension whitelist, and sanitize filename.

    Returns the sanitized safe filename.
    """
    # 1. Check for null byte injection
    if "\x00" in filename:
        raise AppException(
            status_code=400,
            code="MALICIOUS_INPUT_DETECTED",
            message="Null byte found in filename.",
        )

    # 2. Extract and validate file extension
    _, ext = os.path.splitext(filename.lower())
    if ext not in ALLOWED_EXTENSIONS:
        raise AppException(
            status_code=400,
            code="INVALID_FILE_EXTENSION",
            message=f"Unsupported file format '{ext}'. Allowed extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    # 3. Validate file size constraints
    if size_bytes <= 0:
        raise AppException(
            status_code=400,
            code="EMPTY_FILE_UPLOAD",
            message="Uploaded file is empty (0 bytes).",
        )

    if size_bytes > max_size_bytes:
        max_mb = max_size_bytes / (1024 * 1024)
        curr_mb = size_bytes / (1024 * 1024)
        raise AppException(
            status_code=413,
            code="FILE_SIZE_EXCEEDED",
            message=f"Uploaded file size ({curr_mb:.2f} MB) exceeds maximum allowed limit ({max_mb:.0f} MB).",
        )

    return sanitize_filename(filename)
