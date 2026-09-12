"""Statistical Evaluation Engine computing Classification and Regression metrics."""

import math
from typing import List, Tuple

import numpy as np

from app.schemas.training import (
    ConfusionMatrixData,
    CurvePoint,
    EvaluationMetrics,
    ResidualPoint,
)


class ModelEvaluator:
    """Computes comprehensive evaluation metrics, confusion matrices, and ROC curves."""

    @classmethod
    def evaluate_classification(
        cls,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_prob: np.ndarray | None = None,
        labels: List[str] | None = None,
    ) -> Tuple[EvaluationMetrics, ConfusionMatrixData, List[CurvePoint]]:
        """Calculate complete classification performance metrics."""
        y_t = np.asarray(y_true).ravel()
        y_p = np.asarray(y_pred).ravel()
        n = len(y_t)

        unique_labels = sorted(list(set(y_t).union(set(y_p))))
        label_str = [str(l) for l in unique_labels] if not labels else labels
        label_to_idx = {l: i for i, l in enumerate(unique_labels)}
        n_classes = len(unique_labels)

        # 1. Accuracy
        correct = np.sum(y_t == y_p)
        accuracy = float(correct / n) if n > 0 else 0.0

        # 2. Confusion Matrix
        cm = [[0 for _ in range(n_classes)] for _ in range(n_classes)]
        for t, p in zip(y_t, y_p):
            t_idx = label_to_idx.get(t, 0)
            p_idx = label_to_idx.get(p, 0)
            cm[t_idx][p_idx] += 1

        # Normalized confusion matrix
        cm_norm = []
        for row in cm:
            row_sum = sum(row)
            cm_norm.append([round(c / row_sum, 4) if row_sum > 0 else 0.0 for c in row])

        # 3. Per-class Precision, Recall, F1
        precisions = []
        recalls = []
        f1s = []
        weights = []

        for i in range(n_classes):
            tp = cm[i][i]
            fp = sum(cm[r][i] for r in range(n_classes)) - tp
            fn = sum(cm[i][c] for c in range(n_classes)) - tp
            support = sum(cm[i])

            prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

            precisions.append(prec)
            recalls.append(rec)
            f1s.append(f1)
            weights.append(support)

        total_weight = sum(weights)
        if total_weight > 0:
            weighted_prec = float(sum(p * w for p, w in zip(precisions, weights)) / total_weight)
            weighted_rec = float(sum(r * w for r, w in zip(recalls, weights)) / total_weight)
            weighted_f1 = float(sum(f * w for f, w in zip(f1s, weights)) / total_weight)
        else:
            weighted_prec = float(np.mean(precisions)) if precisions else 0.0
            weighted_rec = float(np.mean(recalls)) if recalls else 0.0
            weighted_f1 = float(np.mean(f1s)) if f1s else 0.0

        # 4. ROC-AUC & Curve (Binary or Multiclass)
        roc_auc = None
        roc_curve: List[CurvePoint] = []

        if y_prob is not None and n_classes == 2:
            try:
                # Binary ROC Curve calculation
                scores = y_prob[:, 1] if y_prob.ndim == 2 and y_prob.shape[1] > 1 else y_prob.ravel()
                pos_label = unique_labels[1] if len(unique_labels) > 1 else unique_labels[0]
                y_bin = (y_t == pos_label).astype(int)

                # Generate threshold points
                thresholds = np.linspace(0.0, 1.0, 21)
                tpr_list = []
                fpr_list = []

                n_pos = np.sum(y_bin == 1)
                n_neg = np.sum(y_bin == 0)

                for th in thresholds:
                    preds = (scores >= th).astype(int)
                    tp = np.sum((preds == 1) & (y_bin == 1))
                    fp = np.sum((preds == 1) & (y_bin == 0))
                    tpr = tp / n_pos if n_pos > 0 else 0.0
                    fpr = fp / n_neg if n_neg > 0 else 0.0
                    fpr_list.append(fpr)
                    tpr_list.append(tpr)
                    roc_curve.append(
                        CurvePoint(x=round(float(fpr), 4), y=round(float(tpr), 4), threshold=round(float(th), 4))
                    )

                # Sort by FPR for trapezoid integration
                sorted_pairs = sorted(zip(fpr_list, tpr_list))
                sorted_fpr, sorted_tpr = zip(*sorted_pairs)
                # Trapezoidal AUC with NumPy 2.0+ and 1.x fallback
                trapz_fn = getattr(np, "trapezoid", getattr(np, "trapz", None))
                if trapz_fn:
                    roc_auc = float(trapz_fn(sorted_tpr, sorted_fpr))
                else:
                    roc_auc = float(
                        sum(
                            (sorted_fpr[i] - sorted_fpr[i - 1]) * (sorted_tpr[i] + sorted_tpr[i - 1]) / 2.0
                            for i in range(1, len(sorted_fpr))
                        )
                    )
                if roc_auc < 0:
                    roc_auc = abs(roc_auc)
                if roc_auc > 1.0:
                    roc_auc = 1.0
            except Exception:
                roc_auc = None

        if not roc_curve:
            # Baseline reference curve
            for p in np.linspace(0.0, 1.0, 11):
                roc_curve.append(CurvePoint(x=round(float(p), 2), y=round(float(p), 2)))

        metrics = EvaluationMetrics(
            accuracy=round(accuracy, 4),
            precision=round(weighted_prec, 4),
            recall=round(weighted_rec, 4),
            f1_score=round(weighted_f1, 4),
            roc_auc=round(roc_auc, 4) if roc_auc is not None else None,
        )

        cm_data = ConfusionMatrixData(
            labels=label_str,
            matrix=cm,
            normalized_matrix=cm_norm,
        )

        return metrics, cm_data, roc_curve

    @classmethod
    def evaluate_regression(
        cls,
        y_true: np.ndarray,
        y_pred: np.ndarray,
    ) -> Tuple[EvaluationMetrics, List[ResidualPoint]]:
        """Calculate regression metrics: MSE, RMSE, MAE, R-squared, and residuals."""
        y_t = np.asarray(y_true, dtype=float).ravel()
        y_p = np.asarray(y_pred, dtype=float).ravel()
        n = len(y_t)

        if n == 0:
            return EvaluationMetrics(), []

        residuals = y_t - y_p
        mse = float(np.mean(residuals**2))
        rmse = float(math.sqrt(mse))
        mae = float(np.mean(np.abs(residuals)))

        # R-squared: 1 - SS_res / SS_tot
        y_mean = float(np.mean(y_t))
        ss_tot = float(np.sum((y_t - y_mean) ** 2))
        ss_res = float(np.sum(residuals**2))

        if ss_tot > 1e-8:
            r2 = float(1.0 - (ss_res / ss_tot))
        else:
            r2 = 0.0

        explained_var = float(1.0 - (np.var(residuals) / np.var(y_t))) if np.var(y_t) > 1e-8 else 0.0

        metrics = EvaluationMetrics(
            mse=round(mse, 4),
            rmse=round(rmse, 4),
            mae=round(mae, 4),
            r2_score=round(r2, 4),
            explained_variance=round(explained_var, 4),
        )

        # Residuals sample (first 50 points)
        residuals_sample = []
        sample_limit = min(50, n)
        for i in range(sample_limit):
            residuals_sample.append(
                ResidualPoint(
                    actual=round(float(y_t[i]), 4),
                    predicted=round(float(y_p[i]), 4),
                    residual=round(float(residuals[i]), 4),
                )
            )

        return metrics, residuals_sample
