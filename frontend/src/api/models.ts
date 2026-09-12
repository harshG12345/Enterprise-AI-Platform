/**
 * Axios API client for Model Registry, Governance, Promotion, and Leaderboards.
 */

import { apiClient } from './client';
import {
  ModelComparisonResponse,
  ModelDetailResponse,
  ModelLeaderboardItem,
  ModelPromotionPayload,
  ModelResponse,
} from '../types/models';

export const modelsApi = {
  /**
   * List all registered models with optional project, task, and status filtering.
   */
  listModels: async (params?: {
    project_id?: string;
    task_type?: string;
    status?: string;
  }): Promise<ModelResponse[]> => {
    const response = await apiClient.get<{ success: boolean; data: ModelResponse[] }>(
      '/models',
      { params }
    );
    return response.data.data;
  },

  /**
   * Retrieve complete model diagnostic details, feature importance, confusion matrix, and audit logs.
   */
  getModelDetails: async (modelId: string): Promise<ModelDetailResponse> => {
    const response = await apiClient.get<{ success: boolean; data: ModelDetailResponse }>(
      `/models/${modelId}`
    );
    return response.data.data;
  },

  /**
   * Promote model lifecycle stage (DEVELOPMENT -> STAGING -> PRODUCTION).
   */
  promoteModel: async (
    modelId: string,
    payload: ModelPromotionPayload
  ): Promise<ModelResponse> => {
    const response = await apiClient.post<{ success: boolean; data: ModelResponse }>(
      `/models/${modelId}/promote`,
      payload
    );
    return response.data.data;
  },

  /**
   * Rollback model to DEVELOPMENT stage.
   */
  rollbackModel: async (modelId: string): Promise<ModelResponse> => {
    const response = await apiClient.post<{ success: boolean; data: ModelResponse }>(
      `/models/${modelId}/rollback`
    );
    return response.data.data;
  },

  /**
   * Archive a model version.
   */
  archiveModel: async (modelId: string): Promise<ModelResponse> => {
    const response = await apiClient.post<{ success: boolean; data: ModelResponse }>(
      `/models/${modelId}/archive`
    );
    return response.data.data;
  },

  /**
   * Fetch model leaderboard ranked by generalization test performance score.
   */
  getLeaderboard: async (params?: {
    project_id?: string;
    task_type?: string;
  }): Promise<ModelLeaderboardItem[]> => {
    const response = await apiClient.get<{
      success: boolean;
      data: ModelLeaderboardItem[];
    }>('/models/leaderboard', { params });
    return response.data.data;
  },

  /**
   * Compare multiple models side-by-side.
   */
  compareModels: async (modelIds: string[]): Promise<ModelComparisonResponse> => {
    const response = await apiClient.post<{
      success: boolean;
      data: ModelComparisonResponse;
    }>('/models/compare', { model_ids: modelIds });
    return response.data.data;
  },

  /**
   * Trigger model artifact binary download.
   */
  downloadArtifactUrl: (modelId: string): string => {
    return `/api/v1/models/${modelId}/download`;
  },
};
