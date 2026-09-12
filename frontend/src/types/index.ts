/**
 * Standard enterprise API response envelope.
 */
export interface APIResponse<T> {
  success: boolean;
  data: T;
  message: string;
  request_id?: string;
}

export interface APIErrorResponse {
  success: boolean;
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
  request_id?: string;
}

export interface HealthData {
  status: string;
  version: string;
  app_name: string;
  environment: string;
  timestamp: string;
}

export interface ReadinessData {
  status: string;
  database: string;
  redis: string;
  mlflow: string;
  timestamp: string;
}

export * from './auth';
export * from './project';
export * from './dataset';
export * from './eda';
export * from './preprocessor';
export * from './training';
export * from './experiment';
