/**
 * TypeScript definitions for Model Registry, Governance Stages, and Leaderboards.
 */

export type ModelLifecycleStatus = 'NONE' | 'DEVELOPMENT' | 'STAGING' | 'PRODUCTION' | 'ARCHIVED';

export interface ModelResponse {
  id: string;
  project_id: string;
  project_name?: string;
  dataset_id?: string;
  dataset_name?: string;
  experiment_id?: string;
  name: string;
  version: string;
  task_type: 'classification' | 'regression';
  framework: string;
  metrics?: {
    train?: Record<string, number>;
    test?: Record<string, number>;
    cv?: {
      mean_val_score: number;
      std_val_score: number;
      folds: Array<{ fold: number; train_score: number; val_score: number }>;
    };
    duration_ms?: number;
  };
  artifact_path: string;
  mlflow_run_id?: string;
  status: ModelLifecycleStatus;
  created_at: string;
}

export interface AuditHistoryItem {
  id: string;
  action: string;
  user_id: string;
  metadata: Record<string, any>;
  created_at: string;
}

export interface ModelDetailResponse extends ModelResponse {
  algorithm?: string;
  target_column?: string;
  feature_names: string[];
  hyperparameters: Record<string, any>;
  confusion_matrix?: {
    labels: string[];
    matrix: number[][];
    normalized_matrix: number[][];
  };
  feature_importances: Array<{
    feature: string;
    importance: number;
    rank: number;
  }>;
  audit_history: AuditHistoryItem[];
}

export interface ModelLeaderboardItem {
  rank: number;
  id: string;
  name: string;
  version: string;
  status: ModelLifecycleStatus;
  task_type: 'classification' | 'regression';
  primary_metric_name: string;
  primary_metric_value: number;
  secondary_metric_name?: string;
  secondary_metric_value?: number;
  training_duration_ms?: number;
  created_at: string;
}

export interface ModelPromotionPayload {
  status: ModelLifecycleStatus;
  notes?: string;
}

export interface ModelComparisonResponse {
  models: ModelDetailResponse[];
  all_metrics: string[];
  metric_matrix: Record<string, Record<string, number | null>>;
  differing_hyperparameters: string[];
  common_hyperparameters: Record<string, any>;
}
