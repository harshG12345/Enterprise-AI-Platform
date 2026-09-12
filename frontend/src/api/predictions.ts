/**
 * Axios API client for Prediction & Inference Studio (Real-time and Batch).
 */

import { apiClient } from './client';
import {
  BatchPredictionPayload,
  BatchPredictionResponse,
  PredictionHistoryItem,
  PredictionTelemetryStats,
  RealtimePredictionPayload,
  RealtimePredictionResponse,
} from '../types/prediction';

export const predictionsApi = {
  /**
   * Execute low-latency real-time single record prediction.
   */
  predictRealtime: async (
    payload: RealtimePredictionPayload
  ): Promise<RealtimePredictionResponse> => {
    const response = await apiClient.post<{
      success: boolean;
      data: RealtimePredictionResponse;
    }>('/predictions/realtime', payload);
    return response.data.data;
  },

  /**
   * Direct inference targeting a specific model.
   */
  predictForModel: async (
    modelId: string,
    features: Record<string, any>,
    includeProbabilities: boolean = true
  ): Promise<RealtimePredictionResponse> => {
    const response = await apiClient.post<{
      success: boolean;
      data: RealtimePredictionResponse;
    }>(`/predictions/models/${modelId}/predict`, features, {
      params: { include_probabilities: includeProbabilities },
    });
    return response.data.data;
  },

  /**
   * Launch background asynchronous batch inference job.
   */
  launchBatchPrediction: async (
    payload: BatchPredictionPayload
  ): Promise<BatchPredictionResponse> => {
    const response = await apiClient.post<{
      success: boolean;
      data: BatchPredictionResponse;
    }>('/predictions/batch', payload);
    return response.data.data;
  },

  /**
   * Upload tabular file (CSV/XLSX) and launch background batch inference.
   */
  launchBatchPredictionUpload: async (
    modelId: string,
    projectId: string,
    file: File
  ): Promise<BatchPredictionResponse> => {
    const formData = new FormData();
    formData.append('model_id', modelId);
    formData.append('project_id', projectId);
    formData.append('file', file);

    const response = await apiClient.post<{
      success: boolean;
      data: BatchPredictionResponse;
    }>('/predictions/batch/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data.data;
  },

  /**
   * Retrieve historical prediction audit logs.
   */
  getPredictionHistory: async (params?: {
    project_id?: string;
    model_id?: string;
    limit?: number;
  }): Promise<PredictionHistoryItem[]> => {
    const response = await apiClient.get<{
      success: boolean;
      data: PredictionHistoryItem[];
    }>('/predictions', { params });
    return response.data.data;
  },

  /**
   * Get inference throughput and latency telemetry statistics.
   */
  getPredictionStats: async (
    projectId?: string
  ): Promise<PredictionTelemetryStats> => {
    const response = await apiClient.get<{
      success: boolean;
      data: PredictionTelemetryStats;
    }>('/predictions/stats', {
      params: { project_id: projectId },
    });
    return response.data.data;
  },

  /**
   * Generate result CSV download URL.
   */
  downloadBatchResultsUrl: (jobId: string): string => {
    return `/api/v1/predictions/batch/${jobId}/download`;
  },
};
