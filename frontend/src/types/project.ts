export interface Project {
  id: string;
  name: string;
  description?: string | null;
  owner_id: string;
  owner_email?: string | null;
  owner_name?: string | null;
  dataset_count: number;
  model_count: number;
  experiment_count: number;
  created_at: string;
  updated_at: string;
}

export interface DatasetSummary {
  id: string;
  filename: string;
  file_size: number;
  row_count?: number | null;
  column_count?: number | null;
  status: string;
  created_at: string;
}

export interface ModelSummary {
  id: string;
  name: string;
  version: string;
  task_type: string;
  status: string;
  metrics?: Record<string, unknown> | null;
  created_at: string;
}

export interface ExperimentSummary {
  id: string;
  name: string;
  mlflow_experiment_id?: string | null;
  created_at: string;
}

export interface ProjectDetail extends Project {
  datasets: DatasetSummary[];
  models: ModelSummary[];
  experiments: ExperimentSummary[];
}

export interface ProjectListParams {
  page?: number;
  page_size?: number;
  search?: string;
}
