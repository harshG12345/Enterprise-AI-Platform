"""Pydantic schemas for data preprocessing and feature engineering configuration and results."""

from enum import Enum
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class NumericalImputerStrategy(str, Enum):
    MEAN = "mean"
    MEDIAN = "median"
    MOST_FREQUENT = "most_frequent"
    CONSTANT = "constant"


class NumericalScalerStrategy(str, Enum):
    STANDARD = "standard"
    MINMAX = "minmax"
    ROBUST = "robust"
    MAXABS = "maxabs"
    NONE = "none"


class NumericalPowerTransform(str, Enum):
    NONE = "none"
    LOG1P = "log1p"
    YEO_JOHNSON = "yeo_johnson"


class CategoricalImputerStrategy(str, Enum):
    MOST_FREQUENT = "most_frequent"
    CONSTANT = "constant"


class CategoricalEncoderStrategy(str, Enum):
    ONEHOT = "onehot"
    ORDINAL = "ordinal"
    TARGET = "target"
    FREQUENCY = "frequency"


class DatetimeExtractionPart(str, Enum):
    YEAR = "year"
    MONTH = "month"
    DAY = "day"
    DAYOFWEEK = "dayofweek"
    HOUR = "hour"
    IS_WEEKEND = "is_weekend"
    QUARTER = "quarter"


class NumericalFeatureConfig(BaseModel):
    column_name: str
    imputer: NumericalImputerStrategy = NumericalImputerStrategy.MEDIAN
    imputer_fill_value: float | None = None
    scaler: NumericalScalerStrategy = NumericalScalerStrategy.STANDARD
    power_transform: NumericalPowerTransform = NumericalPowerTransform.NONE
    clip_outliers: bool = False
    lower_percentile: float = 0.01
    upper_percentile: float = 0.99


class CategoricalFeatureConfig(BaseModel):
    column_name: str
    imputer: CategoricalImputerStrategy = CategoricalImputerStrategy.MOST_FREQUENT
    imputer_fill_value: str = "missing"
    encoder: CategoricalEncoderStrategy = CategoricalEncoderStrategy.ONEHOT
    max_categories: int | None = 20  # Keep top K, group remainder as 'Other'
    handle_unknown: str = "ignore"  # 'ignore' | 'error'


class DatetimeFeatureConfig(BaseModel):
    column_name: str
    extracted_parts: List[DatetimeExtractionPart] = Field(
        default_factory=lambda: [
            DatetimeExtractionPart.YEAR,
            DatetimeExtractionPart.MONTH,
            DatetimeExtractionPart.DAY,
            DatetimeExtractionPart.DAYOFWEEK,
            DatetimeExtractionPart.IS_WEEKEND,
        ]
    )
    cyclical_encoding: bool = True  # sin / cos on month & dayofweek
    drop_original: bool = True


class FeatureSelectionConfig(BaseModel):
    variance_threshold: float | None = None  # e.g. 0.0 to drop constant features
    correlation_threshold: float | None = None  # e.g. 0.90 to drop collinear features
    drop_features: List[str] = Field(default_factory=list)


class TrainTestSplitConfig(BaseModel):
    test_size: float = Field(default=0.2, ge=0.05, le=0.5)
    val_size: float = Field(default=0.0, ge=0.0, le=0.3)
    stratify: bool = True
    random_state: int = 42
    shuffle: bool = True


class PreprocessingConfig(BaseModel):
    target_column: str | None = None
    problem_type: str | None = None  # 'classification' | 'regression' | None
    numerical_features: List[NumericalFeatureConfig] = Field(default_factory=list)
    categorical_features: List[CategoricalFeatureConfig] = Field(default_factory=list)
    datetime_features: List[DatetimeFeatureConfig] = Field(default_factory=list)
    feature_selection: FeatureSelectionConfig = Field(default_factory=FeatureSelectionConfig)
    split_config: TrainTestSplitConfig = Field(default_factory=TrainTestSplitConfig)


class PreprocessingResponse(BaseModel):
    pipeline_id: str
    dataset_id: str
    dataset_name: str
    target_column: str | None = None
    problem_type: str | None = None
    original_shape: List[int]  # [rows, cols]
    train_shape: List[int]
    val_shape: List[int] | None = None
    test_shape: List[int]
    original_feature_count: int
    transformed_feature_count: int
    transformed_feature_names: List[str]
    dropped_features: List[str] = Field(default_factory=list)
    storage_path: str
    execution_time_ms: float
    train_preview: List[Dict[str, Any]] = Field(default_factory=list)
    columns: List[str] = Field(default_factory=list)


class PipelineSummaryItem(BaseModel):
    pipeline_id: str
    dataset_id: str
    target_column: str | None = None
    problem_type: str | None = None
    transformed_feature_count: int
    train_rows: int
    test_rows: int
    created_at: str
