"""End-to-end Preprocessing and Feature Engineering Engine with strict Zero Data Leakage."""

import os
import pickle
import time
import uuid
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

from app.ml.transformers import (
    CyclicalDatetimeEncoder,
    TargetMeanEncoder,
)
from app.schemas.preprocessor import (
    CategoricalEncoderStrategy,
    CategoricalFeatureConfig,
    CategoricalImputerStrategy,
    NumericalFeatureConfig,
    NumericalImputerStrategy,
    NumericalPowerTransform,
    NumericalScalerStrategy,
    PreprocessingConfig,
    PreprocessingResponse,
)


class PreprocessingPipelineBuilder:
    """Constructs, fits, and serializes end-to-end tabular transformation pipelines."""

    @classmethod
    def execute_pipeline(
        cls,
        df: pd.DataFrame,
        config: PreprocessingConfig,
        dataset_id: str,
        dataset_name: str,
        output_dir: str,
    ) -> Tuple[PreprocessingResponse, Dict[str, Any]]:
        """Run the full feature engineering pipeline adhering strictly to Zero Data Leakage."""
        start_time = time.perf_counter()
        pipeline_id = str(uuid.uuid4())
        original_shape = [int(len(df)), int(len(df.columns))]

        # 1. Target column extraction & Problem type determination
        target_col = config.target_column
        y = None
        X = df.copy()

        if target_col and target_col in df.columns:
            y = df[target_col].to_numpy()
            X = df.drop(columns=[target_col])
        else:
            target_col = None

        # Drop manually excluded features from config
        if config.feature_selection.drop_features:
            valid_drops = [c for c in config.feature_selection.drop_features if c in X.columns]
            if valid_drops:
                X = X.drop(columns=valid_drops)

        # 2. Train / Test Split (Strict Zero Data Leakage Requirement)
        split_cfg = config.split_config
        X_train, X_val, X_test, y_train, y_val, y_test = cls._split_data(
            X=X,
            y=y,
            test_size=split_cfg.test_size,
            val_size=split_cfg.val_size,
            stratify=split_cfg.stratify if y is not None else False,
            random_state=split_cfg.random_state,
            shuffle=split_cfg.shuffle,
        )

        # 3. Fit Transformation Transformers on Train Split ONLY
        transformers_map = {}
        transformed_train_blocks = []
        transformed_val_blocks = []
        transformed_test_blocks = []
        feature_names: List[str] = []

        # --- Process Numerical Features ---
        for num_cfg in config.numerical_features:
            col = num_cfg.column_name
            if col not in X_train.columns:
                continue

            fitted_block = cls._fit_numerical_feature(
                train_series=X_train[col],
                cfg=num_cfg,
            )
            transformers_map[f"num_{col}"] = fitted_block

            # Transform train, val, test
            train_trans = cls._transform_numerical_feature(X_train[col], fitted_block)
            test_trans = cls._transform_numerical_feature(X_test[col], fitted_block)
            val_trans = cls._transform_numerical_feature(X_val[col], fitted_block) if X_val is not None else None

            transformed_train_blocks.append(train_trans)
            transformed_test_blocks.append(test_trans)
            if val_trans is not None:
                transformed_val_blocks.append(val_trans)

            feature_names.append(col)

        # --- Process Categorical Features ---
        for cat_cfg in config.categorical_features:
            col = cat_cfg.column_name
            if col not in X_train.columns:
                continue

            fitted_block = cls._fit_categorical_feature(
                train_series=X_train[col],
                y_train=y_train,
                cfg=cat_cfg,
            )
            transformers_map[f"cat_{col}"] = fitted_block

            train_trans, out_names = cls._transform_categorical_feature(X_train[col], fitted_block)
            test_trans, _ = cls._transform_categorical_feature(X_test[col], fitted_block)
            val_trans, _ = (
                cls._transform_categorical_feature(X_val[col], fitted_block) if X_val is not None else (None, [])
            )

            transformed_train_blocks.append(train_trans)
            transformed_test_blocks.append(test_trans)
            if val_trans is not None:
                transformed_val_blocks.append(val_trans)

            feature_names.extend(out_names)

        # --- Process Datetime Features ---
        for dt_cfg in config.datetime_features:
            col = dt_cfg.column_name
            if col not in X_train.columns:
                continue

            encoder = CyclicalDatetimeEncoder(
                extracted_parts=[p.value for p in dt_cfg.extracted_parts],
                cyclical_encoding=dt_cfg.cyclical_encoding,
            )
            encoder.fit(X_train[col])
            transformers_map[f"dt_{col}"] = encoder

            train_trans = encoder.transform(X_train[col])
            test_trans = encoder.transform(X_test[col])
            val_trans = encoder.transform(X_val[col]) if X_val is not None else None

            transformed_train_blocks.append(train_trans)
            transformed_test_blocks.append(test_trans)
            if val_trans is not None:
                transformed_val_blocks.append(val_trans)

            for part_name in encoder.output_feature_names_:
                feature_names.append(f"{col}_{part_name}")

        # Assemble Full Feature Matrices
        if not transformed_train_blocks:
            # Fallback if no specific feature configs were supplied: treat all numeric as standard scaled
            num_cols = X_train.select_dtypes(include=[np.number]).columns.tolist()
            if num_cols:
                train_mat = X_train[num_cols].fillna(0).to_numpy()
                test_mat = X_test[num_cols].fillna(0).to_numpy()
                val_mat = X_val[num_cols].fillna(0).to_numpy() if X_val is not None else None
                feature_names = num_cols
            else:
                train_mat = np.zeros((len(X_train), 0))
                test_mat = np.zeros((len(X_test), 0))
                val_mat = np.zeros((len(X_val), 0)) if X_val is not None else None
        else:
            train_mat = np.column_stack(transformed_train_blocks)
            test_mat = np.column_stack(transformed_test_blocks)
            val_mat = np.column_stack(transformed_val_blocks) if X_val is not None else None

        # 4. Feature Selection: Variance Threshold & Multicollinearity Filtering (on Train matrix only)
        dropped_feature_names: List[str] = []
        if config.feature_selection.variance_threshold is not None:
            vt = config.feature_selection.variance_threshold
            vars_ = np.var(train_mat, axis=0)
            keep_mask = vars_ > vt
            dropped_idxs = [i for i, k in enumerate(keep_mask) if not k]
            for idx in dropped_idxs:
                dropped_feature_names.append(feature_names[idx])
            train_mat = train_mat[:, keep_mask]
            test_mat = test_mat[:, keep_mask]
            if val_mat is not None:
                val_mat = val_mat[:, keep_mask]
            feature_names = [f for i, f in enumerate(feature_names) if keep_mask[i]]

        if config.feature_selection.correlation_threshold is not None and train_mat.shape[1] > 1:
            ct = config.feature_selection.correlation_threshold
            corr_df = pd.DataFrame(train_mat).corr().abs()
            upper_tri = np.triu(np.ones(corr_df.shape), k=1).astype(bool)
            to_drop_idx = [i for i in range(train_mat.shape[1]) if any(corr_df.iloc[:i, i] > ct)]

            keep_mask = np.ones(train_mat.shape[1], dtype=bool)
            keep_mask[to_drop_idx] = False

            for idx in to_drop_idx:
                dropped_feature_names.append(feature_names[idx])

            train_mat = train_mat[:, keep_mask]
            test_mat = test_mat[:, keep_mask]
            if val_mat is not None:
                val_mat = val_mat[:, keep_mask]
            feature_names = [f for i, f in enumerate(feature_names) if keep_mask[i]]

        # 5. Persist Serialized Artifact
        os.makedirs(output_dir, exist_ok=True)
        artifact_path = os.path.join(output_dir, f"pipeline_{pipeline_id}.pkl")
        pipeline_artifact = {
            "pipeline_id": pipeline_id,
            "dataset_id": dataset_id,
            "dataset_name": dataset_name,
            "config": config.model_dump(),
            "transformers": transformers_map,
            "feature_names": feature_names,
            "target_column": target_col,
            "problem_type": config.problem_type,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

        with open(artifact_path, "wb") as f:
            pickle.dump(pipeline_artifact, f)

        execution_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        # 6. Generate Train Preview Table (first 10 rows)
        preview_rows = []
        preview_limit = min(10, train_mat.shape[0])
        for r_idx in range(preview_limit):
            row_dict = {}
            for f_idx, f_name in enumerate(feature_names):
                val = float(train_mat[r_idx, f_idx])
                row_dict[f_name] = round(val, 4) if pd.notna(val) else None
            if y_train is not None:
                row_dict["__target__"] = (
                    int(y_train[r_idx]) if isinstance(y_train[r_idx], (int, np.integer)) else str(y_train[r_idx])
                )
            preview_rows.append(row_dict)

        response = PreprocessingResponse(
            pipeline_id=pipeline_id,
            dataset_id=dataset_id,
            dataset_name=dataset_name,
            target_column=target_col,
            problem_type=config.problem_type,
            original_shape=original_shape,
            train_shape=[int(train_mat.shape[0]), int(train_mat.shape[1])],
            val_shape=[int(val_mat.shape[0]), int(val_mat.shape[1])] if val_mat is not None else None,
            test_shape=[int(test_mat.shape[0]), int(test_mat.shape[1])],
            original_feature_count=original_shape[1] - (1 if target_col else 0),
            transformed_feature_count=int(train_mat.shape[1]),
            transformed_feature_names=feature_names,
            dropped_features=dropped_feature_names,
            storage_path=artifact_path,
            execution_time_ms=execution_ms,
            train_preview=preview_rows,
            columns=feature_names,
        )

        pipeline_data_bundle = {
            "X_train": train_mat,
            "X_val": val_mat,
            "X_test": test_mat,
            "y_train": y_train,
            "y_val": y_val,
            "y_test": y_test,
            "feature_names": feature_names,
            "pipeline_id": pipeline_id,
        }

        return response, pipeline_data_bundle

    @classmethod
    def _split_data(
        cls,
        X: pd.DataFrame,
        y: np.ndarray | None,
        test_size: float,
        val_size: float,
        stratify: bool,
        random_state: int,
        shuffle: bool,
    ) -> Tuple[
        pd.DataFrame,
        pd.DataFrame | None,
        pd.DataFrame,
        np.ndarray | None,
        np.ndarray | None,
        np.ndarray | None,
    ]:
        """Perform train/val/test split with stratification and zero leakage."""
        n = len(X)
        rng = np.random.RandomState(random_state)
        indices = np.arange(n)

        if shuffle:
            if stratify and y is not None:
                # Stratified index sampling
                labels, counts = np.unique(y, return_counts=True)
                test_indices = []
                val_indices = []
                train_indices = []

                for label in labels:
                    label_idxs = indices[y == label]
                    rng.shuffle(label_idxs)
                    n_label = len(label_idxs)
                    n_test = int(round(n_label * test_size))
                    if n_test == 0 and test_size > 0:
                        n_test = 1
                    n_val = int(round(n_label * val_size)) if val_size > 0 else 0

                    test_indices.extend(label_idxs[:n_test])
                    if n_val > 0:
                        val_indices.extend(label_idxs[n_test : n_test + n_val])
                        train_indices.extend(label_idxs[n_test + n_val :])
                    else:
                        train_indices.extend(label_idxs[n_test:])

                train_idx = np.array(train_indices)
                test_idx = np.array(test_indices)
                val_idx = np.array(val_indices) if val_size > 0 else None
            else:
                rng.shuffle(indices)
                n_test = int(round(n * test_size))
                if n_test == 0 and test_size > 0:
                    n_test = 1
                n_val = int(round(n * val_size)) if val_size > 0 else 0

                test_idx = indices[:n_test]
                if n_val > 0:
                    val_idx = indices[n_test : n_test + n_val]
                    train_idx = indices[n_test + n_val :]
                else:
                    val_idx = None
                    train_idx = indices[n_test:]
        else:
            n_test = int(round(n * test_size))
            if n_test == 0 and test_size > 0:
                n_test = 1
            n_val = int(round(n * val_size)) if val_size > 0 else 0
            test_idx = indices[-n_test:]
            if n_val > 0:
                val_idx = indices[-(n_test + n_val) : -n_test]
                train_idx = indices[: -(n_test + n_val)]
            else:
                val_idx = None
                train_idx = indices[:-n_test]

        X_train = X.iloc[train_idx].reset_index(drop=True)
        X_test = X.iloc[test_idx].reset_index(drop=True)
        X_val = X.iloc[val_idx].reset_index(drop=True) if val_idx is not None else None

        y_train = y[train_idx] if y is not None else None
        y_test = y[test_idx] if y is not None else None
        y_val = y[val_idx] if (y is not None and val_idx is not None) else None

        return X_train, X_val, X_test, y_train, y_val, y_test

    @classmethod
    def _fit_numerical_feature(cls, train_series: pd.Series, cfg: NumericalFeatureConfig) -> Dict[str, Any]:
        """Fit imputer, clipper, and scaler parameters strictly on training series."""
        clean = pd.to_numeric(train_series, errors="coerce")
        valid_vals = clean.dropna().to_numpy(dtype=float)

        # 1. Imputer value
        if cfg.imputer == NumericalImputerStrategy.MEAN:
            impute_val = float(np.mean(valid_vals)) if len(valid_vals) > 0 else 0.0
        elif cfg.imputer == NumericalImputerStrategy.MEDIAN:
            impute_val = float(np.median(valid_vals)) if len(valid_vals) > 0 else 0.0
        elif cfg.imputer == NumericalImputerStrategy.MOST_FREQUENT:
            mode_s = clean.mode()
            impute_val = float(mode_s.iloc[0]) if len(mode_s) > 0 else 0.0
        elif cfg.imputer == NumericalImputerStrategy.CONSTANT:
            impute_val = float(cfg.imputer_fill_value) if cfg.imputer_fill_value is not None else 0.0
        else:
            impute_val = 0.0

        imputed_train = clean.fillna(impute_val).to_numpy(dtype=float)

        # 2. Outlier Clipper bounds
        clip_bounds = None
        if cfg.clip_outliers and len(imputed_train) > 0:
            low = float(np.percentile(imputed_train, cfg.lower_percentile * 100))
            high = float(np.percentile(imputed_train, cfg.upper_percentile * 100))
            clip_bounds = (low, high)
            imputed_train = np.clip(imputed_train, low, high)

        # 3. Power Transformation (Log1p)
        if cfg.power_transform == NumericalPowerTransform.LOG1P:
            # Shift if min < 0
            shift = 0.0
            min_v = float(np.min(imputed_train)) if len(imputed_train) > 0 else 0.0
            if min_v < 0:
                shift = abs(min_v) + 1.0
            imputed_train = np.log1p(imputed_train + shift)
        else:
            shift = 0.0

        # 4. Scaler parameters
        scale_params = {}
        if cfg.scaler == NumericalScalerStrategy.STANDARD:
            mu = float(np.mean(imputed_train)) if len(imputed_train) > 0 else 0.0
            std = float(np.std(imputed_train)) if len(imputed_train) > 0 else 1.0
            scale_params = {"mean": mu, "std": std if std > 1e-8 else 1.0}
        elif cfg.scaler == NumericalScalerStrategy.MINMAX:
            min_v = float(np.min(imputed_train)) if len(imputed_train) > 0 else 0.0
            max_v = float(np.max(imputed_train)) if len(imputed_train) > 0 else 1.0
            denom = max_v - min_v
            scale_params = {"min": min_v, "max": max_v, "scale": denom if denom > 1e-8 else 1.0}
        elif cfg.scaler == NumericalScalerStrategy.ROBUST:
            q25 = float(np.percentile(imputed_train, 25))
            q50 = float(np.percentile(imputed_train, 50))
            q75 = float(np.percentile(imputed_train, 75))
            iqr = q75 - q25
            scale_params = {"median": q50, "iqr": iqr if iqr > 1e-8 else 1.0}
        elif cfg.scaler == NumericalScalerStrategy.MAXABS:
            max_abs = float(np.max(np.abs(imputed_train))) if len(imputed_train) > 0 else 1.0
            scale_params = {"max_abs": max_abs if max_abs > 1e-8 else 1.0}

        return {
            "impute_val": impute_val,
            "clip_bounds": clip_bounds,
            "power_transform": cfg.power_transform,
            "shift": shift,
            "scaler": cfg.scaler,
            "scale_params": scale_params,
        }

    @classmethod
    def _transform_numerical_feature(cls, series: pd.Series, block: Dict[str, Any]) -> np.ndarray:
        """Apply fitted numerical parameters to test/val/inference series."""
        clean = pd.to_numeric(series, errors="coerce")
        arr = clean.fillna(block["impute_val"]).to_numpy(dtype=float)

        if block["clip_bounds"]:
            low, high = block["clip_bounds"]
            arr = np.clip(arr, low, high)

        if block["power_transform"] == NumericalPowerTransform.LOG1P:
            arr = np.log1p(arr + block["shift"])

        scaler = block["scaler"]
        params = block["scale_params"]

        if scaler == NumericalScalerStrategy.STANDARD:
            arr = (arr - params["mean"]) / params["std"]
        elif scaler == NumericalScalerStrategy.MINMAX:
            arr = (arr - params["min"]) / params["scale"]
        elif scaler == NumericalScalerStrategy.ROBUST:
            arr = (arr - params["median"]) / params["iqr"]
        elif scaler == NumericalScalerStrategy.MAXABS:
            arr = arr / params["max_abs"]

        return arr

    @classmethod
    def _fit_categorical_feature(
        cls, train_series: pd.Series, y_train: np.ndarray | None, cfg: CategoricalFeatureConfig
    ) -> Dict[str, Any]:
        """Fit imputer, top-K grouping, and encoding strictly on training data."""
        clean = train_series.astype(str)

        # 1. Imputer
        if cfg.imputer == CategoricalImputerStrategy.MOST_FREQUENT:
            mode_s = clean.mode()
            impute_val = mode_s.iloc[0] if len(mode_s) > 0 else "missing"
        else:
            impute_val = cfg.imputer_fill_value

        imputed_train = clean.fillna(impute_val)

        # 2. Top-K Categories
        top_k = cfg.max_categories or 20
        val_counts = imputed_train.value_counts()
        top_cats = val_counts.head(top_k).index.tolist()

        # Group non top-K as "Other"
        grouped_train = imputed_train.apply(lambda v: v if v in top_cats else "Other")

        # 3. Encoder fitting
        encoder_data = {}
        out_names = []

        if cfg.encoder == CategoricalEncoderStrategy.ONEHOT:
            unique_cats = sorted(grouped_train.unique().tolist())
            out_names = [f"{cfg.column_name}_{c}" for c in unique_cats]
            encoder_data = {"categories": unique_cats}

        elif cfg.encoder == CategoricalEncoderStrategy.ORDINAL:
            unique_cats = sorted(grouped_train.unique().tolist())
            mapping = {c: float(idx) for idx, c in enumerate(unique_cats)}
            encoder_data = {"mapping": mapping}
            out_names = [cfg.column_name]

        elif cfg.encoder == CategoricalEncoderStrategy.FREQUENCY:
            freq_map = (grouped_train.value_counts(normalize=True)).to_dict()
            encoder_data = {"frequencies": freq_map}
            out_names = [f"{cfg.column_name}_freq"]

        elif cfg.encoder == CategoricalEncoderStrategy.TARGET and y_train is not None:
            t_encoder = TargetMeanEncoder(smoothing=10.0)
            t_encoder.fit(grouped_train.to_frame(), y_train)
            encoder_data = {"target_encoder": t_encoder}
            out_names = [f"{cfg.column_name}_target_enc"]

        return {
            "impute_val": impute_val,
            "top_categories": set(top_cats),
            "encoder": cfg.encoder,
            "encoder_data": encoder_data,
            "out_names": out_names,
            "column_name": cfg.column_name,
        }

    @classmethod
    def _transform_categorical_feature(cls, series: pd.Series, block: Dict[str, Any]) -> Tuple[np.ndarray, List[str]]:
        """Apply fitted categorical encoder to test/val/inference data."""
        clean = series.astype(str).fillna(block["impute_val"])
        top_cats = block["top_categories"]
        grouped = clean.apply(lambda v: v if v in top_cats else "Other")

        encoder = block["encoder"]
        data = block["encoder_data"]
        out_names = block["out_names"]

        if encoder == CategoricalEncoderStrategy.ONEHOT:
            cats = data["categories"]
            matrix = np.zeros((len(grouped), len(cats)), dtype=float)
            cat_to_idx = {c: i for i, c in enumerate(cats)}

            for row_idx, val in enumerate(grouped):
                if val in cat_to_idx:
                    matrix[row_idx, cat_to_idx[val]] = 1.0
                elif "Other" in cat_to_idx:
                    matrix[row_idx, cat_to_idx["Other"]] = 1.0
            return matrix, out_names

        elif encoder == CategoricalEncoderStrategy.ORDINAL:
            mapping = data["mapping"]
            arr = grouped.map(mapping).fillna(-1.0).to_numpy(dtype=float)
            return arr, out_names

        elif encoder == CategoricalEncoderStrategy.FREQUENCY:
            freq_map = data["frequencies"]
            arr = grouped.map(freq_map).fillna(0.0).to_numpy(dtype=float)
            return arr, out_names

        elif encoder == CategoricalEncoderStrategy.TARGET:
            t_encoder: TargetMeanEncoder = data["target_encoder"]
            arr = t_encoder.transform(grouped.to_frame()).ravel()
            return arr, out_names

        # Fallback
        return np.zeros((len(grouped), 1), dtype=float), [block["column_name"]]
