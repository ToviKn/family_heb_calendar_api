import type { NotificationResponse } from '../api';

export interface NotificationSummary {
  title: string;
  subtitle: string;
}

export function formatNotificationCreatedAt(value: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleString();
}

export function getNotificationSummary(notification: NotificationResponse): NotificationSummary {
  if (notification.type === 'EVENT_REMINDER' || notification.type === 'event reminder') {
    const reminderMatch = notification.message.match(/^Reminder:\s*(.+?)\s+on\s+(.+)$/i);
    if (reminderMatch) {
      return {
        title: `Reminder: ${reminderMatch[1]}`,
        subtitle: `Scheduled for ${reminderMatch[2]}`,
      };
    }

    return {
      title: 'Event reminder',
      subtitle: notification.message,
    };
  }

  if (notification.type === 'invite') {
    return {
      title: 'Family invitation',
      subtitle: notification.message,
    };
  }

  return {
    title: notification.message,
    subtitle: `Type: ${notification.type}`,
  };
}
