import type { TFunction } from 'i18next';

import type { NotificationResponse, NotificationUserSummary } from '../api';
import { isHebrewCalendarType } from '../dates/eventDateFormatter';
import { formatHebrewDate } from '../dates/hebrewDateFormatter';
import { formatFamilyNameWithId } from '../../utils/familyDisplay';
export interface NotificationSummary {
  title: string;
  subtitle: string;
  direction: 'rtl' | 'ltr';
}

interface NotificationActorMetadata {
  id?: number;
  name?: string;
}

interface NotificationMetadata {
  actor?: NotificationActorMetadata;
  calendar_type?: string;
  date?: string;
  event_title?: string;
  family_id?: number;
  family_name?: string;
  formatted_hebrew_date?: string;
  hebrew_date?: { day?: number; month?: number; year?: number };
  requesting_user_id?: number;
  requesting_user_name?: string;
  status?: string;
  target?: NotificationActorMetadata;
}

export function getNotificationMetadata(notification: NotificationResponse): NotificationMetadata {
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
  const isHebrew = isHebrewCalendarType(metadata.calendar_type);
  if (isHebrew) {
    if (metadata.formatted_hebrew_date) {
      const parsedHebrew = parseNumericHebrewDate(metadata.formatted_hebrew_date);
      return {
        value: parsedHebrew ? formatHebrewDate(parsedHebrew) : metadata.formatted_hebrew_date,
        direction: 'rtl',
      };
    }

    const hebrewDate = metadata.hebrew_date;
    if (hebrewDate?.day && hebrewDate.month && hebrewDate.year) {
      return {
        value: formatHebrewDate({ day: hebrewDate.day, month: hebrewDate.month, year: hebrewDate.year }),
        direction: 'rtl',
      };
    }

    if (metadata.date) {
      const parsedHebrew = parseNumericHebrewDate(metadata.date);
      if (parsedHebrew) {
        return { value: formatHebrewDate(parsedHebrew), direction: 'rtl' };
      }
    }

    return { value: '', direction: 'rtl' };
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

  return { value: '', direction: 'ltr' };
}

function getMetadataUser(metadataUser: NotificationActorMetadata | undefined, responseUser: NotificationUserSummary | null | undefined): NotificationActorMetadata | undefined {
  return metadataUser ?? responseUser ?? undefined;
}

function getLegacyJoinRequestDetails(message: string): { requestingUserName?: string; family_id?: number } {
  const match = message.match(/^(.+?) requested to join family (.+)$/);
  if (!match) {
    return {};
  }

  const familyId = Number(match[2]);
  return {
    requestingUserName: match[1],
    family_id: Number.isInteger(familyId) && familyId > 0 ? familyId : undefined,
  };
}

function summarizeFamilyNotification(notification: NotificationResponse, metadata: NotificationMetadata, t: TFunction, direction: 'rtl' | 'ltr'): NotificationSummary | null {
  const actor = getMetadataUser(metadata.actor, notification.actor);
  const target = getMetadataUser(metadata.target, notification.target);
  const legacyJoinRequest = notification.type === 'join_request' ? getLegacyJoinRequestDetails(notification.message) : {};
  const requestingUserName = metadata.requesting_user_name ?? actor?.name ?? legacyJoinRequest.requestingUserName;
  const actorName = actor?.name ?? requestingUserName;
  const targetName = target?.name;
  const family = {
    family_id: metadata.family_id ?? notification.family_id ?? legacyJoinRequest.family_id,
    family_name: metadata.family_name ?? notification.family_name,
  };
  const familyDisplay = formatFamilyNameWithId(family, t);

  if (metadata.status === 'approved' && actorName) {
    return {
      title: t('notifications.summary.join_request_approved_title'),
      subtitle: t('notifications.summary.join_request_approved', { actorName, family: familyDisplay }),
      direction,
    };
  }

  if (metadata.status === 'rejected' && actorName) {
    return {
      title: t('notifications.summary.join_request_rejected_title'),
      subtitle: t('notifications.summary.join_request_rejected', { actorName, family: familyDisplay }),
      direction,
    };
  }

  if (notification.type === 'invite' && actorName && targetName) {
    return {
      title: t('notifications.summary.invite_title'),
      subtitle: t('notifications.summary.invited_to_family', { actorName, targetName, family: familyDisplay }),
      direction,
    };
  }

  if (notification.type === 'join_request' && requestingUserName) {
    return {
      title: t('notifications.summary.join_request_title'),
      subtitle: t('notifications.summary.requested_to_join', { userName: requestingUserName, family: familyDisplay }),
      direction,
    };
  }

  return null;
}

function summarizeSystemNotification(message: string, t: TFunction, direction: 'rtl' | 'ltr'): NotificationSummary | null {
  const createdMatch = message.match(/^New event created: (.+)$/);
  if (createdMatch) {
    return {
      title: t('notifications.summary.event_created_title'),
      subtitle: t('notifications.summary.event_created', { title: createdMatch[1] }),
      direction,
    };
  }

  const updatedMatch = message.match(/^Event updated: (.+)$/);
  if (updatedMatch) {
    return {
      title: t('notifications.summary.event_updated_title'),
      subtitle: t('notifications.summary.event_updated', { title: updatedMatch[1] }),
      direction,
    };
  }

  return null;
}

export function getNotificationSummary(notification: NotificationResponse, t: TFunction, locale: string): NotificationSummary {
  const metadata = getNotificationMetadata(notification);
  const direction = locale.startsWith('he') ? 'rtl' : 'ltr';

  if (notification.type === 'EVENT_REMINDER' || notification.type === 'event reminder') {
    const legacyTitleMatch = notification.message.match(/^Reminder: (.+?) on .+$/);
    const title = t('notifications.summary.reminder_title', {
      title: metadata.event_title ?? legacyTitleMatch?.[1] ?? t('notifications.summary.untitled_event'),
    });
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
      direction,
    };
  }

  if (notification.type === 'invite' || notification.type === 'join_request') {
    const familySummary = summarizeFamilyNotification(notification, metadata, t, direction);
    if (familySummary) {
      return familySummary;
    }
  }

  if (notification.type === 'system') {
    const systemSummary = summarizeSystemNotification(notification.message, t, direction);
    if (systemSummary) {
      return systemSummary;
    }
  }

  return {
    title: t('notifications.default_title'),
    subtitle: t('notifications.default_subtitle'),
    direction,
  };
}
