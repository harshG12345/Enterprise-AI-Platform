import { apiClient } from './client';
import {
  ArtifactItem,
  Experiment,
  ExperimentCreate,
  MetricHistoryItem,
  RunComparisonResponse,
  RunDetail,
} from '../types/experiment';

export interface APIResponse<T> {
  success: boolean;
  data: T;
  message?: string;
}

export const experimentsApi = {
  getExperiments: async (projectId?: string): Promise<Experiment[]> => {
    const url = projectId ? `/experiments?project_id=${projectId}` : '/experiments';
    const response = await apiClient.get<APIResponse<Experiment[]>>(url);
    return response.data.data;
  },

  getExperiment: async (experimentId: string): Promise<Experiment> => {
    const response = await apiClient.get<APIResponse<Experiment>>(`/experiments/${experimentId}`);
    return response.data.data;
  },

  createExperiment: async (payload: ExperimentCreate): Promise<Experiment> => {
    const response = await apiClient.post<APIResponse<Experiment>>('/experiments', payload);
    return response.data.data;
  },

  getExperimentRuns: async (experimentId: string): Promise<RunDetail[]> => {
    const response = await apiClient.get<APIResponse<RunDetail[]>>(`/experiments/${experimentId}/runs`);
    return response.data.data;
  },

  getRunDetails: async (runId: string): Promise<RunDetail> => {
    const response = await apiClient.get<APIResponse<RunDetail>>(`/experiments/runs/${runId}`);
    return response.data.data;
  },

  getMetricHistory: async (runId: string, metricKey: string): Promise<MetricHistoryItem[]> => {
    const response = await apiClient.get<APIResponse<MetricHistoryItem[]>>(
      `/experiments/runs/${runId}/metrics/${metricKey}`
    );
    return response.data.data;
  },

  getRunArtifacts: async (runId: string, path?: string): Promise<ArtifactItem[]> => {
    const url = path
      ? `/experiments/runs/${runId}/artifacts?path=${encodeURIComponent(path)}`
      : `/experiments/runs/${runId}/artifacts`;
    const response = await apiClient.get<APIResponse<ArtifactItem[]>>(url);
    return response.data.data;
  },

  compareRuns: async (runIds: string[]): Promise<RunComparisonResponse> => {
    const response = await apiClient.post<APIResponse<RunComparisonResponse>>('/experiments/compare', {
      run_ids: runIds,
    });
    return response.data.data;
  },
};
