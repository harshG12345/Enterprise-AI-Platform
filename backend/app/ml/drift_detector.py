"""Statistical Data Drift and Concept Drift Detection Engine.

Implements Kolmogorov-Smirnov (KS) test, Population Stability Index (PSI),
Wasserstein distance, Chi-Square test, and distribution histogram profiling.
"""

import logging
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

try:
    from scipy import stats

    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

logger = logging.getLogger(__name__)


class DriftDetector:
    """Enterprise statistical drift detection engine."""

    @staticmethod
    def calculate_psi(
        baseline: np.ndarray,
        current: np.ndarray,
        num_bins: int = 10,
        is_categorical: bool = False,
        epsilon: float = 1e-4,
    ) -> Tuple[float, List[Dict[str, Any]]]:
        """Calculate Population Stability Index (PSI) and histogram bin proportions.

        PSI < 0.1: No significant distribution change (Stable)
        0.1 <= PSI < 0.2: Moderate shift (Warning)
        PSI >= 0.2: Significant drift detected (Alert)
        """
        if len(baseline) == 0 or len(current) == 0:
            return 0.0, []

        bins_data: List[Dict[str, Any]] = []

        if is_categorical:
            # Extract unique categories
            all_cats = list(set(baseline.tolist()).union(set(current.tolist())))
            n_base = len(baseline)
            n_curr = len(current)

            psi_val = 0.0
            for cat in sorted(all_cats):
                b_count = np.sum(baseline == cat)
                c_count = np.sum(current == cat)

                b_pct = (b_count / n_base) + epsilon
                c_pct = (c_count / n_curr) + epsilon

                sub_psi = (c_pct - b_pct) * np.log(c_pct / b_pct)
                psi_val += float(sub_psi)

                bins_data.append(
                    {
                        "bin_label": str(cat),
                        "baseline_pct": round(float(b_count / n_base * 100.0), 2),
                        "current_pct": round(float(c_count / n_curr * 100.0), 2),
                    }
                )

            return round(max(0.0, float(psi_val)), 4), bins_data

        else:
            # Continuous Numerical Feature Binning
            clean_base = baseline[np.isfinite(baseline)]
            clean_curr = current[np.isfinite(current)]

            if len(clean_base) == 0 or len(clean_curr) == 0:
                return 0.0, []

            # Determine quantiles on baseline data
            quantiles = np.linspace(0, 100, num_bins + 1)
            bin_edges = np.percentile(clean_base, quantiles)
            # Ensure unique edges
            bin_edges = np.unique(bin_edges)
            if len(bin_edges) < 2:
                bin_edges = np.array([np.min(clean_base) - 1e-3, np.max(clean_base) + 1e-3])

            n_base = len(clean_base)
            n_curr = len(clean_curr)

            psi_val = 0.0
            for i in range(len(bin_edges) - 1):
                low = bin_edges[i]
                high = bin_edges[i + 1]

                if i == 0:
                    b_count = np.sum((clean_base >= low) & (clean_base <= high))
                    c_count = np.sum((clean_curr >= low) & (clean_curr <= high))
                else:
                    b_count = np.sum((clean_base > low) & (clean_base <= high))
                    c_count = np.sum((clean_curr > low) & (clean_curr <= high))

                b_pct = (b_count / n_base) + epsilon
                c_pct = (c_count / n_curr) + epsilon

                sub_psi = (c_pct - b_pct) * np.log(c_pct / b_pct)
                psi_val += float(sub_psi)

                label = f"{round(float(low), 2)} - {round(float(high), 2)}"
                bins_data.append(
                    {
                        "bin_label": label,
                        "baseline_pct": round(float(b_count / n_base * 100.0), 2),
                        "current_pct": round(float(c_count / n_curr * 100.0), 2),
                    }
                )

            if n_curr < 15 or n_base < 15:
                psi_val = 0.0

            return round(max(0.0, float(psi_val)), 4), bins_data

    @staticmethod
    def calculate_ks_test(baseline: np.ndarray, current: np.ndarray) -> Tuple[float, float, bool]:
        """Perform two-sample Kolmogorov-Smirnov test for continuous numerical features.

        Returns (statistic, p_value, is_drift_detected).
        """
        clean_base = baseline[np.isfinite(baseline)]
        clean_curr = current[np.isfinite(current)]

        if len(clean_base) < 2 or len(clean_curr) < 2:
            return 0.0, 1.0, False

        if HAS_SCIPY:
            res = stats.ks_2samp(clean_base, clean_curr)
            stat = float(res.statistic)
            pval = float(res.pvalue)
        else:
            # Fallback approximate empirical KS statistic
            stat = float(abs(np.mean(clean_base) - np.mean(clean_curr)) / (np.std(clean_base) + 1e-5))
            pval = 0.01 if stat > 0.3 else 0.5

        is_drift = pval < 0.05
        return round(stat, 4), round(pval, 6), is_drift

    @staticmethod
    def calculate_wasserstein(baseline: np.ndarray, current: np.ndarray) -> float:
        """Compute Wasserstein Distance (Earth Mover's Distance) between two numerical distributions."""
        clean_base = baseline[np.isfinite(baseline)]
        clean_curr = current[np.isfinite(current)]

        if len(clean_base) == 0 or len(clean_curr) == 0:
            return 0.0

        if HAS_SCIPY:
            dist = float(stats.wasserstein_distance(clean_base, clean_curr))
        else:
            dist = float(abs(np.mean(clean_base) - np.mean(clean_curr)))

        return round(dist, 4)

    @staticmethod
    def calculate_chi_square(baseline: np.ndarray, current: np.ndarray) -> Tuple[float, float, bool]:
        """Perform Chi-Square goodness-of-fit / independence test for categorical features."""
        all_cats = list(set(baseline.tolist()).union(set(current.tolist())))
        if len(all_cats) <= 1 or len(baseline) == 0 or len(current) == 0:
            return 0.0, 1.0, False

        b_counts = np.array([np.sum(baseline == cat) for cat in all_cats], dtype=float)
        c_counts = np.array([np.sum(current == cat) for cat in all_cats], dtype=float)

        # Re-scale baseline frequencies to match current sample size
        n_curr = len(current)
        n_base = len(baseline)
        expected = b_counts * (n_curr / n_base)
        expected = np.maximum(expected, 1e-3)

        if HAS_SCIPY:
            try:
                res = stats.chisquare(f_obs=c_counts, f_exp=expected)
                stat = float(res.statistic)
                pval = float(res.pvalue)
            except Exception:
                stat = 0.0
                pval = 1.0
        else:
            stat = float(np.sum((c_counts - expected) ** 2 / expected))
            pval = 0.01 if stat > 5.99 else 0.5

        is_drift = pval < 0.05
        return round(stat, 4), round(pval, 6), is_drift

    @classmethod
    def analyze_dataset_drift(
        cls,
        baseline_df: pd.DataFrame,
        current_df: pd.DataFrame,
        feature_names: List[str],
        alpha: float = 0.05,
        psi_warning_threshold: float = 0.1,
        psi_drift_threshold: float = 0.2,
    ) -> Dict[str, Any]:
        """Execute comprehensive multi-metric statistical drift diagnostics across all model features."""
        feature_reports: List[Dict[str, Any]] = []
        drifted_features_count = 0
        max_psi = 0.0

        for feat in feature_names:
            if feat not in baseline_df.columns or feat not in current_df.columns:
                continue

            base_col = baseline_df[feat].dropna().values
            curr_col = current_df[feat].dropna().values

            if len(base_col) == 0 or len(curr_col) == 0:
                continue

            # Determine if numerical or categorical
            is_numeric = pd.api.types.is_numeric_dtype(baseline_df[feat]) and not (
                len(np.unique(base_col)) <= 5 and base_col.dtype == object
            )

            if is_numeric:
                base_arr = np.asarray(base_col, dtype=np.float64)
                curr_arr = np.asarray(curr_col, dtype=np.float64)

                psi_score, histogram_bins = cls.calculate_psi(base_arr, curr_arr, is_categorical=False)
                ks_stat, ks_pval, ks_drift = cls.calculate_ks_test(base_arr, curr_arr)
                wass_dist = cls.calculate_wasserstein(base_arr, curr_arr)

                # Flag feature as drifted if PSI >= 0.2 or KS test rejects null hypothesis with sufficient sample size
                is_feature_drifted = bool(psi_score >= psi_drift_threshold or (ks_pval < alpha and len(curr_arr) >= 15))

                feature_reports.append(
                    {
                        "feature_name": feat,
                        "feature_type": "numerical",
                        "drift_detected": is_feature_drifted,
                        "psi_score": psi_score,
                        "primary_test": "Kolmogorov-Smirnov",
                        "test_statistic": ks_stat,
                        "p_value": ks_pval,
                        "wasserstein_distance": wass_dist,
                        "histogram_bins": histogram_bins,
                        "baseline_stats": {
                            "mean": round(float(np.mean(base_arr)), 4),
                            "std": round(float(np.std(base_arr)), 4),
                            "min": round(float(np.min(base_arr)), 4),
                            "max": round(float(np.max(base_arr)), 4),
                        },
                        "current_stats": {
                            "mean": round(float(np.mean(curr_arr)), 4),
                            "std": round(float(np.std(curr_arr)), 4),
                            "min": round(float(np.min(curr_arr)), 4),
                            "max": round(float(np.max(curr_arr)), 4),
                        },
                    }
                )
            else:
                # Categorical Feature Drift
                base_arr = np.asarray(base_col, dtype=str)
                curr_arr = np.asarray(curr_col, dtype=str)

                psi_score, histogram_bins = cls.calculate_psi(base_arr, curr_arr, is_categorical=True)
                chi2_stat, chi2_pval, chi2_drift = cls.calculate_chi_square(base_arr, curr_arr)

                is_feature_drifted = bool(
                    psi_score >= psi_drift_threshold or (chi2_pval < alpha and len(curr_arr) >= 15)
                )

                feature_reports.append(
                    {
                        "feature_name": feat,
                        "feature_type": "categorical",
                        "drift_detected": is_feature_drifted,
                        "psi_score": psi_score,
                        "primary_test": "Chi-Square",
                        "test_statistic": chi2_stat,
                        "p_value": chi2_pval,
                        "wasserstein_distance": None,
                        "histogram_bins": histogram_bins,
                        "baseline_stats": {"unique_categories": len(np.unique(base_arr))},
                        "current_stats": {"unique_categories": len(np.unique(curr_arr))},
                    }
                )

            if is_feature_drifted:
                drifted_features_count += 1
            if psi_score > max_psi:
                max_psi = psi_score

        # Determine overall Model System Health Status
        total_feats = len(feature_reports)
        drift_percentage = round((drifted_features_count / total_feats * 100.0), 1) if total_feats > 0 else 0.0

        if max_psi >= psi_drift_threshold or drift_percentage >= 30.0:
            health_status = "DRIFT_DETECTED"
        elif max_psi >= psi_warning_threshold or drift_percentage > 0:
            health_status = "WARNING"
        else:
            health_status = "HEALTHY"

        return {
            "health_status": health_status,
            "drift_score": round(max_psi, 4),
            "drift_percentage": drift_percentage,
            "total_features": total_feats,
            "drifted_features_count": drifted_features_count,
            "max_psi": round(max_psi, 4),
            "feature_reports": feature_reports,
            "baseline_sample_count": len(baseline_df),
            "current_sample_count": len(current_df),
        }
