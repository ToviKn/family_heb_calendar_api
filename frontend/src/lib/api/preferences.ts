import { apiClient } from './axios';
import type { NotificationPreferences } from './types';

export async function getNotificationPreferences(): Promise<NotificationPreferences> {
  const { data } = await apiClient.get<NotificationPreferences>('/api/notification-preferences/');
  return data;
}

export async function updateNotificationPreferences(payload: Partial<NotificationPreferences>): Promise<NotificationPreferences> {
  const { data } = await apiClient.put<NotificationPreferences>('/api/notification-preferences/', payload);
  return data;
}
