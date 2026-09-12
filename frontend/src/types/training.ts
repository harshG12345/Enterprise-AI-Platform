/**
 * Types for ML Model Training, Cross Validation, and Diagnostic Evaluation.
 */

export type TaskType = 'classification' | 'regression';

export type ModelAlgorithm =
  | 'random_forest_classifier'
  | 'gradient_boosting_classifier'
  | 'logistic_regression'
  | 'decision_tree_classifier'
  | 'knn_classifier'
  | 'random_forest_regressor'
  | 'gradient_boosting_regressor'
  | 'linear_regression'
  | 'ridge_regression'
  | 'decision_tree_regressor'
  | 'knn_regressor';

export interface HyperparameterProperty {
  type: 'int' | 'float' | 'string';
  min?: number;
  max?: number;
  default: number | string;
}

export interface AlgorithmInfo {
  algorithm: string;
  name: string;
  task_type: TaskType;
  description: string;
  default_hyperparameters: Record<string, number | string>;
  hyperparameter_schema: Record<string, HyperparameterProperty>;
}

export interface CrossValidationConfig {
  n_splits: number;
  stratify: boolean;
  shuffle: boolean;
  random_state: number;
}

export interface TrainingJobCreate {
  project_id: string;
  dataset_id: string;
  pipeline_id?: string;
  target_column: string;
  task_type: TaskType;
  algorithm: string;
  hyperparameters: Record<string, number | string>;
  cv_config?: CrossValidationConfig;
  model_name?: string;
}

export interface EvaluationMetrics {
  // Classification
  accuracy?: number;
  precision?: number;
  recall?: number;
  f1_score?: number;
  roc_auc?: number;
  log_loss?: number;
  // Regression
  mse?: number;
  rmse?: number;
  mae?: number;
  r2_score?: number;
  explained_variance?: number;
}

export interface ConfusionMatrixData {
  labels: string[];
  matrix: number[][];
  normalized_matrix: number[][];
}

export interface CurvePoint {
  x: number;
  y: number;
  threshold?: number;
}

export interface CVFoldResult {
  fold: number;
  train_score: number;
  val_score: number;
  metrics: Record<string, number>;
}

export interface CVSummary {
  mean_val_score: number;
  std_val_score: number;
  folds: CVFoldResult[];
}

export interface FeatureImportanceItem {
  feature: string;
  importance: number;
  rank: number;
}

export interface ResidualPoint {
  actual: number;
  predicted: number;
  residual: number;
}

export interface TrainingJobDetailResponse {
  id: string;
  project_id: string;
  dataset_id: string;
  model_id?: string;
  status: string;
  algorithm: string;
  task_type: TaskType;
  target_column: string;
  hyperparameters: Record<string, unknown>;
  train_metrics: EvaluationMetrics;
  test_metrics: EvaluationMetrics;
  cv_summary?: CVSummary;
  feature_importances: FeatureImportanceItem[];
  confusion_matrix?: ConfusionMatrixData;
  roc_curve: CurvePoint[];
  residuals_sample: ResidualPoint[];
  training_duration_ms: number;
  artifact_path?: string;
  created_at: string;
}

export interface TrainingJobListItem {
  id: string;
  project_id: string;
  project_name: string;
  dataset_id: string;
  dataset_name: string;
  target_column: string;
  task_type: TaskType;
  status: 'PENDING' | 'RUNNING' | 'SUCCESS' | 'FAILED' | 'CANCELLED';
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
}
