export interface DatasetOverviewStats {
  total_rows: number;
  total_columns: number;
  memory_usage_bytes: number;
  memory_usage_human: string;
  duplicate_rows_count: number;
  duplicate_rows_percentage: number;
  total_cells: number;
  total_missing_cells: number;
  missing_cells_percentage: number;
  numerical_columns_count: number;
  categorical_columns_count: number;
  datetime_columns_count: number;
  boolean_columns_count: number;
}

export interface ColumnMissingSummary {
  column_name: string;
  data_type: string;
  missing_count: number;
  missing_percentage: number;
  valid_count: number;
  valid_percentage: number;
}

export interface HistogramBin {
  bin_start: number;
  bin_end: number;
  label: string;
  count: number;
}

export interface BoxPlotData {
  min: number;
  q1: number;
  median: number;
  q3: number;
  max: number;
  iqr: number;
  lower_whisker: number;
  upper_whisker: number;
  outliers_count: number;
  outliers_sample: number[];
}

export interface NumericalColumnStats {
  column_name: string;
  count: number;
  mean: number;
  std: number;
  variance: number;
  min: number;
  q25: number;
  median: number;
  q75: number;
  max: number;
  iqr: number;
  skewness: number;
  kurtosis: number;
  zeros_count: number;
  zeros_percentage: number;
  negative_count: number;
  outliers_iqr_count: number;
  outliers_zscore_count: number;
  histogram: HistogramBin[];
  boxplot: BoxPlotData;
}

export interface CategoryFrequency {
  value: string;
  count: number;
  percentage: number;
}

export interface CategoricalColumnStats {
  column_name: string;
  count: number;
  unique_count: number;
  unique_ratio: number;
  top_value: string | null;
  top_frequency: number | null;
  top_percentage: number | null;
  frequencies: CategoryFrequency[];
  is_high_cardinality: boolean;
}

export interface CorrelationCell {
  feature_x: string;
  feature_y: string;
  correlation: number;
}

export interface CorrelationMatrix {
  method: 'pearson' | 'spearman';
  features: string[];
  matrix: (number | null)[][];
  pairwise_pairs: CorrelationCell[];
}

export interface DataHealthWarning {
  code: string;
  level: 'warning' | 'critical' | 'info';
  column?: string | null;
  columns?: string[] | null;
  message: string;
  suggestion: string;
}

export interface EDAResponse {
  dataset_id: string;
  dataset_name: string;
  overview: DatasetOverviewStats;
  missing_summary: ColumnMissingSummary[];
  numerical_features: NumericalColumnStats[];
  categorical_features: CategoricalColumnStats[];
  pearson_correlation?: CorrelationMatrix | null;
  spearman_correlation?: CorrelationMatrix | null;
  health_warnings: DataHealthWarning[];
}
