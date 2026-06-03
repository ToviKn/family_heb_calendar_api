import { describe, it } from 'node:test';
import assert from 'node:assert/strict';

import { formatHebrewYear } from '../src/lib/dates/hebrewYear.ts';

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
