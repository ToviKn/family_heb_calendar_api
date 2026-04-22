import { apiClient } from './axios';
import type {
  NotificationCreate,
  NotificationListResponse,
  NotificationResponse,
} from './types';

export interface ProcessRemindersResponse {
  created: number;
}

export async function getNotifications(): Promise<NotificationListResponse> {
  const { data } = await apiClient.get<NotificationListResponse>('/notifications/');
  return data;
}

export async function createNotification(payload: NotificationCreate): Promise<NotificationResponse> {
  const { data } = await apiClient.post<NotificationResponse>('/notifications/', payload);
  return data;
}

export async function markNotificationRead(notificationId: number): Promise<NotificationResponse> {
  const { data } = await apiClient.patch<NotificationResponse>(`/notifications/${notificationId}/read`);
  return data;
}

export async function deleteNotification(notificationId: number): Promise<void> {
  await apiClient.delete(`/notifications/${notificationId}`);
}

export async function processNotificationReminders(): Promise<ProcessRemindersResponse> {
  const { data } = await apiClient.post<ProcessRemindersResponse>('/notifications/reminders/process');
  return data;
}
