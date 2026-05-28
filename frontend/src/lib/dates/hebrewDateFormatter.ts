import { HDate } from '@hebcal/core';

import type { SimpleDate } from '../api';

const RTL_MARK = '\u200F';

export function normalizeHebrewYear(year: number): number {
  if (year < 1000) {
    return 5700 + year;
  }
  return year;
}

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

    return `${RTL_MARK}${gematria}${RTL_MARK}`;
  } catch {
    return formatHebrewDateNumeric(date);
  }
}
