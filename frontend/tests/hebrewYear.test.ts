import { describe, it } from 'node:test';
import assert from 'node:assert/strict';

import { formatHebrewYear, formatHebrewYearInput, parseHebrewYearInput } from '../src/lib/dates/hebrewYear.ts';

describe('formatHebrewYear', () => {
  const cases: Array<[number, string]> = [
    [1, 'א׳'],
    [2, 'ב׳'],
    [10, 'י׳'],
    [100, 'ק׳'],
    [999, 'תתקצ״ט'],
    [1000, 'א׳'],
    [5000, 'ה׳'],
    [5786, 'תשפ״ו'],
  ];

  for (const [year, expected] of cases) {
    it(`formats Hebrew year ${year} as ${expected}`, () => {
      assert.equal(formatHebrewYear(year), expected);
    });
  }
});

describe('formatHebrewYearInput', () => {
  it('omits punctuation for single-letter ancient years while including thousands for modern years', () => {
    assert.equal(formatHebrewYearInput(1), 'א');
    assert.equal(formatHebrewYearInput(100), 'ק');
    assert.equal(formatHebrewYearInput(5786), 'ה׳תשפ״ו');
  });
});

describe('parseHebrewYearInput', () => {
  const cases: Array<[string, number]> = [
    ['א', 1],
    ['ב', 2],
    ['ק', 100],
    ['א׳', 1],
    ['תש"ח', 708],
    ['תשפ"ו', 786],
    ['ה\'תש"ח', 5708],
    ['ה\'תשפ"ו', 5786],
    ['ה׳תש״ח', 5708],
    ['ה׳תשפ״ו', 5786],
  ];

  for (const [input, expected] of cases) {
    it(`parses ${input} as ${expected}`, () => {
      assert.equal(parseHebrewYearInput(input, 5786), expected);
    });
  }

  it('rejects invalid Hebrew year strings', () => {
    assert.equal(parseHebrewYearInput('abcא', 5786), null);
  });
});
