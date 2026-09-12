import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import { APIErrorResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Request Interceptor: Attach Auth Token and correlation IDs
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('auth_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Safe error formatting
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<APIErrorResponse>) => {
    if (error.response?.status === 401) {
      // Clear token on 401 unauthenticated
      localStorage.removeItem('auth_token');
    }
    const safeError = {
      message:
        error.response?.data?.error?.message ||
        error.message ||
        'An unexpected network error occurred.',
      code: error.response?.data?.error?.code || 'NETWORK_ERROR',
      status: error.response?.status,
    };
    return Promise.reject(safeError);
  }
);
