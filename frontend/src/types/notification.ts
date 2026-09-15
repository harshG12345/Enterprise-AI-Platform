export type NotificationType = 'INFO' | 'SUCCESS' | 'WARNING' | 'ERROR';

export type NotificationCategory = 'TRAINING' | 'DATASET' | 'DRIFT' | 'MODEL' | 'SECURITY' | 'SYSTEM';

export interface Notification {
  id: string;
  user_id: string;
  title: string;
  message: string;
  type: NotificationType;
  category: NotificationCategory;
  link?: string | null;
  is_read: boolean;
  created_at: string;
  read_at?: string | null;
}

export interface NotificationListResponse {
  items: Notification[];
  total: number;
  unread_count: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface UnreadCountResponse {
  unread_count: number;
}

export interface NotificationBatchActionResponse {
  success: boolean;
  message: string;
  affected_count: number;
}

export interface CreateNotificationPayload {
  title: string;
  message: string;
  type?: NotificationType;
  category?: NotificationCategory;
  link?: string | null;
}
