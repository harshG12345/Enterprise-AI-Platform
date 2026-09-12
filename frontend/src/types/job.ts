/**
 * Type definitions for Celery Background Jobs and Live Status Polling.
 */

export interface JobStatusData {
  id: string;
  project_id: string;
  project_name?: string;
  dataset_id: string;
  dataset_name?: string;
  user_id: string;
  status: 'PENDING' | 'RUNNING' | 'SUCCESS' | 'FAILED' | 'CANCELLED';
  target_column: string;
  task_type: 'classification' | 'regression';
  celery_task_id?: string;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
  model_id?: string;
  metrics?: Record<string, any>;
  artifact_path?: string;
}

export interface AsyncTrainingLaunchData {
  job_id: string;
  celery_task_id?: string;
  status: string;
  message: string;
}
