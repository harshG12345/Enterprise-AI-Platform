"""Dataset validation rules, MIME checks, and structural verification."""

import os
from typing import Set

import pandas as pd

from app.config.settings import get_settings
from app.core.exceptions import ValidationException

settings = get_settings()

ALLOWED_EXTENSIONS: Set[str] = {".csv", ".xlsx", ".xls"}


class DatasetValidator:
    """Validates raw tabular uploads for size, format, integrity, and column uniqueness."""

    @staticmethod
    def validate_file_metadata(filename: str, file_size: int) -> str:
        """Validate filename, extension, and file size boundaries."""
        if not filename or filename.strip() == "":
            raise ValidationException("Filename cannot be empty")

        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValidationException(
                f"Unsupported file format '{ext}'. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        if file_size <= 0:
            raise ValidationException("Uploaded file is empty (0 bytes)")

        if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
            max_mb = settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
            raise ValidationException(f"File size exceeds maximum allowable limit of {max_mb}MB")

        return ext

    @staticmethod
    def validate_raw_headers(header_line: str) -> None:
        """Validate raw header line before pandas auto-mangles duplicate column names."""
        if not header_line or header_line.strip() == "":
            raise ValidationException("Dataset header is empty")

        # Detect delimiter
        if "\t" in header_line:
            delimiter = "\t"
        elif ";" in header_line:
            delimiter = ";"
        else:
            delimiter = ","

        columns = [c.strip().strip('"').strip("'") for c in header_line.split(delimiter)]
        if len(columns) != len(set(columns)):
            duplicates = [c for c in set(columns) if columns.count(c) > 1]
            raise ValidationException(f"Dataset contains duplicate column names: {', '.join(duplicates)}")

    @staticmethod
    def validate_dataframe(df: pd.DataFrame) -> None:
        """Inspect loaded dataframe for empty contents and unnamed columns."""
        if df.empty:
            raise ValidationException("Dataset contains 0 rows of data")

        if len(df.columns) == 0:
            raise ValidationException("Dataset contains 0 columns")

        cols = [str(c).strip() for c in df.columns]

        # Check if all columns are unnamed
        if all("Unnamed:" in c for c in cols):
            raise ValidationException("Dataset header appears to be malformed or missing")
