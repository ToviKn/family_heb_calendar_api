import { HDate } from '@hebcal/core';

import type { SimpleDate } from '../api';

const RTL_MARK = '\u200F';

const HEBREW_NUMERAL_VALUES: Record<string, number> = {
  א: 1,
  ב: 2,
  ג: 3,
  ד: 4,
  ה: 5,
  ו: 6,
  ז: 7,
  ח: 8,
  ט: 9,
  י: 10,
  כ: 20,
  ך: 20,
  ל: 30,
  מ: 40,
  ם: 40,
  נ: 50,
  ן: 50,
  ס: 60,
  ע: 70,
  פ: 80,
  ף: 80,
  צ: 90,
  ץ: 90,
  ק: 100,
  ר: 200,
  ש: 300,
  ת: 400,
};

const HEBREW_LETTER_PATTERN = /[א-ת]/;
const HEBREW_THOUSANDS_SEPARATOR_PATTERN = /[׳']/;

function sumHebrewNumeralLetters(value: string): number | null {
  let total = 0;
  let hasHebrewLetter = false;

  for (const character of value) {
    const characterValue = HEBREW_NUMERAL_VALUES[character];

    if (characterValue !== undefined) {
      total += characterValue;
      hasHebrewLetter = true;
    }
  }

  return hasHebrewLetter ? total : null;
}

export function parseHebrewYearInput(input: string, referenceYear: number): number | null {
  const trimmed = input.trim();

  if (!trimmed) {
    return null;
  }

  if (/^\d+$/.test(trimmed)) {
    const numericYear = Number(trimmed);
    return numericYear >= 1 ? normalizeHebrewYear(numericYear) : null;
  }

  if (!HEBREW_LETTER_PATTERN.test(trimmed)) {
    return null;
  }

  const thousandsMatch = trimmed.match(HEBREW_THOUSANDS_SEPARATOR_PATTERN);

  if (thousandsMatch?.index && thousandsMatch.index > 0) {
    const thousandsText = trimmed.slice(0, thousandsMatch.index);
    const yearText = trimmed.slice(thousandsMatch.index + 1);
    const thousands = sumHebrewNumeralLetters(thousandsText);
    const yearRemainder = sumHebrewNumeralLetters(yearText);

    if (thousands !== null && yearRemainder !== null) {
      const year = thousands * 1000 + yearRemainder;
      return year >= 1 ? year : null;
    }
  }

  const yearRemainder = sumHebrewNumeralLetters(trimmed);

  if (yearRemainder === null || yearRemainder < 1) {
    return null;
  }

  const normalizedReferenceYear = normalizeHebrewYear(referenceYear);

  if (yearRemainder < 100) {
    const referenceCentury = Math.floor(normalizedReferenceYear / 100) * 100;
    return referenceCentury + yearRemainder;
  }

  const referenceMillennium = Math.floor(normalizedReferenceYear / 1000) * 1000;
  return referenceMillennium + yearRemainder;
}

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
