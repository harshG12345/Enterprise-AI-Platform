/**
 * TypeScript interfaces for MLflow Experiment Tracking, Runs, Metrics, and Comparisons.
 */

export interface Experiment {
  id: string;
  project_id: string;
  dataset_id?: string;
  name: string;
  mlflow_experiment_id?: string;
  run_count: number;
  created_at: string;
}

export interface ExperimentCreate {
  project_id: string;
  name: string;
  dataset_id?: string;
  tags?: Record<string, string>;
}

export interface ArtifactItem {
  path: string;
  is_dir: boolean;
  file_size_bytes: number;
}

export interface MetricHistoryItem {
  step: number;
  value: number;
  timestamp: string;
}

export interface RunDetail {
  run_id: string;
  experiment_id: string;
  run_name: string;
  status: 'RUNNING' | 'FINISHED' | 'FAILED' | 'KILLED';
  started_at: string;
  end_time?: string;
  duration_ms?: number;
  parameters: Record<string, unknown>;
  metrics: Record<string, number>;
  tags: Record<string, string>;
  artifacts: ArtifactItem[];
}

export interface RunComparisonItem {
  run_id: string;
  run_name: string;
  status: string;
  duration_ms?: number;
  parameters: Record<string, unknown>;
  metrics: Record<string, number>;
  tags: Record<string, string>;
  created_at: string;
}

export interface RunComparisonResponse {
  runs: RunComparisonItem[];
  common_parameters: Record<string, unknown>;
  differing_parameters: string[];
  all_metrics: string[];
  metric_matrix: Record<string, Record<string, number | null>>;
}
