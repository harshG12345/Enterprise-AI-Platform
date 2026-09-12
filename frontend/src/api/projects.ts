import { apiClient } from './client';
import { APIResponse } from '../types';
import { Project, ProjectDetail, ProjectListParams } from '../types/project';

export interface ProjectListResult {
  items: Project[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export const getProjects = async (params?: ProjectListParams): Promise<APIResponse<ProjectListResult>> => {
  const response = await apiClient.get<APIResponse<ProjectListResult>>('/projects', { params });
  return response.data;
};

export const getProject = async (id: string): Promise<APIResponse<ProjectDetail>> => {
  const response = await apiClient.get<APIResponse<ProjectDetail>>(`/projects/${id}`);
  return response.data;
};

export const createProject = async (data: {
  name: string;
  description?: string;
}): Promise<APIResponse<Project>> => {
  const response = await apiClient.post<APIResponse<Project>>('/projects', data);
  return response.data;
};

export const updateProject = async (
  id: string,
  data: { name?: string; description?: string }
): Promise<APIResponse<Project>> => {
  const response = await apiClient.put<APIResponse<Project>>(`/projects/${id}`, data);
  return response.data;
};

export const deleteProject = async (id: string): Promise<APIResponse<null>> => {
  const response = await apiClient.delete<APIResponse<null>>(`/projects/${id}`);
  return response.data;
};
