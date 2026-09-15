import { apiClient } from './client';
import {
  APIResponse,
  CreateNotificationPayload,
  Notification,
  NotificationBatchActionResponse,
  NotificationCategory,
  NotificationListResponse,
  NotificationType,
  UnreadCountResponse,
} from '../types';

export interface FetchNotificationParams {
  unread_only?: boolean;
  category?: NotificationCategory;
  notification_type?: NotificationType;
  page?: number;
  page_size?: number;
}

export const notificationsApi = {
  /**
   * Fetch paginated list of user notifications.
   */
  async getNotifications(params: FetchNotificationParams = {}): Promise<NotificationListResponse> {
    const res = await apiClient.get<APIResponse<NotificationListResponse>>('/notifications', {
      params,
    });
    return res.data.data;
  },

  /**
   * Get total count of unread notifications.
   */
  async getUnreadCount(): Promise<number> {
    const res = await apiClient.get<APIResponse<UnreadCountResponse>>('/notifications/unread-count');
    return res.data.data.unread_count;
  },

  /**
   * Create a new notification.
   */
  async createNotification(payload: CreateNotificationPayload): Promise<Notification> {
    const res = await apiClient.post<APIResponse<Notification>>('/notifications', payload);
    return res.data.data;
  },

  /**
   * Seed demo notifications for presentation / live showcase.
   */
  async seedDemoNotifications(): Promise<Notification[]> {
    const res = await apiClient.post<APIResponse<Notification[]>>('/notifications/seed-demo');
    return res.data.data;
  },

  /**
   * Mark a single notification as read.
   */
  async markAsRead(notificationId: string): Promise<Notification> {
    const res = await apiClient.patch<APIResponse<Notification>>(
      `/notifications/${notificationId}/read`
    );
    return res.data.data;
  },

  /**
   * Mark all unread notifications as read.
   */
  async markAllAsRead(): Promise<NotificationBatchActionResponse> {
    const res = await apiClient.post<APIResponse<NotificationBatchActionResponse>>(
      '/notifications/mark-all-read'
    );
    return res.data.data;
  },

  /**
   * Delete a single notification.
   */
  async deleteNotification(notificationId: string): Promise<NotificationBatchActionResponse> {
    const res = await apiClient.delete<APIResponse<NotificationBatchActionResponse>>(
      `/notifications/${notificationId}`
    );
    return res.data.data;
  },

  /**
   * Clear all user notifications.
   */
  async clearAll(): Promise<NotificationBatchActionResponse> {
    const res = await apiClient.delete<APIResponse<NotificationBatchActionResponse>>(
      '/notifications'
    );
    return res.data.data;
  },
};
