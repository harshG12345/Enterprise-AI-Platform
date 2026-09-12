"""Pure Python/Numpy vectorized implementations of core ML algorithms."""

from typing import List

import numpy as np


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

    def fit(self, X: np.ndarray, y: np.ndarray):
        X_arr = np.asarray(X, dtype=float)
        y_arr = np.asarray(y, dtype=float).ravel()
        n_samples, n_features = X_arr.shape

        if self.alpha == 0.0:
            # Analytical OLS with pseudo-inverse for numerical stability
            X_b = np.column_stack([np.ones(n_samples), X_arr])
            try:
                theta = np.linalg.pinv(X_b.T @ X_b) @ (X_b.T @ y_arr)
                self.bias_ = float(theta[0])
                self.weights_ = theta[1:]
            except np.linalg.LinAlgError:
                self.weights_ = np.zeros(n_features)
                self.bias_ = float(np.mean(y_arr))
        else:
            # Analytical Ridge: (X^T X + alpha*I)^(-1) X^T y
            X_mean = np.mean(X_arr, axis=0)
            X_std = np.std(X_arr, axis=0)
            X_std[X_std == 0] = 1.0
            X_norm = (X_arr - X_mean) / X_std

            y_mean = np.mean(y_arr)
            y_centered = y_arr - y_mean

            I = np.eye(n_features)
            theta_norm = np.linalg.pinv(X_norm.T @ X_norm + self.alpha * I) @ (X_norm.T @ y_centered)
            self.weights_ = theta_norm / X_std
            self.bias_ = float(y_mean - np.sum(self.weights_ * X_mean))

        # Absolute weight magnitude as feature importance
        raw_imp = np.abs(self.weights_)
        tot = np.sum(raw_imp)
        self.feature_importances_ = raw_imp / tot if tot > 0 else np.ones(n_features) / n_features
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        X_arr = np.asarray(X, dtype=float)
        return X_arr @ self.weights_ + self.bias_

    def get_feature_importances(self) -> np.ndarray | None:
        return self.feature_importances_


class LogisticRegressionModel(BaseMLModel):
    """Vectorized Multi-class & Binary Logistic Regression with L2 Regularization."""

    def __init__(self, C: float = 1.0, max_iter: int = 200, lr: float = 0.05):
        self.C = float(C)
        self.max_iter = max_iter
        self.lr = lr
        self.classes_: np.ndarray | None = None
        self.weights_: np.ndarray | None = None  # (n_classes, n_features)
        self.biases_: np.ndarray | None = None
        self.feature_importances_: np.ndarray | None = None

    @staticmethod
    def _sigmoid(z: np.ndarray) -> np.ndarray:
        return 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))

    def fit(self, X: np.ndarray, y: np.ndarray):
        X_arr = np.asarray(X, dtype=float)
        y_arr = np.asarray(y)
        n_samples, n_features = X_arr.shape

        self.classes_ = np.unique(y_arr)
        n_classes = len(self.classes_)

        # Standardize features for gradient descent convergence
        X_mean = np.mean(X_arr, axis=0)
        X_std = np.std(X_arr, axis=0)
        X_std[X_std == 0] = 1.0
        X_norm = (X_arr - X_mean) / X_std

        if n_classes == 2:
            y_bin = (y_arr == self.classes_[1]).astype(float)
            w = np.zeros(n_features)
            b = 0.0
            lambda_reg = 1.0 / self.C if self.C > 0 else 0.0

            for _ in range(self.max_iter):
                preds = self._sigmoid(X_norm @ w + b)
                grad_w = (1.0 / n_samples) * (X_norm.T @ (preds - y_bin)) + (lambda_reg / n_samples) * w
                grad_b = float((1.0 / n_samples) * np.sum(preds - y_bin))
                w -= self.lr * grad_w
                b -= self.lr * grad_b

            self.weights_ = (w / X_std).reshape(1, -1)
            self.biases_ = np.array([b - np.sum((w / X_std) * X_mean)])
        else:
            # One-vs-Rest Multi-class
            self.weights_ = np.zeros((n_classes, n_features))
            self.biases_ = np.zeros(n_classes)
            lambda_reg = 1.0 / self.C if self.C > 0 else 0.0

            for c_idx, cls_label in enumerate(self.classes_):
                y_bin = (y_arr == cls_label).astype(float)
                w = np.zeros(n_features)
                b = 0.0
                for _ in range(self.max_iter):
                    preds = self._sigmoid(X_norm @ w + b)
                    grad_w = (1.0 / n_samples) * (X_norm.T @ (preds - y_bin)) + (lambda_reg / n_samples) * w
                    grad_b = float((1.0 / n_samples) * np.sum(preds - y_bin))
                    w -= self.lr * grad_w
                    b -= self.lr * grad_b

                self.weights_[c_idx] = w / X_std
                self.biases_[c_idx] = b - np.sum((w / X_std) * X_mean)

        # Compute aggregate feature importance from weight magnitudes
        raw_imp = np.mean(np.abs(self.weights_), axis=0)
        tot = np.sum(raw_imp)
        self.feature_importances_ = raw_imp / tot if tot > 0 else np.ones(n_features) / n_features
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        X_arr = np.asarray(X, dtype=float)
        if len(self.classes_) == 2:
            scores = self._sigmoid(X_arr @ self.weights_[0] + self.biases_[0])
            return np.column_stack([1.0 - scores, scores])
        else:
            logits = X_arr @ self.weights_.T + self.biases_
            exp_logits = np.exp(logits - np.max(logits, axis=1, keepdims=True))
            return exp_logits / np.sum(exp_logits, axis=1, keepdims=True)

    def predict(self, X: np.ndarray) -> np.ndarray:
        probas = self.predict_proba(X)
        pred_indices = np.argmax(probas, axis=1)
        return self.classes_[pred_indices]

    def get_feature_importances(self) -> np.ndarray | None:
        return self.feature_importances_


