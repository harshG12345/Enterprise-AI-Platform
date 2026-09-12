from typing import List

from pydantic import BaseModel, Field


class DatasetOverviewStats(BaseModel):
    total_rows: int
    total_columns: int
    memory_usage_bytes: int
    memory_usage_human: str
    duplicate_rows_count: int
    duplicate_rows_percentage: float
    total_cells: int
    total_missing_cells: int
    missing_cells_percentage: float
    numerical_columns_count: int
    categorical_columns_count: int
    datetime_columns_count: int
    boolean_columns_count: int


class ColumnMissingSummary(BaseModel):
    column_name: str
    data_type: str
    missing_count: int
    missing_percentage: float
    valid_count: int
    valid_percentage: float


class HistogramBin(BaseModel):
    bin_start: float
    bin_end: float
    label: str
    count: int


class BoxPlotData(BaseModel):
    min: float
    q1: float
    median: float
    q3: float
    max: float
    iqr: float
    lower_whisker: float
    upper_whisker: float
    outliers_count: int
    outliers_sample: List[float] = Field(default_factory=list)


class NumericalColumnStats(BaseModel):
    column_name: str
    count: int
    mean: float
    std: float
    variance: float
    min: float
    q25: float
    median: float
    q75: float
    max: float
    iqr: float
    skewness: float
    kurtosis: float
    zeros_count: int
    zeros_percentage: float
    negative_count: int
    outliers_iqr_count: int
    outliers_zscore_count: int
    histogram: List[HistogramBin] = Field(default_factory=list)
    boxplot: BoxPlotData


class CategoryFrequency(BaseModel):
    value: str
    count: int
    percentage: float


class CategoricalColumnStats(BaseModel):
    column_name: str
    count: int
    unique_count: int
    unique_ratio: float
    top_value: str | None = None
    top_frequency: int | None = None
    top_percentage: float | None = None
    frequencies: List[CategoryFrequency] = Field(default_factory=list)
    is_high_cardinality: bool = False


class CorrelationCell(BaseModel):
    feature_x: str
    feature_y: str
    correlation: float


class CorrelationMatrix(BaseModel):
    method: str  # 'pearson' | 'spearman'
    features: List[str]
    matrix: List[List[float | None]]
    pairwise_pairs: List[CorrelationCell] = Field(default_factory=list)


class DataHealthWarning(BaseModel):
    code: str  # 'HIGH_MISSING' | 'HIGH_CARDINALITY' | 'CONSTANT_COLUMN' | 'HIGH_COLLINEARITY' | 'HIGH_SKEW' | 'DUPLICATE_ROWS'
    level: str  # 'warning' | 'critical' | 'info'
    column: str | None = None
    columns: List[str] | None = None
    message: str
    suggestion: str


class EDAResponse(BaseModel):
    dataset_id: str
    dataset_name: str
    overview: DatasetOverviewStats
    missing_summary: List[ColumnMissingSummary] = Field(default_factory=list)
    numerical_features: List[NumericalColumnStats] = Field(default_factory=list)
    categorical_features: List[CategoricalColumnStats] = Field(default_factory=list)
    pearson_correlation: CorrelationMatrix | None = None
    spearman_correlation: CorrelationMatrix | None = None
    health_warnings: List[DataHealthWarning] = Field(default_factory=list)
