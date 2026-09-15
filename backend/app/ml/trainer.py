"""Model Trainer & K-Fold Cross-Validation Engine."""

import time
from typing import Any, Dict, List

import numpy as np

from app.ml.evaluator import ModelEvaluator
from app.ml.models import (
    BaseMLModel,
    DecisionTreeModel,
    GradientBoostingModel,
    KNNModel,
    LinearRegressionModel,
    LogisticRegressionModel,
    RandomForestModel,
)
from app.schemas.training import (
    AlgorithmInfo,
    CrossValidationConfig,
    CVFoldResult,
    CVSummary,
    FeatureImportanceItem,
    ModelAlgorithm,
)


class ModelTrainer:
    """Instantiates models, executes K-Fold Cross Validation, and calculates full evaluation diagnostics."""

    ALGORITHMS: Dict[str, Dict[str, Any]] = {
        ModelAlgorithm.RANDOM_FOREST_CLASSIFIER.value: {
            "name": "Random Forest Classifier",
            "task_type": "classification",
            "class": RandomForestModel,
            "description": "Ensemble bagging of randomized decision trees with robust resistance to overfitting.",
            "default_hyperparameters": {
                "n_estimators": 25,
                "max_depth": 6,
                "min_samples_split": 2,
            },
            "hyperparameter_schema": {
                "n_estimators": {"type": "int", "min": 5, "max": 100, "default": 25},
                "max_depth": {"type": "int", "min": 2, "max": 20, "default": 6},
                "min_samples_split": {"type": "int", "min": 2, "max": 10, "default": 2},
            },
        },
        ModelAlgorithm.GRADIENT_BOOSTING_CLASSIFIER.value: {
            "name": "Gradient Boosting Classifier",
            "task_type": "classification",
            "class": GradientBoostingModel,
            "description": "Sequential boosting minimizing loss via stage-wise tree ensembles.",
            "default_hyperparameters": {
                "n_estimators": 20,
                "learning_rate": 0.1,
                "max_depth": 4,
            },
            "hyperparameter_schema": {
                "n_estimators": {"type": "int", "min": 5, "max": 100, "default": 20},
                "learning_rate": {"type": "float", "min": 0.01, "max": 0.5, "default": 0.1},
                "max_depth": {"type": "int", "min": 2, "max": 10, "default": 4},
            },
        },
        ModelAlgorithm.LOGISTIC_REGRESSION.value: {
            "name": "Logistic Regression",
            "task_type": "classification",
            "class": LogisticRegressionModel,
            "description": "Linear classifier optimizing log-loss with L2 weight regularization.",
            "default_hyperparameters": {
                "C": 1.0,
                "max_iter": 200,
                "lr": 0.05,
            },
            "hyperparameter_schema": {
                "C": {"type": "float", "min": 0.01, "max": 10.0, "default": 1.0},
                "max_iter": {"type": "int", "min": 50, "max": 500, "default": 200},
                "lr": {"type": "float", "min": 0.001, "max": 0.2, "default": 0.05},
            },
        },
        ModelAlgorithm.DECISION_TREE_CLASSIFIER.value: {
            "name": "Decision Tree Classifier",
            "task_type": "classification",
            "class": DecisionTreeModel,
            "description": "Non-parametric tree partition on Gini Impurity reduction.",
            "default_hyperparameters": {
                "max_depth": 6,
                "min_samples_split": 2,
            },
            "hyperparameter_schema": {
                "max_depth": {"type": "int", "min": 2, "max": 20, "default": 6},
                "min_samples_split": {"type": "int", "min": 2, "max": 10, "default": 2},
            },
        },
        ModelAlgorithm.KNN_CLASSIFIER.value: {
            "name": "K-Nearest Neighbors Classifier",
            "task_type": "classification",
            "class": KNNModel,
            "description": "Instance-based Euclidean distance classification.",
            "default_hyperparameters": {
                "n_neighbors": 5,
            },
            "hyperparameter_schema": {
                "n_neighbors": {"type": "int", "min": 1, "max": 25, "default": 5},
            },
        },
        # --- Regression Models ---
        ModelAlgorithm.RANDOM_FOREST_REGRESSOR.value: {
            "name": "Random Forest Regressor",
            "task_type": "regression",
            "class": RandomForestModel,
            "description": "Averaged ensemble of regression trees minimizing mean squared error.",
            "default_hyperparameters": {
                "n_estimators": 25,
                "max_depth": 6,
                "min_samples_split": 2,
            },
            "hyperparameter_schema": {
                "n_estimators": {"type": "int", "min": 5, "max": 100, "default": 25},
                "max_depth": {"type": "int", "min": 2, "max": 20, "default": 6},
                "min_samples_split": {"type": "int", "min": 2, "max": 10, "default": 2},
            },
        },
        ModelAlgorithm.GRADIENT_BOOSTING_REGRESSOR.value: {
            "name": "Gradient Boosting Regressor",
            "task_type": "regression",
            "class": GradientBoostingModel,
            "description": "Additive boosting fitting sequential tree estimators on negative MSE gradients.",
            "default_hyperparameters": {
                "n_estimators": 20,
                "learning_rate": 0.1,
                "max_depth": 4,
            },
            "hyperparameter_schema": {
                "n_estimators": {"type": "int", "min": 5, "max": 100, "default": 20},
                "learning_rate": {"type": "float", "min": 0.01, "max": 0.5, "default": 0.1},
                "max_depth": {"type": "int", "min": 2, "max": 10, "default": 4},
            },
        },
        ModelAlgorithm.LINEAR_REGRESSION.value: {
            "name": "Linear Regression (OLS)",
            "task_type": "regression",
            "class": LinearRegressionModel,
            "description": "Ordinary least squares estimating optimal continuous linear hyperplanes.",
            "default_hyperparameters": {
                "alpha": 0.0,
            },
            "hyperparameter_schema": {
                "alpha": {"type": "float", "min": 0.0, "max": 10.0, "default": 0.0},
            },
        },
        ModelAlgorithm.RIDGE_REGRESSION.value: {
            "name": "Ridge Regression (L2)",
            "task_type": "regression",
            "class": LinearRegressionModel,
            "description": "Linear regression with Tikhonov (L2) coefficient shrinkage.",
            "default_hyperparameters": {
                "alpha": 1.0,
            },
            "hyperparameter_schema": {
                "alpha": {"type": "float", "min": 0.01, "max": 20.0, "default": 1.0},
            },
        },
        ModelAlgorithm.DECISION_TREE_REGRESSOR.value: {
            "name": "Decision Tree Regressor",
            "task_type": "regression",
            "class": DecisionTreeModel,
            "description": "Recursive binary regression tree on variance reduction.",
            "default_hyperparameters": {
                "max_depth": 6,
                "min_samples_split": 2,
            },
            "hyperparameter_schema": {
                "max_depth": {"type": "int", "min": 2, "max": 20, "default": 6},
                "min_samples_split": {"type": "int", "min": 2, "max": 10, "default": 2},
            },
        },
        ModelAlgorithm.KNN_REGRESSOR.value: {
            "name": "K-Nearest Neighbors Regressor",
            "task_type": "regression",
            "class": KNNModel,
            "description": "Locally weighted continuous regression averaging K closest spatial instances.",
            "default_hyperparameters": {
                "n_neighbors": 5,
            },
            "hyperparameter_schema": {
                "n_neighbors": {"type": "int", "min": 1, "max": 25, "default": 5},
            },
        },
    }

    @classmethod
    def list_available_algorithms(cls) -> List[AlgorithmInfo]:
        """Return metadata and hyperparameter schemas for all supported algorithms."""
        result: List[AlgorithmInfo] = []
        for key, info in cls.ALGORITHMS.items():
            result.append(
                AlgorithmInfo(
                    algorithm=key,
                    name=info["name"],
                    task_type=info["task_type"],
                    description=info["description"],
                    default_hyperparameters=info["default_hyperparameters"],
                    hyperparameter_schema=info["hyperparameter_schema"],
                )
            )
        return result

    @classmethod
    def instantiate_model(cls, algorithm: str, hyperparameters: Dict[str, Any], task_type: str) -> BaseMLModel:
        """Create configured instance of the specified model algorithm."""
        if algorithm not in cls.ALGORITHMS:
            # Default fallback
            algorithm = (
                ModelAlgorithm.RANDOM_FOREST_CLASSIFIER.value
                if task_type == "classification"
                else ModelAlgorithm.RANDOM_FOREST_REGRESSOR.value
            )

        info = cls.ALGORITHMS[algorithm]
        model_cls = info["class"]
        merged_params = dict(info["default_hyperparameters"])
        merged_params.update(hyperparameters)

        # Inject task_type if supported by constructor
        if "task_type" in model_cls.__init__.__code__.co_varnames:
            merged_params["task_type"] = task_type

        return model_cls(**merged_params)

    @classmethod
    def cross_validate(
        cls,
        algorithm: str,
        hyperparameters: Dict[str, Any],
        X: np.ndarray,
        y: np.ndarray,
        cv_config: CrossValidationConfig,
        task_type: str,
    ) -> CVSummary:
        """Perform K-Fold Cross Validation strictly evaluating out-of-fold partitions."""
        n_samples = len(X)
        k = min(cv_config.n_splits, n_samples)
        if k < 2:
            return CVSummary(mean_val_score=0.0, std_val_score=0.0, folds=[])

        rng = np.random.RandomState(cv_config.random_state)
        indices = np.arange(n_samples)
        if cv_config.shuffle:
            rng.shuffle(indices)

        # Partition folds
        fold_sizes = np.full(k, n_samples // k, dtype=int)
        fold_sizes[: n_samples % k] += 1
        current = 0
        folds_indices = []
        for fold_size in fold_sizes:
            start, stop = current, current + fold_size
            folds_indices.append(indices[start:stop])
            current = stop

        folds_results: List[CVFoldResult] = []
        val_scores: List[float] = []

        for fold_idx in range(k):
            val_idx = folds_indices[fold_idx]
            train_idx = np.setdiff1d(indices, val_idx)

            X_tr, y_tr = X[train_idx], y[train_idx]
            X_va, y_va = X[val_idx], y[val_idx]

            fold_model = cls.instantiate_model(algorithm, hyperparameters, task_type)
            fold_model.fit(X_tr, y_tr)

            tr_pred = fold_model.predict(X_tr)
            va_pred = fold_model.predict(X_va)

            if task_type == "classification":
                tr_score = float(np.mean(tr_pred == y_tr))
                va_score = float(np.mean(va_pred == y_va))
                metrics_dict = {"accuracy": round(va_score, 4)}
            else:
                # R2 score for regression
                ss_res = np.sum((y_va - va_pred) ** 2)
                ss_tot = np.sum((y_va - np.mean(y_va)) ** 2)
                va_score = float(1.0 - (ss_res / ss_tot)) if ss_tot > 1e-8 else 0.0
                tr_score = 0.0
                metrics_dict = {"r2_score": round(va_score, 4)}

            val_scores.append(va_score)
            folds_results.append(
                CVFoldResult(
                    fold=fold_idx + 1,
                    train_score=round(tr_score, 4),
                    val_score=round(va_score, 4),
                    metrics=metrics_dict,
                )
            )

        mean_val = float(np.mean(val_scores))
        std_val = float(np.std(val_scores))

        return CVSummary(
            mean_val_score=round(mean_val, 4),
            std_val_score=round(std_val, 4),
            folds=folds_results,
        )

    @classmethod
    def train_and_evaluate(
        cls,
        algorithm: str,
        hyperparameters: Dict[str, Any],
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        feature_names: List[str],
        task_type: str,
        cv_config: CrossValidationConfig | None = None,
    ) -> Dict[str, Any]:
        """Execute cross-validation, train final model on full train split, and calculate complete metrics."""
        start_time = time.perf_counter()

        # Pre-flight input matrix validation & NaN/Inf sanitization
        X_train = np.nan_to_num(X_train, nan=0.0, posinf=0.0, neginf=0.0)
        X_test = np.nan_to_num(X_test, nan=0.0, posinf=0.0, neginf=0.0)

        if len(X_train) < 2:
            raise ValueError("Training matrix requires at least 2 samples")
        if len(X_test) < 1:
            raise ValueError("Evaluation matrix requires at least 1 sample")

        # 1. K-Fold Cross Validation
        cv_summary = None
        if cv_config and cv_config.n_splits >= 2 and len(X_train) >= 4:
            cv_summary = cls.cross_validate(
                algorithm=algorithm,
                hyperparameters=hyperparameters,
                X=X_train,
                y=y_train,
                cv_config=cv_config,
                task_type=task_type,
            )

        # 2. Final Training on Full X_train
        model = cls.instantiate_model(algorithm, hyperparameters, task_type)
        model.fit(X_train, y_train)

        # 3. Predict on Train & Test Splits
        train_preds = model.predict(X_train)
        test_preds = model.predict(X_test)

        train_prob = None
        test_prob = None
        if task_type == "classification" and hasattr(model, "predict_proba"):
            try:
                train_prob = model.predict_proba(X_train)
                test_prob = model.predict_proba(X_test)
            except Exception:
                train_prob = None
                test_prob = None

        # 4. Compute Metrics Suite
        if task_type == "classification":
            train_metrics, _, _ = ModelEvaluator.evaluate_classification(
                y_true=y_train, y_pred=train_preds, y_prob=train_prob
            )
            test_metrics, cm_data, roc_curve = ModelEvaluator.evaluate_classification(
                y_true=y_test, y_pred=test_preds, y_prob=test_prob
            )
            residuals_sample = []
        else:
            train_metrics, _ = ModelEvaluator.evaluate_regression(y_true=y_train, y_pred=train_preds)
            test_metrics, residuals_sample = ModelEvaluator.evaluate_regression(y_true=y_test, y_pred=test_preds)
            cm_data = None
            roc_curve = []

        # 5. Extract Feature Importances
        raw_imp = model.get_feature_importances()
        feature_importances: List[FeatureImportanceItem] = []
        if raw_imp is not None and len(raw_imp) == len(feature_names):
            sorted_indices = np.argsort(raw_imp)[::-1]
            for rank, idx in enumerate(sorted_indices, start=1):
                feature_importances.append(
                    FeatureImportanceItem(
                        feature=feature_names[idx],
                        importance=round(float(raw_imp[idx]), 4),
                        rank=rank,
                    )
                )

        duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        return {
            "model": model,
            "train_metrics": train_metrics,
            "test_metrics": test_metrics,
            "cv_summary": cv_summary,
            "feature_importances": feature_importances,
            "confusion_matrix": cm_data,
            "roc_curve": roc_curve,
            "residuals_sample": residuals_sample,
            "duration_ms": duration_ms,
        }
