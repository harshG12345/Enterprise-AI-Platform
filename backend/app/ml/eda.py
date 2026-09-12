import math
from typing import List, Tuple

import numpy as np
import pandas as pd

from app.schemas.eda import (
    BoxPlotData,
    CategoricalColumnStats,
    CategoryFrequency,
    ColumnMissingSummary,
    CorrelationCell,
    CorrelationMatrix,
    DataHealthWarning,
    DatasetOverviewStats,
    EDAResponse,
    HistogramBin,
    NumericalColumnStats,
)


class EDAEngine:
    """Statistical Exploratory Data Analysis engine for tabular datasets."""

    @staticmethod
    def _format_memory(num_bytes: int) -> str:
        """Convert byte count to human-readable string."""
        for unit in ["B", "KB", "MB", "GB"]:
            if abs(num_bytes) < 1024.0:
                return f"{num_bytes:.2f} {unit}"
            num_bytes /= 1024.0
        return f"{num_bytes:.2f} TB"

    @classmethod
    def analyze_dataset(
        cls,
        df: pd.DataFrame,
        dataset_id: str,
        dataset_name: str,
    ) -> EDAResponse:
        """Perform comprehensive exploratory data analysis on a pandas DataFrame."""
        total_rows = int(len(df))
        total_columns = int(len(df.columns))
        total_cells = total_rows * total_columns if total_rows > 0 else 0

        # Memory usage
        mem_bytes = int(df.memory_usage(deep=True).sum())
        mem_human = cls._format_memory(mem_bytes)

        # Duplicates
        dup_rows = int(df.duplicated().sum()) if total_rows > 0 else 0
        dup_pct = round((dup_rows / total_rows * 100.0), 2) if total_rows > 0 else 0.0

        # Total missing cells
        missing_matrix = df.isna()
        total_missing = int(missing_matrix.sum().sum())
        missing_pct = round((total_missing / total_cells * 100.0), 2) if total_cells > 0 else 0.0

        # Missing summary by column
        missing_summary: List[ColumnMissingSummary] = []
        for col in df.columns:
            col_missing = int(missing_matrix[col].sum())
            col_missing_pct = round((col_missing / total_rows * 100.0), 2) if total_rows > 0 else 0.0
            col_valid = total_rows - col_missing
            col_valid_pct = round(100.0 - col_missing_pct, 2)
            missing_summary.append(
                ColumnMissingSummary(
                    column_name=str(col),
                    data_type=str(df[col].dtype),
                    missing_count=col_missing,
                    missing_percentage=col_missing_pct,
                    valid_count=col_valid,
                    valid_percentage=col_valid_pct,
                )
            )

        # Segregate columns by inferred type
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        cat_cols = df.select_dtypes(include=["object", "category", "string", "bool"]).columns.tolist()
        datetime_cols = df.select_dtypes(include=["datetime", "datetimetz"]).columns.tolist()
        bool_cols = df.select_dtypes(include=["bool"]).columns.tolist()

        # Generate overview statistics
        overview = DatasetOverviewStats(
            total_rows=total_rows,
            total_columns=total_columns,
            memory_usage_bytes=mem_bytes,
            memory_usage_human=mem_human,
            duplicate_rows_count=dup_rows,
            duplicate_rows_percentage=dup_pct,
            total_cells=total_cells,
            total_missing_cells=total_missing,
            missing_cells_percentage=missing_pct,
            numerical_columns_count=len(num_cols),
            categorical_columns_count=len(cat_cols),
            datetime_columns_count=len(datetime_cols),
            boolean_columns_count=len(bool_cols),
        )

        # Health warnings tracker
        warnings: List[DataHealthWarning] = []

        if dup_rows > 0:
            warnings.append(
                DataHealthWarning(
                    code="DUPLICATE_ROWS",
                    level="info" if dup_pct < 5.0 else "warning",
                    message=f"Dataset contains {dup_rows:,} duplicate rows ({dup_pct:.1f}%).",
                    suggestion="Consider deduplicating the dataset during preprocessing if duplicate instances are redundant.",
                )
            )

        # Analyze Numerical Features
        numerical_features: List[NumericalColumnStats] = []
        for col in num_cols:
            series = df[col].dropna()
            if len(series) == 0:
                continue

            stats_item, col_warnings = cls._analyze_numerical_column(str(col), series, total_rows)
            numerical_features.append(stats_item)
            warnings.extend(col_warnings)

        # Analyze Categorical Features
        categorical_features: List[CategoricalColumnStats] = []
        for col in cat_cols:
            series = df[col].dropna()
            stats_item, col_warnings = cls._analyze_categorical_column(str(col), series, total_rows)
            categorical_features.append(stats_item)
            warnings.extend(col_warnings)

        # Missingness warnings
        for m in missing_summary:
            if m.missing_percentage >= 50.0:
                warnings.append(
                    DataHealthWarning(
                        code="HIGH_MISSING",
                        level="critical",
                        column=m.column_name,
                        message=f"Column '{m.column_name}' has {m.missing_percentage:.1f}% missing values.",
                        suggestion="Consider dropping this feature or applying robust domain-specific imputation.",
                    )
                )
            elif m.missing_percentage >= 20.0:
                warnings.append(
                    DataHealthWarning(
                        code="HIGH_MISSING",
                        level="warning",
                        column=m.column_name,
                        message=f"Column '{m.column_name}' has {m.missing_percentage:.1f}% missing values.",
                        suggestion="Imputation (median, mode, or KNN/Iterative) is recommended before training.",
                    )
                )

        # Correlation Matrices (Pearson and Spearman)
        pearson_corr = None
        spearman_corr = None

        if len(num_cols) >= 2:
            num_df = df[num_cols]
            pearson_corr = cls._compute_correlation_matrix(num_df, "pearson")
            spearman_corr = cls._compute_correlation_matrix(num_df, "spearman")

            # Check for high multicollinearity (|r| >= 0.85)
            if pearson_corr:
                for pair in pearson_corr.pairwise_pairs:
                    if abs(pair.correlation) >= 0.85:
                        warnings.append(
                            DataHealthWarning(
                                code="HIGH_COLLINEARITY",
                                level="warning",
                                columns=[pair.feature_x, pair.feature_y],
                                message=f"Strong linear correlation (r = {pair.correlation:.2f}) between '{pair.feature_x}' and '{pair.feature_y}'.",
                                suggestion="High multicollinearity may inflate regression variance. Consider feature selection or PCA.",
                            )
                        )

        return EDAResponse(
            dataset_id=dataset_id,
            dataset_name=dataset_name,
            overview=overview,
            missing_summary=missing_summary,
            numerical_features=numerical_features,
            categorical_features=categorical_features,
            pearson_correlation=pearson_corr,
            spearman_correlation=spearman_corr,
            health_warnings=warnings,
        )

    @classmethod
    def _analyze_numerical_column(
        cls, col_name: str, series: pd.Series, total_rows: int
    ) -> Tuple[NumericalColumnStats, List[DataHealthWarning]]:
        """Compute complete descriptive statistics, histogram bins, boxplot, and outlier metrics."""
        warnings: List[DataHealthWarning] = []
        n = len(series)
        arr = series.to_numpy(dtype=float)

        mean_val = float(np.mean(arr))
        std_val = float(np.std(arr, ddof=1)) if n > 1 else 0.0
        var_val = float(np.var(arr, ddof=1)) if n > 1 else 0.0
        min_val = float(np.min(arr))
        max_val = float(np.max(arr))

        q25 = float(np.percentile(arr, 25))
        median_val = float(np.percentile(arr, 50))
        q75 = float(np.percentile(arr, 75))
        iqr_val = float(q75 - q25)

        # Skewness and Kurtosis
        try:
            skew_raw = series.skew()
            skew_val = float(skew_raw) if pd.notna(skew_raw) else 0.0
        except Exception:
            skew_val = 0.0

        try:
            kurt_raw = series.kurtosis()
            kurt_val = float(kurt_raw) if pd.notna(kurt_raw) else 0.0
        except Exception:
            kurt_val = 0.0

        if math.isnan(skew_val) or math.isinf(skew_val):
            skew_val = 0.0
        if math.isnan(kurt_val) or math.isinf(kurt_val):
            kurt_val = 0.0

        # Check for constant column (zero variance)
        if std_val == 0.0 or min_val == max_val:
            warnings.append(
                DataHealthWarning(
                    code="CONSTANT_COLUMN",
                    level="warning",
                    column=col_name,
                    message=f"Column '{col_name}' is constant (zero variance, constant value {min_val}).",
                    suggestion="Remove constant features as they provide zero predictive signal to machine learning models.",
                )
            )

        # Check for extreme skewness
        if abs(skew_val) >= 1.5:
            warnings.append(
                DataHealthWarning(
                    code="HIGH_SKEW",
                    level="info",
                    column=col_name,
                    message=f"Column '{col_name}' is heavily skewed (skewness = {skew_val:.2f}).",
                    suggestion="Apply PowerTransformer, Log1p, or Box-Cox transformation to normalize the distribution.",
                )
            )

        # Zeros and negatives
        zeros_count = int(np.sum(arr == 0))
        zeros_pct = round((zeros_count / total_rows * 100.0), 2) if total_rows > 0 else 0.0
        neg_count = int(np.sum(arr < 0))

        # Outlier Detection: IQR method
        lower_bound = q25 - 1.5 * iqr_val
        upper_bound = q75 + 1.5 * iqr_val
        iqr_outliers = arr[(arr < lower_bound) | (arr > upper_bound)]
        outliers_iqr_count = int(len(iqr_outliers))

        # Outlier Detection: Z-Score method (|z| > 3)
        if std_val > 0:
            z_scores = np.abs((arr - mean_val) / std_val)
            outliers_zscore_count = int(np.sum(z_scores > 3.0))
        else:
            outliers_zscore_count = 0

        # Whisker calculations for boxplot
        non_outliers = arr[(arr >= lower_bound) & (arr <= upper_bound)]
        lower_whisker = float(np.min(non_outliers)) if len(non_outliers) > 0 else min_val
        upper_whisker = float(np.max(non_outliers)) if len(non_outliers) > 0 else max_val

        # Outliers sample (up to 25 values)
        outliers_sample = [float(v) for v in iqr_outliers[:25]]

        boxplot = BoxPlotData(
            min=min_val,
            q1=q25,
            median=median_val,
            q3=q75,
            max=max_val,
            iqr=iqr_val,
            lower_whisker=lower_whisker,
            upper_whisker=upper_whisker,
            outliers_count=outliers_iqr_count,
            outliers_sample=outliers_sample,
        )

        # Histogram Generation
        histogram_bins: List[HistogramBin] = []
        if min_val < max_val:
            num_bins = min(20, max(5, int(math.ceil(math.sqrt(n)))))
            counts, bin_edges = np.histogram(arr, bins=num_bins)
            for i in range(len(counts)):
                b_start = float(bin_edges[i])
                b_end = float(bin_edges[i + 1])
                label = f"[{b_start:.1f} - {b_end:.1f}]"
                histogram_bins.append(
                    HistogramBin(
                        bin_start=b_start,
                        bin_end=b_end,
                        label=label,
                        count=int(counts[i]),
                    )
                )
        else:
            histogram_bins.append(
                HistogramBin(
                    bin_start=min_val,
                    bin_end=max_val,
                    label=f"[{min_val:.1f}]",
                    count=n,
                )
            )

        stats_item = NumericalColumnStats(
            column_name=col_name,
            count=n,
            mean=round(mean_val, 4),
            std=round(std_val, 4),
            variance=round(var_val, 4),
            min=round(min_val, 4),
            q25=round(q25, 4),
            median=round(median_val, 4),
            q75=round(q75, 4),
            max=round(max_val, 4),
            iqr=round(iqr_val, 4),
            skewness=round(skew_val, 4),
            kurtosis=round(kurt_val, 4),
            zeros_count=zeros_count,
            zeros_percentage=zeros_pct,
            negative_count=neg_count,
            outliers_iqr_count=outliers_iqr_count,
            outliers_zscore_count=outliers_zscore_count,
            histogram=histogram_bins,
            boxplot=boxplot,
        )

        return stats_item, warnings

    @classmethod
    def _analyze_categorical_column(
        cls, col_name: str, series: pd.Series, total_rows: int
    ) -> Tuple[CategoricalColumnStats, List[DataHealthWarning]]:
        """Compute frequency distribution, uniqueness, mode, and cardinality metrics."""
        warnings: List[DataHealthWarning] = []
        n = len(series)
        val_counts = series.value_counts()
        unique_cnt = int(len(val_counts))
        unique_ratio = round((unique_cnt / n), 4) if n > 0 else 0.0

        top_val = str(val_counts.index[0]) if unique_cnt > 0 else None
        top_freq = int(val_counts.iloc[0]) if unique_cnt > 0 else None
        top_pct = round((top_freq / n * 100.0), 2) if (top_freq and n > 0) else None

        # Build top 12 category frequencies
        frequencies: List[CategoryFrequency] = []
        top_n = min(12, unique_cnt)
        accounted_count = 0

        for i in range(top_n):
            val = str(val_counts.index[i])
            cnt = int(val_counts.iloc[i])
            pct = round((cnt / n * 100.0), 2) if n > 0 else 0.0
            accounted_count += cnt
            frequencies.append(CategoryFrequency(value=val, count=cnt, percentage=pct))

        # If there are more categories, group remainder into "Other"
        if unique_cnt > top_n:
            other_cnt = n - accounted_count
            if other_cnt > 0:
                other_pct = round((other_cnt / n * 100.0), 2) if n > 0 else 0.0
                frequencies.append(
                    CategoryFrequency(
                        value=f"Other ({unique_cnt - top_n} categories)",
                        count=other_cnt,
                        percentage=other_pct,
                    )
                )

        is_high_card = unique_cnt > 50 and unique_ratio > 0.25

        if is_high_card:
            warnings.append(
                DataHealthWarning(
                    code="HIGH_CARDINALITY",
                    level="warning",
                    column=col_name,
                    message=f"Column '{col_name}' has high cardinality ({unique_cnt:,} unique values).",
                    suggestion="High cardinality features may cause one-hot encoding explosion. Consider Target Encoding or Frequency Encoding.",
                )
            )

        if unique_cnt == 1:
            warnings.append(
                DataHealthWarning(
                    code="CONSTANT_COLUMN",
                    level="warning",
                    column=col_name,
                    message=f"Column '{col_name}' has only 1 unique categorical value ('{top_val}').",
                    suggestion="Remove single-valued constant features prior to model training.",
                )
            )

        stats_item = CategoricalColumnStats(
            column_name=col_name,
            count=n,
            unique_count=unique_cnt,
            unique_ratio=unique_ratio,
            top_value=top_val,
            top_frequency=top_freq,
            top_percentage=top_pct,
            frequencies=frequencies,
            is_high_cardinality=is_high_card,
        )

        return stats_item, warnings

    @classmethod
    def _compute_correlation_matrix(cls, num_df: pd.DataFrame, method: str = "pearson") -> CorrelationMatrix | None:
        """Calculate pairwise correlation matrix and tabular list of pairs."""
        features = [str(c) for c in num_df.columns]
        if len(features) < 2:
            return None

        corr_df = num_df.corr(method=method)

        # Build 2D matrix
        matrix: List[List[float | None]] = []
        pairwise_pairs: List[CorrelationCell] = []

        for i, f1 in enumerate(features):
            row: List[float | None] = []
            for j, f2 in enumerate(features):
                val = corr_df.iloc[i, j]
                if pd.isna(val) or np.isinf(val):
                    val_float = None
                else:
                    val_float = round(float(val), 4)
                row.append(val_float)

                # Pairwise list (upper triangular only, excluding self)
                if j > i and val_float is not None:
                    pairwise_pairs.append(
                        CorrelationCell(
                            feature_x=f1,
                            feature_y=f2,
                            correlation=val_float,
                        )
                    )
            matrix.append(row)

        # Sort pairwise pairs by absolute correlation descending
        pairwise_pairs.sort(key=lambda c: abs(c.correlation), reverse=True)

        return CorrelationMatrix(
            method=method,
            features=features,
            matrix=matrix,
            pairwise_pairs=pairwise_pairs,
        )
