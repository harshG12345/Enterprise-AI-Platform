"""Data loading and schema inference engine for CSV and Excel files."""

import math
import os
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

from app.core.exceptions import ValidationException
from app.ml.validator import DatasetValidator


class DataLoader:
    """Loads tabular datasets and extracts statistical schema metadata."""

    @staticmethod
    def load_file(file_path: str, nrows: int | None = None) -> pd.DataFrame:
        """Load CSV or Excel file into a Pandas DataFrame with header validation."""
        if not os.path.exists(file_path):
            raise ValidationException(f"Dataset file not found at path: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()

        # Validate raw CSV header for duplicate column names before pandas mangles them
        if ext == ".csv":
            try:
                with open(file_path, encoding="utf-8", errors="replace") as f:
                    header_line = f.readline()
                DatasetValidator.validate_raw_headers(header_line)
            except UnicodeDecodeError:
                pass  # Fallback to pandas decoding

        try:
            if ext == ".csv":
                df = pd.read_csv(file_path, nrows=nrows)
            elif ext in [".xlsx", ".xls"]:
                # Read header to check duplicate columns
                raw_df = pd.read_excel(file_path, nrows=0)
                raw_cols = [str(c) for c in raw_df.columns]
                if len(raw_cols) != len(set(raw_cols)):
                    duplicates = [c for c in set(raw_cols) if raw_cols.count(c) > 1]
                    raise ValidationException(f"Dataset contains duplicate column names: {', '.join(duplicates)}")
                df = pd.read_excel(file_path, nrows=nrows)
            else:
                raise ValidationException(f"Unsupported file extension: {ext}")
        except ValidationException:
            raise
        except Exception as e:
            raise ValidationException(f"Failed to parse tabular file: {str(e)}") from e

        # Validate DataFrame structure
        DatasetValidator.validate_dataframe(df)
        return df

    @staticmethod
    def infer_column_type(series: pd.Series) -> str:
        """Infer semantic data type of column."""
        dtype_str = str(series.dtype)
        if pd.api.types.is_bool_dtype(series):
            return "boolean"
        elif pd.api.types.is_numeric_dtype(series):
            return "numeric"
        elif pd.api.types.is_datetime64_any_dtype(series):
            return "datetime"
        else:
            non_null = series.dropna()
            if len(non_null) > 0:
                unique_ratio = non_null.nunique() / len(non_null)
                if unique_ratio < 0.2 or non_null.nunique() < 50:
                    return "categorical"
            return "text"

    @classmethod
    def extract_metadata(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """Compute structural schema metadata, memory footprint, and column summaries."""
        row_count, column_count = df.shape
        memory_bytes = int(df.memory_usage(deep=True).sum())

        columns_meta: List[Dict[str, Any]] = []
        for col_name in df.columns:
            series = df[col_name]
            missing_cnt = int(series.isna().sum())
            missing_pct = round((missing_cnt / row_count) * 100, 2) if row_count > 0 else 0.0
            unique_cnt = int(series.nunique(dropna=True))
            inferred_type = cls.infer_column_type(series)

            columns_meta.append(
                {
                    "name": str(col_name),
                    "dtype": str(series.dtype),
                    "inferred_type": inferred_type,
                    "missing_count": missing_cnt,
                    "missing_percentage": missing_pct,
                    "unique_count": unique_cnt,
                }
            )

        return {
            "row_count": row_count,
            "column_count": column_count,
            "memory_bytes": memory_bytes,
            "columns": columns_meta,
        }

    @staticmethod
    def sanitize_preview_value(val: Any) -> Any:
        """Sanitize NaN, Infinity, and NaT values for strict JSON serialization."""
        if pd.isna(val):
            return None
        elif isinstance(val, (float, np.floating)):
            if math.isnan(val) or math.isinf(val):
                return None
            return float(val)
        elif isinstance(val, (int, np.integer)):
            return int(val)
        elif isinstance(val, (pd.Timestamp, np.datetime64)):
            return str(val)
        return str(val)

    @classmethod
    def get_paginated_preview(
        cls,
        df: pd.DataFrame,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[Dict[str, Any]], int, int]:
        """Return sanitized rows and pagination metadata."""
        total_rows = len(df)
        total_pages = math.ceil(total_rows / page_size) if total_rows > 0 else 1

        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size

        page_slice = df.iloc[start_idx:end_idx]

        rows: List[Dict[str, Any]] = []
        for _, row in page_slice.iterrows():
            clean_row = {str(col): cls.sanitize_preview_value(row[col]) for col in df.columns}
            rows.append(clean_row)

        return rows, total_rows, total_pages
