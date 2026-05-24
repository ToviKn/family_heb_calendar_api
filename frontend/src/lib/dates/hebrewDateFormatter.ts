import { HDate } from '@hebcal/core';

import type { SimpleDate } from '../api';

const RTL_MARK = '\u200F';

export function formatHebrewDateNumeric(date: SimpleDate): string {
  const month = String(date.month).padStart(2, '0');
  const day = String(date.day).padStart(2, '0');
  return `${day}/${month}/${date.year}`;
}

export function formatHebrewDate(date: SimpleDate): string {
  try {
    const hd = new HDate(date.day, date.month, date.year);
    const gematria = hd.renderGematriya();

    if (!gematria || !gematria.trim()) {
      return formatHebrewDateNumeric(date);
    }

    return `${RTL_MARK}${gematria}${RTL_MARK}`;
  } catch {
    return formatHebrewDateNumeric(date);
  }
}
