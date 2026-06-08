import { HDate } from '@hebcal/core';

import type { SimpleDate } from '../api';
import { formatHebrewYear, normalizeHebrewYear } from './hebrewYear';

export { formatHebrewYear, formatHebrewYearInput, normalizeHebrewYear, parseHebrewYearInput } from './hebrewYear';

const RTL_MARK = '\u200F';

export function getCurrentHebrewDate(): SimpleDate {
  const today = new HDate(new Date());
  const currentHebrewDate = {
    day: today.getDate(),
    month: today.getMonth(),
    year: normalizeHebrewYear(today.getFullYear()),
  };
  return currentHebrewDate;
}

export function formatHebrewDateNumeric(date: SimpleDate): string {
  const month = String(date.month).padStart(2, '0');
  const day = String(date.day).padStart(2, '0');
  return `${day}/${month}/${normalizeHebrewYear(date.year)}`;
}

export function formatHebrewDate(date: SimpleDate): string {
  try {
    const hd = new HDate(date.day, date.month, normalizeHebrewYear(date.year));
    const gematria = hd.renderGematriya();

    if (!gematria || !gematria.trim()) {
      return formatHebrewDateNumeric(date);
    }

    const parts = gematria.trim().split(/\s+/);
    parts[parts.length - 1] = formatHebrewYear(date.year);

    return `${RTL_MARK}${parts.join(' ')}${RTL_MARK}`;
  } catch {
    return formatHebrewDateNumeric(date);
  }
}
