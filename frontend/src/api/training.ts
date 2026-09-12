import { apiClient } from './client';
import {
  AlgorithmInfo,
  TrainingJobCreate,
  TrainingJobDetailResponse,
  TrainingJobListItem,
} from '../types/training';

export interface APIResponse<T> {
  success: boolean;
  data: T;
  message?: string;
}

export const trainingApi = {
  getAlgorithms: async (): Promise<AlgorithmInfo[]> => {
    const response = await apiClient.get<APIResponse<AlgorithmInfo[]>>('/training/algorithms');
    return response.data.data;
  },

  trainModel: async (payload: TrainingJobCreate): Promise<TrainingJobDetailResponse> => {
    const response = await apiClient.post<APIResponse<TrainingJobDetailResponse>>(
      '/training/train',
      payload
    );
    return response.data.data;
  },

  trainModelAsync: async (payload: TrainingJobCreate): Promise<{ job_id: string; celery_task_id?: string; status: string; message: string }> => {
    const response = await apiClient.post<APIResponse<{ job_id: string; celery_task_id?: string; status: string; message: string }>>(
      '/training/train-async',
      payload
    );
    return response.data.data;
  },

  getTrainingJobs: async (projectId?: string): Promise<TrainingJobListItem[]> => {
    const url = projectId ? `/training/jobs?project_id=${projectId}` : '/training/jobs';
    const response = await apiClient.get<APIResponse<TrainingJobListItem[]>>(url);
    return response.data.data;
  },
};
