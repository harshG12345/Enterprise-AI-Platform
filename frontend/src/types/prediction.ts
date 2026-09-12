/**
 * TypeScript definitions for Prediction and Inference Engine (Phase 12).
 */

export interface PredictionProbability {
  class_name: string;
  probability: number;
}

export interface RealtimePredictionPayload {
  model_id: string;
  features: Record<string, any>;
  include_probabilities?: boolean;
}

export interface RealtimePredictionResponse {
  prediction_id: string;
  model_id: string;
  model_name: string;
  model_version: string;
  task_type: 'classification' | 'regression';
  predicted_value: any;
  probabilities?: PredictionProbability[];
  latency_ms: number;
  timestamp: string;
}

export interface BatchPredictionPayload {
  model_id: string;
  project_id: string;
  dataset_id?: string;
  output_format?: string;
}

export interface BatchPredictionResponse {
  job_id: string;
  celery_task_id: string;
  model_id: string;
  status: string;
  message: string;
}

export interface PredictionHistoryItem {
  id: string;
  model_id: string;
  model_name?: string;
  task_type?: string;
  user_id?: string;
  input_data: Record<string, any>;
  prediction: {
    predicted_value: any;
    probabilities?: PredictionProbability[];
    task_type?: string;
  };
  latency_ms: number;
  created_at: string;
}

export interface PredictionTelemetryStats {
  total_predictions: number;
  average_latency_ms: number;
  p95_latency_ms: number;
  predictions_by_model: Record<string, number>;
}