# ==========================================
# Tree Models: Decision Tree & Random Forest
# ==========================================


class _TreeNode:
    def __init__(self, feature=None, threshold=None, left=None, right=None, *, value=None, impurity=0.0):
        self.feature = feature
        self.threshold = threshold
        self.left = left
        self.right = right
        self.value = value
        self.impurity = impurity

    @property
    def is_leaf(self) -> bool:
        return self.value is not None


class DecisionTreeModel(BaseMLModel):
    """Classification & Regression CART Decision Tree with impurity gain feature importances."""

    def __init__(
        self,
        max_depth: int = 6,
        min_samples_split: int = 2,
        task_type: str = "classification",
    ):
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.task_type = task_type
        self.root: _TreeNode | None = None
        self.feature_importances_: np.ndarray | None = None
        self.n_features_: int = 0
        self.classes_: np.ndarray | None = None

    def fit(self, X: np.ndarray, y: np.ndarray):
        X_arr = np.asarray(X, dtype=float)
        y_arr = np.asarray(y)
        self.n_features_ = X_arr.shape[1]
        self.feature_importances_ = np.zeros(self.n_features_)

        if self.task_type == "classification":
            self.classes_ = np.unique(y_arr)

        self.root = self._build_tree(X_arr, y_arr, depth=0)
        tot = np.sum(self.feature_importances_)
        if tot > 0:
            self.feature_importances_ /= tot
        else:
            self.feature_importances_ = np.ones(self.n_features_) / self.n_features_
        return self

    def _build_tree(self, X: np.ndarray, y: np.ndarray, depth: int) -> _TreeNode:
        n_samples, n_features = X.shape

        # Leaf conditions
        if depth >= self.max_depth or n_samples < self.min_samples_split or len(np.unique(y)) <= 1:
            leaf_val = self._calc_leaf_value(y)
            return _TreeNode(value=leaf_val)

        best_feat, best_thresh, best_gain = self._best_split(X, y)
        if best_feat is None or best_gain <= 1e-7:
            return _TreeNode(value=self._calc_leaf_value(y))

        # Accumulate impurity reduction
        self.feature_importances_[best_feat] += best_gain * (n_samples / 1.0)

        left_idx = X[:, best_feat] <= best_thresh
        right_idx = ~left_idx

        left = self._build_tree(X[left_idx], y[left_idx], depth + 1)
        right = self._build_tree(X[right_idx], y[right_idx], depth + 1)

        return _TreeNode(feature=best_feat, threshold=best_thresh, left=left, right=right)

    def _calc_leaf_value(self, y: np.ndarray):
        if self.task_type == "classification":
            vals, counts = np.unique(y, return_counts=True)
            return vals[np.argmax(counts)]
        return float(np.mean(y))

    def _best_split(self, X: np.ndarray, y: np.ndarray):
        best_gain = -1.0
        best_feat = None
        best_thresh = None
        n = len(y)

        current_impurity = self._calc_impurity(y)

        for feat_idx in range(X.shape[1]):
            col_vals = X[:, feat_idx]
            unique_threshs = np.percentile(col_vals, np.linspace(10, 90, 10))

            for thresh in unique_threshs:
                left_mask = col_vals <= thresh
                right_mask = ~left_mask

                if np.sum(left_mask) == 0 or np.sum(right_mask) == 0:
                    continue

                n_l, n_r = np.sum(left_mask), np.sum(right_mask)
                imp_l = self._calc_impurity(y[left_mask])
                imp_r = self._calc_impurity(y[right_mask])

                gain = current_impurity - ((n_l / n) * imp_l + (n_r / n) * imp_r)
                if gain > best_gain:
                    best_gain = gain
                    best_feat = feat_idx
                    best_thresh = thresh

        return best_feat, best_thresh, best_gain

    def _calc_impurity(self, y: np.ndarray) -> float:
        n = len(y)
        if n == 0:
            return 0.0
        if self.task_type == "classification":
            _, counts = np.unique(y, return_counts=True)
            probs = counts / n
            return float(1.0 - np.sum(probs**2))  # Gini Impurity
        return float(np.var(y))  # Variance for MSE reduction

    def _predict_row(self, node: _TreeNode, x: np.ndarray):
        if node.is_leaf:
            return node.value
        if x[node.feature] <= node.threshold:
            return self._predict_row(node.left, x)
        return self._predict_row(node.right, x)

    def predict(self, X: np.ndarray) -> np.ndarray:
        X_arr = np.asarray(X, dtype=float)
        return np.array([self._predict_row(self.root, row) for row in X_arr])

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        if self.task_type != "classification":
            raise ValueError("predict_proba is only supported for classification")
        preds = self.predict(X)
        probas = np.zeros((len(preds), len(self.classes_)))
        for i, p in enumerate(preds):
            c_idx = np.where(self.classes_ == p)[0][0]
            probas[i, c_idx] = 1.0
        return probas

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
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.task_type = task_type
        self.random_state = random_state
        self.trees_: List[DecisionTreeModel] = []
        self.feature_importances_: np.ndarray | None = None
        self.classes_: np.ndarray | None = None

    def fit(self, X: np.ndarray, y: np.ndarray):
        X_arr = np.asarray(X, dtype=float)
        y_arr = np.asarray(y)
        n_samples, n_features = X_arr.shape
        rng = np.random.RandomState(self.random_state)

        if self.task_type == "classification":
            self.classes_ = np.unique(y_arr)

        self.trees_ = []
        agg_importances = np.zeros(n_features)

        for i in range(self.n_estimators):
            # Bootstrap sample
            boot_idx = rng.choice(n_samples, size=n_samples, replace=True)
            X_boot = X_arr[boot_idx]
            y_boot = y_arr[boot_idx]

            tree = DecisionTreeModel(
                max_depth=self.max_depth,
                min_samples_split=self.min_samples_split,
                task_type=self.task_type,
            )
            tree.fit(X_boot, y_boot)
            self.trees_.append(tree)
            agg_importances += tree.feature_importances_

        tot = np.sum(agg_importances)
        self.feature_importances_ = agg_importances / tot if tot > 0 else np.ones(n_features) / n_features
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        X_arr = np.asarray(X, dtype=float)
        all_preds = np.array([t.predict(X_arr) for t in self.trees_])  # (n_trees, n_samples)

        if self.task_type == "classification":
            # Majority vote
            n_samples = X_arr.shape[0]
            majority_preds = []
            for j in range(n_samples):
                col = all_preds[:, j]
                vals, counts = np.unique(col, return_counts=True)
                majority_preds.append(vals[np.argmax(counts)])
            return np.array(majority_preds)
        else:
            return np.mean(all_preds, axis=0)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        if self.task_type != "classification":
            raise ValueError("predict_proba only available for classification")
        X_arr = np.asarray(X, dtype=float)
        all_preds = np.array([t.predict(X_arr) for t in self.trees_])  # (n_trees, n_samples)
        n_samples = X_arr.shape[0]
        n_classes = len(self.classes_)
        probas = np.zeros((n_samples, n_classes))

        for j in range(n_samples):
            col = all_preds[:, j]
            for c_idx, cls_label in enumerate(self.classes_):
                probas[j, c_idx] = np.mean(col == cls_label)
        return probas

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
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.max_depth = max_depth
        self.task_type = task_type
        self.base_pred_: float = 0.0
        self.trees_: List[DecisionTreeModel] = []
        self.feature_importances_: np.ndarray | None = None
        self.classes_: np.ndarray | None = None

    def fit(self, X: np.ndarray, y: np.ndarray):
        X_arr = np.asarray(X, dtype=float)
        y_arr = np.asarray(y)
        n_samples, n_features = X_arr.shape

        if self.task_type == "classification":
            self.classes_ = np.unique(y_arr)
            # Binary target
            y_target = (y_arr == self.classes_[1]).astype(float) if len(self.classes_) == 2 else y_arr.astype(float)
        else:
            y_target = y_arr.astype(float)

        self.base_pred_ = float(np.mean(y_target))
        current_preds = np.full(n_samples, self.base_pred_)
        self.trees_ = []
        agg_importances = np.zeros(n_features)

        for _ in range(self.n_estimators):
            # Compute negative gradient (residuals)
            residuals = y_target - current_preds
            tree = DecisionTreeModel(max_depth=self.max_depth, task_type="regression")
            tree.fit(X_arr, residuals)
            self.trees_.append(tree)

            current_preds += self.learning_rate * tree.predict(X_arr)
            agg_importances += tree.feature_importances_

        tot = np.sum(agg_importances)
        self.feature_importances_ = agg_importances / tot if tot > 0 else np.ones(n_features) / n_features
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        X_arr = np.asarray(X, dtype=float)
        preds = np.full(X_arr.shape[0], self.base_pred_)
        for tree in self.trees_:
            preds += self.learning_rate * tree.predict(X_arr)

        if self.task_type == "classification":
            if len(self.classes_) == 2:
                return np.where(preds >= 0.5, self.classes_[1], self.classes_[0])
            return np.round(preds).astype(int)
        return preds

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        X_arr = np.asarray(X, dtype=float)
        preds = np.full(X_arr.shape[0], self.base_pred_)
        for tree in self.trees_:
            preds += self.learning_rate * tree.predict(X_arr)
        # Sigmoid probability
        scores = 1.0 / (1.0 + np.exp(-np.clip(preds, -15, 15)))
        return np.column_stack([1.0 - scores, scores])

    def get_feature_importances(self) -> np.ndarray | None:
        return self.feature_importances_


