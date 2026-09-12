export type NumericalImputer = 'mean' | 'median' | 'most_frequent' | 'constant';
export type NumericalScaler = 'standard' | 'minmax' | 'robust' | 'maxabs' | 'none';
export type NumericalPowerTransform = 'none' | 'log1p' | 'yeo_johnson';

export type CategoricalImputer = 'most_frequent' | 'constant';
export type CategoricalEncoder = 'onehot' | 'ordinal' | 'target' | 'frequency';

export type DatetimePart = 'year' | 'month' | 'day' | 'dayofweek' | 'hour' | 'is_weekend' | 'quarter';

export interface NumericalFeatureConfig {
  column_name: string;
  imputer: NumericalImputer;
  imputer_fill_value?: number | null;
  scaler: NumericalScaler;
  power_transform: NumericalPowerTransform;
  clip_outliers: boolean;
  lower_percentile: number;
  upper_percentile: number;
}

export interface CategoricalFeatureConfig {
  column_name: string;
  imputer: CategoricalImputer;
  imputer_fill_value: string;
  encoder: CategoricalEncoder;
  max_categories?: number | null;
  handle_unknown: 'ignore' | 'error';
}

export interface DatetimeFeatureConfig {
  column_name: string;
  extracted_parts: DatetimePart[];
  cyclical_encoding: boolean;
  drop_original: boolean;
}

export interface FeatureSelectionConfig {
  variance_threshold?: number | null;
  correlation_threshold?: number | null;
  drop_features: string[];
}

export interface TrainTestSplitConfig {
  test_size: number;
  val_size: number;
  stratify: boolean;
  random_state: number;
  shuffle: boolean;
}

export interface PreprocessingConfig {
  target_column?: string | null;
  problem_type?: 'classification' | 'regression' | null;
  numerical_features: NumericalFeatureConfig[];
  categorical_features: CategoricalFeatureConfig[];
  datetime_features: DatetimeFeatureConfig[];
  feature_selection: FeatureSelectionConfig;
  split_config: TrainTestSplitConfig;
}

export interface PreprocessingResponse {
  pipeline_id: string;
  dataset_id: string;
  dataset_name: string;
  target_column?: string | null;
  problem_type?: string | null;
  original_shape: [number, number];
  train_shape: [number, number];
  val_shape?: [number, number] | null;
  test_shape: [number, number];
  original_feature_count: number;
  transformed_feature_count: number;
  transformed_feature_names: string[];
  dropped_features: string[];
  storage_path: string;
  execution_time_ms: number;
  train_preview: Record<string, any>[];
  columns: string[];
}

export interface PipelineSummaryItem {
  pipeline_id: string;
  dataset_id: string;
  target_column?: string | null;
  problem_type?: string | null;
  transformed_feature_count: number;
  train_rows: number;
  test_rows: number;
  created_at: string;
}
