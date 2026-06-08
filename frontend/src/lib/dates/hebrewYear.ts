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
const HEBREW_YEAR_INPUT_PATTERN = /^[\s\u200e\u200fא-ת׳״'\"]+$/;
const HEBREW_THOUSANDS_SEPARATOR_PATTERN = /[׳']/;
const HEBREW_GERESH = '׳';
const HEBREW_GERSHAYIM = '״';

const HEBREW_ONES = ['', 'א', 'ב', 'ג', 'ד', 'ה', 'ו', 'ז', 'ח', 'ט'];
const HEBREW_TENS = ['', 'י', 'כ', 'ל', 'מ', 'נ', 'ס', 'ע', 'פ', 'צ'];
const HEBREW_HUNDREDS = ['', 'ק', 'ר', 'ש', 'ת'];

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

export function normalizeHebrewYear(year: number): number {
  return Math.floor(year);
}

export function parseHebrewYearInput(input: string, _referenceYear: number): number | null {
  const trimmed = input.trim();

  if (!trimmed) {
    return null;
  }

  if (/^\d+$/.test(trimmed)) {
    const numericYear = Number(trimmed);
    return numericYear >= 1 ? normalizeHebrewYear(numericYear) : null;
  }

  if (!HEBREW_LETTER_PATTERN.test(trimmed) || !HEBREW_YEAR_INPUT_PATTERN.test(trimmed)) {
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

  const year = sumHebrewNumeralLetters(trimmed);
  return year !== null && year >= 1 ? year : null;
}

function formatHebrewYearPart(value: number): string {
  if (value <= 0) {
    return '';
  }

  let remaining = value;
  const letters: string[] = [];

  while (remaining >= 400) {
    letters.push(HEBREW_HUNDREDS[4]);
    remaining -= 400;
  }

  const hundreds = Math.floor(remaining / 100);
  if (hundreds > 0) {
    letters.push(HEBREW_HUNDREDS[hundreds]);
    remaining %= 100;
  }

  if (remaining === 15) {
    letters.push('ט', 'ו');
    remaining = 0;
  } else if (remaining === 16) {
    letters.push('ט', 'ז');
    remaining = 0;
  }

  const tens = Math.floor(remaining / 10);
  if (tens > 0) {
    letters.push(HEBREW_TENS[tens]);
    remaining %= 10;
  }

  if (remaining > 0) {
    letters.push(HEBREW_ONES[remaining]);
  }

  if (letters.length === 0) {
    return '';
  }

  if (letters.length === 1) {
    return `${letters[0]}${HEBREW_GERESH}`;
  }

  return `${letters.slice(0, -1).join('')}${HEBREW_GERSHAYIM}${letters[letters.length - 1]}`;
}

export function formatHebrewYear(year: number): string {
  if (!Number.isFinite(year) || year < 1) {
    return String(year);
  }

  const normalizedYear = normalizeHebrewYear(year);
  const yearRemainder = normalizedYear % 1000;

  if (yearRemainder > 0) {
    return formatHebrewYearPart(yearRemainder);
  }

  return formatHebrewYearPart(Math.floor(normalizedYear / 1000));
}

export function formatHebrewYearInput(year: number): string {
  if (!Number.isFinite(year) || year < 1) {
    return String(year);
  }

  const normalizedYear = normalizeHebrewYear(year);

  if (normalizedYear < 1000) {
    const yearPart = formatHebrewYearPart(normalizedYear);
    return yearPart.endsWith(HEBREW_GERESH) ? yearPart.slice(0, -1) : yearPart;
  }

  const thousands = Math.floor(normalizedYear / 1000);
  const yearRemainder = normalizedYear % 1000;
  const thousandsLabel = formatHebrewYearPart(thousands);

  if (yearRemainder === 0) {
    return thousandsLabel;
  }

  return `${thousandsLabel}${formatHebrewYearPart(yearRemainder)}`;
}
