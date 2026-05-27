import type { TFunction } from 'i18next';

import type { NotificationResponse } from '../api';
import { isHebrewCalendarType } from '../dates/eventDateFormatter';
import { formatHebrewDate, formatHebrewDateNumeric } from '../dates/hebrewDateFormatter';
export interface NotificationSummary {
  title: string;
  subtitle: string;
  direction: 'rtl' | 'ltr';
}

interface NotificationMetadata {
  date?: string;
  event_title?: string;
  calendar_type?: string;
  formatted_hebrew_date?: string;
}

function getNotificationMetadata(notification: NotificationResponse): NotificationMetadata {
  if (notification.metadata && typeof notification.metadata === 'object') {
    return notification.metadata as NotificationMetadata;
  }
  if (notification.metadata_json && typeof notification.metadata_json === 'object') {
    return notification.metadata_json as NotificationMetadata;
  }
  return {};
}


function parseNumericHebrewDate(value: string): { day: number; month: number; year: number } | null {
  const match = value.trim().match(/^(\d{1,2})\/(\d{1,2})\/(\d{2,4})$/);
  if (!match) {
    return null;
  }

  const day = Number(match[1]);
  const month = Number(match[2]);
  const year = Number(match[3]);

  if ([day, month, year].some((part) => Number.isNaN(part))) {
    return null;
  }

  return { day, month, year };
}

export function formatNotificationCreatedAt(value: string, locale?: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleString(locale);
}

function formatReminderDate(metadata: NotificationMetadata, locale: string): { value: string; direction: 'rtl' | 'ltr' } {
  const isHebrew = isHebrewCalendarType((metadata.calendar_type ?? '').toLowerCase());
  if (isHebrew) {
    if (metadata.formatted_hebrew_date) {
      const parsedHebrew = parseNumericHebrewDate(metadata.formatted_hebrew_date);
      if (parsedHebrew) {
        return { value: formatHebrewDate(parsedHebrew), direction: 'rtl' };
      }

      return { value: metadata.formatted_hebrew_date, direction: 'rtl' };
    }

    if (metadata.date) {
      const parsedHebrew = parseNumericHebrewDate(metadata.date);
      if (parsedHebrew) {
        return { value: formatHebrewDate(parsedHebrew), direction: 'rtl' };
      }
    }
  }

  if (metadata.date) {
    const parsed = new Date(metadata.date);
    if (!Number.isNaN(parsed.getTime())) {
      return {
        value: parsed.toLocaleDateString(locale, { year: 'numeric', month: 'long', day: 'numeric' }),
        direction: 'ltr',
      };
    }
  }

  if (isHebrew && metadata.date) {
    const parsedHebrew = parseNumericHebrewDate(metadata.date);
    if (parsedHebrew) {
      return { value: formatHebrewDateNumeric(parsedHebrew), direction: 'rtl' };
    }
  }

  return { value: '', direction: 'ltr' };
}

export function getNotificationSummary(notification: NotificationResponse, t: TFunction, locale: string): NotificationSummary {
  const metadata = getNotificationMetadata(notification);

  if (notification.type === 'EVENT_REMINDER' || notification.type === 'event reminder') {
    const title = t('notifications.summary.reminder_title', { title: metadata.event_title ?? notification.message });
    const formattedDate = formatReminderDate(metadata, locale);
    if (formattedDate.value) {
      return {
        title,
        subtitle: t('notifications.summary.scheduled_for', { date: formattedDate.value }),
        direction: formattedDate.direction,
      };
    }

    return {
      title,
      subtitle: t('notifications.summary.event_reminder_fallback'),
      direction: 'ltr',
    };
  }

  if (notification.type === 'invite') {
    return {
      title: t('notifications.summary.invite_title'),
      subtitle: notification.message,
      direction: 'ltr',
    };
  }

  return {
    title: t('notifications.default_title'),
    subtitle: notification.message || t('notifications.default_subtitle'),
    direction: 'ltr',
  };
}
