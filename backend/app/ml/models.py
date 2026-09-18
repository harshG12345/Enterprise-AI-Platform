"""High-performance Scikit-Learn accelerated ML algorithms with standardized BaseMLModel interface."""

import numpy as np
from sklearn.ensemble import (
    GradientBoostingClassifier,
    GradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor


class BaseMLModel:
    """Base interface for all platform algorithms."""

    def fit(self, X: np.ndarray, y: np.ndarray):
        raise NotImplementedError

    def predict(self, X: np.ndarray) -> np.ndarray:
        raise NotImplementedError

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        raise NotImplementedError

    def get_feature_importances(self) -> np.ndarray | None:
        return None


# ==========================================
# Linear Models: Logistic & Linear Regression
# ==========================================


class LinearRegressionModel(BaseMLModel):
    """Ordinary Least Squares & Ridge ($L_2$) / Lasso ($L_1$) Regularized Linear Regression."""

    def __init__(self, alpha: float = 0.0, l1_ratio: float = 0.0, max_iter: int = 1000, lr: float = 0.01):
        self.alpha = float(alpha)
        self.l1_ratio = float(l1_ratio)
        self.max_iter = max_iter
        self.lr = lr
        self.weights_: np.ndarray | None = None
        self.bias_: float = 0.0
        self.feature_importances_: np.ndarray | None = None
        self._estimator = Ridge(alpha=self.alpha) if self.alpha > 0.0 else LinearRegression()

    def fit(self, X: np.ndarray, y: np.ndarray):
        X_arr = np.asarray(X, dtype=float)
        y_arr = np.asarray(y, dtype=float).ravel()
        n_features = X_arr.shape[1]

        self._estimator.fit(X_arr, y_arr)
        self.weights_ = np.asarray(self._estimator.coef_, dtype=float)
        self.bias_ = float(self._estimator.intercept_)

        raw_imp = np.abs(self.weights_)
        tot = np.sum(raw_imp)
        self.feature_importances_ = raw_imp / tot if tot > 0 else np.ones(n_features) / n_features
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        X_arr = np.asarray(X, dtype=float)
        return np.asarray(self._estimator.predict(X_arr), dtype=float)

    def get_feature_importances(self) -> np.ndarray | None:
        return self.feature_importances_


class LogisticRegressionModel(BaseMLModel):
    """Vectorized Multi-class & Binary Logistic Regression with L2 Regularization."""

    def __init__(self, C: float = 1.0, max_iter: int = 200, lr: float = 0.05):
        self.C = float(C) if float(C) > 0 else 1.0
        self.max_iter = max(50, int(max_iter))
        self.lr = lr
        self.classes_: np.ndarray | None = None
        self.weights_: np.ndarray | None = None
        self.biases_: np.ndarray | None = None
        self.feature_importances_: np.ndarray | None = None
        self._estimator = LogisticRegression(
            C=self.C,
            max_iter=self.max_iter,
            random_state=42,
        )

    def fit(self, X: np.ndarray, y: np.ndarray):
        X_arr = np.asarray(X, dtype=float)
        y_arr = np.asarray(y)
        n_features = X_arr.shape[1]

        self._estimator.fit(X_arr, y_arr)
        self.classes_ = np.asarray(self._estimator.classes_)
        self.weights_ = np.asarray(self._estimator.coef_)
        self.biases_ = np.asarray(self._estimator.intercept_)

        raw_imp = np.mean(np.abs(self.weights_), axis=0) if self.weights_.ndim > 1 else np.abs(self.weights_)
        tot = np.sum(raw_imp)
        self.feature_importances_ = raw_imp / tot if tot > 0 else np.ones(n_features) / n_features
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        X_arr = np.asarray(X, dtype=float)
        return np.asarray(self._estimator.predict_proba(X_arr), dtype=float)

    def predict(self, X: np.ndarray) -> np.ndarray:
        X_arr = np.asarray(X, dtype=float)
        return np.asarray(self._estimator.predict(X_arr))

    def get_feature_importances(self) -> np.ndarray | None:
        return self.feature_importances_


# ==========================================
# Tree Models: Decision Tree & Random Forest
# ==========================================


class DecisionTreeModel(BaseMLModel):
    """Classification & Regression CART Decision Tree with impurity gain feature importances."""

    def __init__(
        self,
        max_depth: int = 6,
        min_samples_split: int = 2,
        task_type: str = "classification",
    ):
        self.max_depth = int(max_depth) if max_depth is not None else None
        self.min_samples_split = max(2, int(min_samples_split))
        self.task_type = task_type
        self.feature_importances_: np.ndarray | None = None
        self.classes_: np.ndarray | None = None
        if self.task_type == "classification":
            self._estimator = DecisionTreeClassifier(
                max_depth=self.max_depth,
                min_samples_split=self.min_samples_split,
                random_state=42,
            )
        else:
            self._estimator = DecisionTreeRegressor(
                max_depth=self.max_depth,
                min_samples_split=self.min_samples_split,
                random_state=42,
            )

    def fit(self, X: np.ndarray, y: np.ndarray):
        X_arr = np.asarray(X, dtype=float)
        y_arr = np.asarray(y)
        n_features = X_arr.shape[1]

        self._estimator.fit(X_arr, y_arr)
        if self.task_type == "classification":
            self.classes_ = np.asarray(self._estimator.classes_)

        imp = np.asarray(self._estimator.feature_importances_, dtype=float)
        tot = np.sum(imp)
        self.feature_importances_ = imp / tot if tot > 0 else np.ones(n_features) / n_features
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        X_arr = np.asarray(X, dtype=float)
        return np.asarray(self._estimator.predict(X_arr))

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        if self.task_type != "classification":
            raise ValueError("predict_proba is only supported for classification")
        X_arr = np.asarray(X, dtype=float)
        return np.asarray(self._estimator.predict_proba(X_arr), dtype=float)

    def get_feature_importances(self) -> np.ndarray | None:
        return self.feature_importances_


class RandomForestModel(BaseMLModel):
    """Ensemble Bagging Random Forest with bootstrap sampling."""

    def __init__(
        self,
        n_estimators: int = 20,
        max_depth: int = 6,
        min_samples_split: int = 2,
        task_type: str = "classification",
        random_state: int = 42,
    ):
        self.n_estimators = int(n_estimators)
        self.max_depth = int(max_depth) if max_depth is not None else None
        self.min_samples_split = max(2, int(min_samples_split))
        self.task_type = task_type
        self.random_state = random_state
        self.feature_importances_: np.ndarray | None = None
        self.classes_: np.ndarray | None = None

        if self.task_type == "classification":
            self._estimator = RandomForestClassifier(
                n_estimators=self.n_estimators,
                max_depth=self.max_depth,
                min_samples_split=self.min_samples_split,
                random_state=self.random_state,
                n_jobs=-1,
            )
        else:
            self._estimator = RandomForestRegressor(
                n_estimators=self.n_estimators,
                max_depth=self.max_depth,
                min_samples_split=self.min_samples_split,
                random_state=self.random_state,
                n_jobs=-1,
            )

    def fit(self, X: np.ndarray, y: np.ndarray):
        X_arr = np.asarray(X, dtype=float)
        y_arr = np.asarray(y)
        n_features = X_arr.shape[1]

        self._estimator.fit(X_arr, y_arr)
        if self.task_type == "classification":
            self.classes_ = np.asarray(self._estimator.classes_)

        imp = np.asarray(self._estimator.feature_importances_, dtype=float)
        tot = np.sum(imp)
        self.feature_importances_ = imp / tot if tot > 0 else np.ones(n_features) / n_features
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        X_arr = np.asarray(X, dtype=float)
        return np.asarray(self._estimator.predict(X_arr))

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        if self.task_type != "classification":
            raise ValueError("predict_proba only available for classification")
        X_arr = np.asarray(X, dtype=float)
        return np.asarray(self._estimator.predict_proba(X_arr), dtype=float)

    def get_feature_importances(self) -> np.ndarray | None:
        return self.feature_importances_


class GradientBoostingModel(BaseMLModel):
    """Forward stagewise gradient boosting ensemble."""

    def __init__(
        self,
        n_estimators: int = 15,
        learning_rate: float = 0.1,
        max_depth: int = 4,
        task_type: str = "classification",
    ):
        self.n_estimators = int(n_estimators)
        self.learning_rate = float(learning_rate)
        self.max_depth = int(max_depth)
        self.task_type = task_type
        self.feature_importances_: np.ndarray | None = None
        self.classes_: np.ndarray | None = None

        if self.task_type == "classification":
            self._estimator = GradientBoostingClassifier(
                n_estimators=self.n_estimators,
                learning_rate=self.learning_rate,
                max_depth=self.max_depth,
                random_state=42,
            )
        else:
            self._estimator = GradientBoostingRegressor(
                n_estimators=self.n_estimators,
                learning_rate=self.learning_rate,
                max_depth=self.max_depth,
                random_state=42,
            )

    def fit(self, X: np.ndarray, y: np.ndarray):
        X_arr = np.asarray(X, dtype=float)
        y_arr = np.asarray(y)
        n_features = X_arr.shape[1]

        self._estimator.fit(X_arr, y_arr)
        if self.task_type == "classification":
            self.classes_ = np.asarray(self._estimator.classes_)

        imp = np.asarray(self._estimator.feature_importances_, dtype=float)
        tot = np.sum(imp)
        self.feature_importances_ = imp / tot if tot > 0 else np.ones(n_features) / n_features
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        X_arr = np.asarray(X, dtype=float)
        return np.asarray(self._estimator.predict(X_arr))

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        X_arr = np.asarray(X, dtype=float)
        return np.asarray(self._estimator.predict_proba(X_arr), dtype=float)

    def get_feature_importances(self) -> np.ndarray | None:
        return self.feature_importances_


class KNNModel(BaseMLModel):
    """K-Nearest Neighbors using Euclidean distance."""

    def __init__(self, n_neighbors: int = 5, task_type: str = "classification"):
        self.n_neighbors = int(n_neighbors)
        self.task_type = task_type
        self.classes_: np.ndarray | None = None
        self.feature_importances_: np.ndarray | None = None

        if self.task_type == "classification":
            self._estimator = KNeighborsClassifier(n_neighbors=self.n_neighbors, n_jobs=-1)
        else:
            self._estimator = KNeighborsRegressor(n_neighbors=self.n_neighbors, n_jobs=-1)

    def fit(self, X: np.ndarray, y: np.ndarray):
        X_arr = np.asarray(X, dtype=float)
        y_arr = np.asarray(y)
        n_features = X_arr.shape[1]

        self._estimator.fit(X_arr, y_arr)
        if self.task_type == "classification":
            self.classes_ = np.asarray(self._estimator.classes_)
        self.feature_importances_ = np.ones(n_features) / n_features
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        X_arr = np.asarray(X, dtype=float)
        return np.asarray(self._estimator.predict(X_arr))

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        if self.task_type != "classification":
            raise ValueError("predict_proba is only supported for classification")
        X_arr = np.asarray(X, dtype=float)
        return np.asarray(self._estimator.predict_proba(X_arr), dtype=float)

    def get_feature_importances(self) -> np.ndarray | None:
        return self.feature_importances_
