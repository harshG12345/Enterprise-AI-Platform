import { apiClient } from './client';
import { EDAResponse } from '../types/eda';

export interface APIResponse<T> {
  success: boolean;
  data: T;
  message?: string;
}

export const edaApi = {
  getDatasetEDA: async (datasetId: string): Promise<EDAResponse> => {
    const response = await apiClient.get<APIResponse<EDAResponse>>(`/datasets/${datasetId}/eda`);
    return response.data.data;
  },
};