class KNNModel(BaseMLModel):
    """K-Nearest Neighbors using Euclidean distance."""

    def __init__(self, n_neighbors: int = 5, task_type: str = "classification"):
        self.n_neighbors = n_neighbors
        self.task_type = task_type
        self.X_train_: np.ndarray | None = None
        self.y_train_: np.ndarray | None = None
        self.classes_: np.ndarray | None = None

    def fit(self, X: np.ndarray, y: np.ndarray):
        self.X_train_ = np.asarray(X, dtype=float)
        self.y_train_ = np.asarray(y)
        if self.task_type == "classification":
            self.classes_ = np.unique(self.y_train_)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        X_arr = np.asarray(X, dtype=float)
        preds = []

        for x in X_arr:
            dists = np.linalg.norm(self.X_train_ - x, axis=1)
            nn_idxs = np.argsort(dists)[: self.n_neighbors]
            nn_labels = self.y_train_[nn_idxs]

            if self.task_type == "classification":
                vals, counts = np.unique(nn_labels, return_counts=True)
                preds.append(vals[np.argmax(counts)])
            else:
                preds.append(float(np.mean(nn_labels)))

        return np.array(preds)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        X_arr = np.asarray(X, dtype=float)
        probas = np.zeros((len(X_arr), len(self.classes_)))

        for i, x in enumerate(X_arr):
            dists = np.linalg.norm(self.X_train_ - x, axis=1)
            nn_idxs = np.argsort(dists)[: self.n_neighbors]
            nn_labels = self.y_train_[nn_idxs]

            for c_idx, cls_label in enumerate(self.classes_):
                probas[i, c_idx] = np.mean(nn_labels == cls_label)

        return probas
