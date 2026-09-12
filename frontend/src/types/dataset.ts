export interface ColumnMeta {
  name: string;
  dtype: string;
  inferred_type: 'numeric' | 'categorical' | 'datetime' | 'boolean' | 'text';
  missing_count: number;
  missing_percentage: number;
  unique_count: number;
}

export interface Dataset {
  id: string;
  project_id: string;
  filename: string;
  file_size: number;
  row_count?: number | null;
  column_count?: number | null;
  status: 'PENDING' | 'PROCESSING' | 'VALIDATED' | 'ERROR';
  created_at: string;
  updated_at: string;
}

export interface DatasetDetail extends Dataset {
  schema_metadata?: {
    row_count: number;
    column_count: number;
    memory_bytes: number;
    columns: ColumnMeta[];
  } | null;
  columns: ColumnMeta[];
  memory_bytes?: number | null;
}

export interface DatasetPreview {
  columns: string[];
  rows: Record<string, unknown>[];
  total_rows: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface DatasetListParams {
  project_id?: string;
  page?: number;
  page_size?: number;
  search?: string;
}
