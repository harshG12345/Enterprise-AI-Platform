/**
 * TypeScript definitions for Monitoring, Observability, and Statistical Drift (Phase 13).
 */

export interface HistogramBin {
  bin_label: string;
  baseline_pct: number;
  current_pct: number;
}

export interface FeatureDriftReport {
  feature_name: string;
  feature_type: 'numerical' | 'categorical';
  drift_detected: boolean;
  psi_score: number;
  primary_test: string;
  test_statistic: number;
  p_value: number;
  wasserstein_distance?: number;
  histogram_bins: HistogramBin[];
  baseline_stats: Record<string, any>;
  current_stats: Record<string, any>;
}

export interface ModelDriftAnalysisResponse {
  model_id: string;
  model_name: string;
  model_version: string;
  task_type: string;
  health_status: 'HEALTHY' | 'WARNING' | 'DRIFT_DETECTED';
  drift_score: number;
  drift_percentage: number;
  total_features: number;
  drifted_features_count: number;
  max_psi: number;
  baseline_sample_count: number;
  current_sample_count: number;
  feature_reports: FeatureDriftReport[];
  analyzed_at: string;
}

export interface ModelMonitoringOverview {
  model_id: string;
  model_name: string;
  model_version: string;
  status: string;
  health_status: 'HEALTHY' | 'WARNING' | 'DRIFT_DETECTED';
  total_inferences: number;
  max_psi: number;
  drifted_features_count: number;
  last_inference_at?: string;
}

export interface CustomDriftAnalysisPayload {
  current_dataset_id?: string;
  alpha?: number;
  psi_threshold?: number;
}
