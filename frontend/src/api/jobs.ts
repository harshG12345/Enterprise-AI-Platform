/**
 * Axios API client for Celery background job status polling and job history.
 */

import { apiClient } from './client';
import { JobStatusData } from '../types/job';

export const jobsApi = {
  /**
   * Poll live background job execution status, worker error message, or completed model metrics.
   */
  getJobStatus: async (jobId: string): Promise<JobStatusData> => {
    const response = await apiClient.get<{ success: boolean; data: JobStatusData }>(
      `/jobs/${jobId}`
    );
    return response.data.data;
  },

  /**
   * List all background jobs for a project or user.
   */
  listJobs: async (projectId?: string): Promise<JobStatusData[]> => {
    const response = await apiClient.get<{ success: boolean; data: JobStatusData[] }>(
      '/jobs',
      {
        params: projectId ? { project_id: projectId } : undefined,
      }
    );
    return response.data.data;
  },
};
