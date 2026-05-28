import type { EventResponse, SimpleDate } from '../api';

import { formatHebrewDate } from './hebrewDateFormatter';

export interface DisplayDateOptions {
  fallbackYear?: number;
}

export function formatGregorianDateNumeric(date: SimpleDate): string {
  const year = String(date.year).padStart(4, '0');
  const month = String(date.month).padStart(2, '0');
  const day = String(date.day).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export function formatEventDisplayDate(event: Pick<EventResponse, 'calendar_type' | 'year' | 'month' | 'day'>, options?: DisplayDateOptions): string {
  if (event.calendar_type === 'hebrew') {
    return formatHebrewDate({
      year: event.year ?? options?.fallbackYear ?? new Date().getFullYear(),
      month: event.month,
      day: event.day,
    });
  }

  if (event.year) {
    return formatGregorianDateNumeric({ year: event.year, month: event.month, day: event.day });
  }

  return `${String(event.month).padStart(2, '0')}/${String(event.day).padStart(2, '0')}`;
}

export function isHebrewCalendarType(calendarType?: string | null): boolean {
  return calendarType?.toLowerCase() === 'hebrew';
}
