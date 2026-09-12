import { apiClient } from './client';
import { APIResponse } from '../types';
import { Dataset, DatasetDetail, DatasetListParams, DatasetPreview } from '../types/dataset';

export interface DatasetListResult {
  items: Dataset[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export const getDatasets = async (params?: DatasetListParams): Promise<APIResponse<DatasetListResult>> => {
  const response = await apiClient.get<APIResponse<DatasetListResult>>('/datasets', { params });
  return response.data;
};

export const getDataset = async (id: string): Promise<APIResponse<DatasetDetail>> => {
  const response = await apiClient.get<APIResponse<DatasetDetail>>(`/datasets/${id}`);
  return response.data;
};

export const getDatasetPreview = async (
  id: string,
  page: number = 1,
  pageSize: number = 50
): Promise<APIResponse<DatasetPreview>> => {
  const response = await apiClient.get<APIResponse<DatasetPreview>>(`/datasets/${id}/preview`, {
    params: { page, page_size: pageSize },
  });
  return response.data;
};

export const uploadDataset = async (
  projectId: string,
  file: File,
  onProgress?: (percent: number) => void
): Promise<APIResponse<Dataset>> => {
  const formData = new FormData();
  formData.append('project_id', projectId);
  formData.append('file', file);

  const response = await apiClient.post<APIResponse<Dataset>>('/datasets/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (progressEvent.total && onProgress) {
        const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(percent);
      }
    },
  });
  return response.data;
};

export const deleteDataset = async (id: string): Promise<APIResponse<null>> => {
  const response = await apiClient.delete<APIResponse<null>>(`/datasets/${id}`);
  return response.data;
};

export const datasetsApi = {
  getDatasets,
  getDataset,
  getDatasetPreview,
  uploadDataset,
  deleteDataset,
};

