"""Custom Scikit-Learn compatible transformers with strict Zero Data Leakage guarantees."""

from typing import Any, Dict, List, Tuple, Union

import numpy as np
import pandas as pd


class BaseCustomTransformer:
    """Base class providing fit and transform methods compatible with Scikit-learn pipelines."""

    def fit(self, X: Any, y: Any = None):
        return self

    def transform(self, X: Any) -> Any:
        return X

    def fit_transform(self, X: Any, y: Any = None) -> Any:
        return self.fit(X, y).transform(X)


class FrequencyEncoder(BaseCustomTransformer):
    """Encodes categorical strings into normalized frequency values computed strictly on train split."""

    def __init__(self, handle_unknown: float = 0.0):
        self.handle_unknown = handle_unknown
        self.frequencies_: Dict[str, Dict[Any, float]] = {}
        self.columns_: List[str] = []

    def fit(self, X: Union[pd.DataFrame, np.ndarray], y: Any = None):
        df = pd.DataFrame(X)
        self.columns_ = [str(c) for c in df.columns]
        self.frequencies_ = {}

        for col in df.columns:
            series = df[col].dropna()
            n = len(series)
            if n > 0:
                val_counts = series.value_counts(normalize=True).to_dict()
                self.frequencies_[str(col)] = val_counts
            else:
                self.frequencies_[str(col)] = {}
        return self

    def transform(self, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        df = pd.DataFrame(X, columns=self.columns_ if hasattr(X, "columns") else None)
        out_df = df.copy()

        for col in df.columns:
            col_key = str(col)
            mapping = self.frequencies_.get(col_key, {})
            out_df[col] = df[col].map(mapping).fillna(self.handle_unknown).astype(float)

        return out_df.to_numpy()


class TopKCategoryGrouper(BaseCustomTransformer):
    """Keeps top K most frequent categories from training split and groups remaining as 'Other'."""

    def __init__(self, top_k: int = 20, other_label: str = "Other"):
        self.top_k = top_k
        self.other_label = other_label
        self.top_categories_: Dict[str, List[Any]] = {}

    def fit(self, X: Union[pd.DataFrame, np.ndarray], y: Any = None):
        df = pd.DataFrame(X)
        self.top_categories_ = {}

        for col in df.columns:
            val_counts = df[col].dropna().value_counts()
            top_cats = val_counts.head(self.top_k).index.tolist()
            self.top_categories_[str(col)] = top_cats
        return self

    def transform(self, X: Union[pd.DataFrame, np.ndarray]) -> pd.DataFrame:
        df = pd.DataFrame(X)
        out_df = df.copy()

        for col in df.columns:
            top_cats = set(self.top_categories_.get(str(col), []))
            out_df[col] = df[col].apply(lambda v: v if v in top_cats or pd.isna(v) else self.other_label)

        return out_df


class OutlierClipper(BaseCustomTransformer):
    """Clips numerical values to upper and lower percentiles fitted strictly on training data."""

    def __init__(self, lower_percentile: float = 0.01, upper_percentile: float = 0.99):
        self.lower_percentile = lower_percentile
        self.upper_percentile = upper_percentile
        self.bounds_: Dict[int, Tuple[float, float]] = {}

    def fit(self, X: Union[pd.DataFrame, np.ndarray], y: Any = None):
        arr = np.asarray(X, dtype=float)
        self.bounds_ = {}

        for col_idx in range(arr.shape[1]):
            col_vals = arr[:, col_idx]
            valid_vals = col_vals[~np.isnan(col_vals)]
            if len(valid_vals) > 0:
                low = float(np.percentile(valid_vals, self.lower_percentile * 100))
                high = float(np.percentile(valid_vals, self.upper_percentile * 100))
                self.bounds_[col_idx] = (low, high)
            else:
                self.bounds_[col_idx] = (-np.inf, np.inf)
        return self

    def transform(self, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        arr = np.asarray(X, dtype=float).copy()
        for col_idx in range(arr.shape[1]):
            if col_idx in self.bounds_:
                low, high = self.bounds_[col_idx]
                arr[:, col_idx] = np.clip(arr[:, col_idx], low, high)
        return arr


class CyclicalDatetimeEncoder(BaseCustomTransformer):
    """Extracts calendar/clock components and generates sine/cosine cyclical representations."""

    def __init__(
        self,
        extracted_parts: List[str] | None = None,
        cyclical_encoding: bool = True,
    ):
        self.extracted_parts = extracted_parts or ["year", "month", "day", "dayofweek", "is_weekend"]
        self.cyclical_encoding = cyclical_encoding
        self.output_feature_names_: List[str] = []

    def fit(self, X: Any, y: Any = None):
        # Determine output feature names from parts
        names: List[str] = []
        for part in self.extracted_parts:
            names.append(part)
            if self.cyclical_encoding and part in ["month", "dayofweek", "hour"]:
                names.append(f"{part}_sin")
                names.append(f"{part}_cos")
        self.output_feature_names_ = names
        return self

    def transform(self, X: Union[pd.Series, pd.DataFrame, np.ndarray, List[Any]]) -> np.ndarray:
        if isinstance(X, pd.DataFrame):
            series = X.iloc[:, 0]
        elif isinstance(X, pd.Series):
            series = X
        else:
            series = pd.Series(X.ravel() if hasattr(X, "ravel") else X)

        dt_series = pd.to_datetime(series, errors="coerce")
        features: List[np.ndarray] = []

        for part in self.extracted_parts:
            if part == "year":
                vals = dt_series.dt.year.fillna(2000).to_numpy(dtype=float)
                features.append(vals)
            elif part == "month":
                vals = dt_series.dt.month.fillna(1).to_numpy(dtype=float)
                features.append(vals)
                if self.cyclical_encoding:
                    sin_vals = np.sin(2 * np.pi * (vals - 1) / 12.0)
                    cos_vals = np.cos(2 * np.pi * (vals - 1) / 12.0)
                    features.append(sin_vals)
                    features.append(cos_vals)
            elif part == "day":
                vals = dt_series.dt.day.fillna(1).to_numpy(dtype=float)
                features.append(vals)
            elif part == "dayofweek":
                vals = dt_series.dt.dayofweek.fillna(0).to_numpy(dtype=float)
                features.append(vals)
                if self.cyclical_encoding:
                    sin_vals = np.sin(2 * np.pi * vals / 7.0)
                    cos_vals = np.cos(2 * np.pi * vals / 7.0)
                    features.append(sin_vals)
                    features.append(cos_vals)
            elif part == "hour":
                vals = dt_series.dt.hour.fillna(0).to_numpy(dtype=float)
                features.append(vals)
                if self.cyclical_encoding:
                    sin_vals = np.sin(2 * np.pi * vals / 24.0)
                    cos_vals = np.cos(2 * np.pi * vals / 24.0)
                    features.append(sin_vals)
                    features.append(cos_vals)
            elif part == "is_weekend":
                dow = dt_series.dt.dayofweek.fillna(0)
                vals = (dow >= 5).astype(float).to_numpy()
                features.append(vals)
            elif part == "quarter":
                vals = dt_series.dt.quarter.fillna(1).to_numpy(dtype=float)
                features.append(vals)

        if not features:
            return np.zeros((len(series), 0), dtype=float)

        return np.column_stack(features)


class TargetMeanEncoder(BaseCustomTransformer):
    """Smoothed Empirical Bayes Target Mean Encoder with zero leakage."""

    def __init__(self, smoothing: float = 10.0, cv_folds: int = 5):
        self.smoothing = smoothing
        self.cv_folds = cv_folds
        self.target_means_: Dict[str, Dict[Any, float]] = {}
        self.global_mean_: float = 0.0
        self.columns_: List[str] = []

    def fit(self, X: Union[pd.DataFrame, np.ndarray], y: Any):
        if y is None:
            raise ValueError("TargetMeanEncoder requires target variable 'y' to fit.")

        df = pd.DataFrame(X)
        self.columns_ = [str(c) for c in df.columns]
        y_arr = np.asarray(y, dtype=float)
        self.global_mean_ = float(np.nanmean(y_arr)) if len(y_arr) > 0 else 0.0
        self.target_means_ = {}

        for col in df.columns:
            col_series = df[col]
            temp_df = pd.DataFrame({"cat": col_series, "y": y_arr})
            grouped = temp_df.groupby("cat")["y"].agg(["count", "mean"])

            # Smoothed mean: (count * mean + m * global_mean) / (count + m)
            counts = grouped["count"]
            means = grouped["mean"]
            smoothed = (counts * means + self.smoothing * self.global_mean_) / (counts + self.smoothing)
            self.target_means_[str(col)] = smoothed.to_dict()

        return self

    def transform(self, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        df = pd.DataFrame(X, columns=self.columns_ if hasattr(X, "columns") else None)
        out_df = df.copy()

        for col in df.columns:
            col_key = str(col)
            mapping = self.target_means_.get(col_key, {})
            out_df[col] = df[col].map(mapping).fillna(self.global_mean_).astype(float)

        return out_df.to_numpy()
