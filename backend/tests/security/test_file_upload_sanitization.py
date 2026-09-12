"""Security validation tests for path traversal protection and upload sanitization."""

import pytest

from app.core.exceptions import AppException
from app.core.sanitizer import sanitize_filename, validate_file_upload, validate_secure_path


def test_sanitize_filename_removes_directory_traversal():
    """Verify that path traversal sequences are cleanly stripped."""
    assert sanitize_filename("../../etc/passwd") == "passwd"
    assert sanitize_filename("..\\..\\Windows\\System32\\cmd.exe") == "cmd.exe"
    assert sanitize_filename("/var/log/secret.csv") == "secret.csv"
    assert sanitize_filename("safe_dataset.csv") == "safe_dataset.csv"


def test_sanitize_filename_handles_illegal_characters():
    """Verify that illegal control characters and spaces are safely normalized."""
    assert sanitize_filename("my dataset (v1.0) #final.csv") == "my_dataset_v1.0_final.csv"
    assert sanitize_filename(".hidden_dataset.csv") == "dataset_hidden_dataset.csv"
    assert sanitize_filename("") == "unnamed_dataset.csv"


def test_validate_secure_path_prevents_directory_escape(tmp_path):
    """Verify that paths resolving outside the storage root are blocked."""
    base_dir = str(tmp_path / "storage")
    import os

    os.makedirs(base_dir, exist_ok=True)

    # Valid internal path
    valid_path = validate_secure_path(base_dir, "datasets/data.csv")
    assert valid_path.startswith(base_dir)

    # Path traversal attack
    with pytest.raises(AppException) as exc:
        validate_secure_path(base_dir, "../../../etc/shadow")
    assert exc.value.code == "PATH_TRAVERSAL_DETECTED"


def test_validate_file_upload_enforces_extension_whitelist():
    """Verify that forbidden executable extensions are rejected."""
    with pytest.raises(AppException) as exc:
        validate_file_upload(filename="malicious.exe", size_bytes=1024, max_size_bytes=100000)
    assert exc.value.code == "INVALID_FILE_EXTENSION"

    with pytest.raises(AppException) as exc:
        validate_file_upload(filename="script.sh", size_bytes=1024, max_size_bytes=100000)
    assert exc.value.code == "INVALID_FILE_EXTENSION"


def test_validate_file_upload_enforces_size_limits():
    """Verify that empty files and oversized files are rejected."""
    # Empty file
    with pytest.raises(AppException) as exc:
        validate_file_upload(filename="empty.csv", size_bytes=0, max_size_bytes=100000)
    assert exc.value.code == "EMPTY_FILE_UPLOAD"

    # Oversized file
    with pytest.raises(AppException) as exc:
        validate_file_upload(filename="huge.csv", size_bytes=200000, max_size_bytes=100000)
    assert exc.value.code == "FILE_SIZE_EXCEEDED"
    assert exc.value.status_code == 413
