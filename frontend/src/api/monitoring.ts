/**
 * Axios API client for Observability and Statistical Drift Engine (Phase 13).
 */

import { apiClient } from './client';
import {
  CustomDriftAnalysisPayload,
  ModelDriftAnalysisResponse,
  ModelMonitoringOverview,
} from '../types/monitoring';

export const monitoringApi = {
  /**
   * Retrieve observability overview of all models across a project or workspace.
   */
  getMonitoringOverview: async (
    projectId?: string
  ): Promise<ModelMonitoringOverview[]> => {
    const response = await apiClient.get<{
      success: boolean;
      data: ModelMonitoringOverview[];
    }>('/monitoring/overview', {
      params: { project_id: projectId },
    });
    return response.data.data;
  },

  /**
   * Compute comprehensive feature drift diagnostics (KS-test, PSI, Wasserstein distance).
   */
  getModelDrift: async (
    modelId: string,
    params?: { alpha?: number; psi_threshold?: number }
  ): Promise<ModelDriftAnalysisResponse> => {
    const response = await apiClient.get<{
      success: boolean;
      data: ModelDriftAnalysisResponse;
    }>(`/monitoring/models/${modelId}/drift`, { params });
    return response.data.data;
  },

  /**
   * Run custom drift analysis comparing model baseline against an uploaded/selected evaluation dataset.
   */
  analyzeCustomDrift: async (
    modelId: string,
    payload: CustomDriftAnalysisPayload
  ): Promise<ModelDriftAnalysisResponse> => {
    const response = await apiClient.post<{
      success: boolean;
      data: ModelDriftAnalysisResponse;
    }>(`/monitoring/models/${modelId}/drift/analyze`, payload);
    return response.data.data;
  },
};
