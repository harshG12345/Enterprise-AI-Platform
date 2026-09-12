import { apiClient } from './client';
import { APIResponse } from '../types';
import { TokenData, User, UserRole } from '../types/auth';

export const registerUser = async (data: {
  email: string;
  full_name: string;
  password: string;
  role?: UserRole;
}): Promise<APIResponse<User>> => {
  const response = await apiClient.post<APIResponse<User>>('/auth/register', data);
  return response.data;
};

export const loginUser = async (data: {
  email: string;
  password: string;
}): Promise<APIResponse<TokenData>> => {
  const response = await apiClient.post<APIResponse<TokenData>>('/auth/login', data);
  return response.data;
};

export const getCurrentUser = async (): Promise<APIResponse<User>> => {
  const response = await apiClient.get<APIResponse<User>>('/users/me');
  return response.data;
};

export const changePassword = async (data: {
  current_password: string;
  new_password: string;
}): Promise<APIResponse<null>> => {
  const response = await apiClient.post<APIResponse<null>>('/auth/change-password', data);
  return response.data;
};
