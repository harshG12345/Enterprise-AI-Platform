import { apiClient } from './client';
import { APIResponse, HealthData, ReadinessData } from '../types';

export const getHealth = async (): Promise<APIResponse<HealthData>> => {
  const response = await apiClient.get<APIResponse<HealthData>>('/health');
  return response.data;
};

export const getReadiness = async (): Promise<APIResponse<ReadinessData>> => {
  const response = await apiClient.get<APIResponse<ReadinessData>>('/health/ready');
  return response.data;
};
