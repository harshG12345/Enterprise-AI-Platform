import { apiClient } from './client';
import {
  PipelineSummaryItem,
  PreprocessingConfig,
  PreprocessingResponse,
} from '../types/preprocessor';

export interface APIResponse<T> {
  success: boolean;
  data: T;
  message?: string;
}

export const preprocessorApi = {
  validateConfig: async (
    datasetId: string,
    config: PreprocessingConfig
  ): Promise<{ valid: boolean; columns_configured: number }> => {
    const response = await apiClient.post<APIResponse<{ valid: boolean; columns_configured: number }>>(
      `/datasets/${datasetId}/preprocess/validate`,
      config
    );
    return response.data.data;
  },

  executePreprocessing: async (
    datasetId: string,
    config: PreprocessingConfig
  ): Promise<PreprocessingResponse> => {
    const response = await apiClient.post<APIResponse<PreprocessingResponse>>(
      `/datasets/${datasetId}/preprocess`,
      config
    );
    return response.data.data;
  },

  listPipelines: async (datasetId: string): Promise<PipelineSummaryItem[]> => {
    const response = await apiClient.get<APIResponse<PipelineSummaryItem[]>>(
      `/datasets/${datasetId}/pipelines`
    );
    return response.data.data;
  },
};
