import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { formatHebrewDate, formatHebrewYearInput, getCurrentHebrewDate, normalizeHebrewYear, parseHebrewYearInput } from '../lib/dates/hebrewDateFormatter';

type HebrewDateValue = {
  day: number;
  month: number;
  year: number;
};

type HebrewDatePickerProps = {
  value: HebrewDateValue | null;
  onChange: (value: HebrewDateValue) => void;
  onValidityChange?: (isValid: boolean) => void;
};

const HEBREW_MONTHS = [
  { value: 1, key: 'events.hebrew_months.1' },
  { value: 2, key: 'events.hebrew_months.2' },
  { value: 3, key: 'events.hebrew_months.3' },
  { value: 4, key: 'events.hebrew_months.4' },
  { value: 5, key: 'events.hebrew_months.5' },
  { value: 6, key: 'events.hebrew_months.6' },
  { value: 7, key: 'events.hebrew_months.7' },
  { value: 8, key: 'events.hebrew_months.8' },
  { value: 9, key: 'events.hebrew_months.9' },
  { value: 10, key: 'events.hebrew_months.10' },
  { value: 11, key: 'events.hebrew_months.11' },
  { value: 12, key: 'events.hebrew_months.12' },
  { value: 13, key: 'events.hebrew_months.13' },
];

function getDayLabel(day: number): string {
  try {
    return formatHebrewDate({ day, month: 1, year: 5786 }).split(' ')[0] ?? String(day);
  } catch {
    return String(day);
  }
}

function getYearLabel(year: number): string {
  return formatHebrewYearInput(normalizeHebrewYear(year));
}

export function HebrewDatePicker({ value, onChange, onValidityChange }: HebrewDatePickerProps) {
  const { t } = useTranslation();
  const todayHebrew = useMemo(() => getCurrentHebrewDate(), []);
  const day = value?.day ?? todayHebrew.day;
  const month = value?.month ?? todayHebrew.month;
  const year = normalizeHebrewYear(value?.year ?? todayHebrew.year);
  const yearLabel = getYearLabel(year);
  const [yearInput, setYearInput] = useState(yearLabel);
  const [isEditingYear, setIsEditingYear] = useState(false);
  const [yearError, setYearError] = useState<string | null>(null);

  useEffect(() => {
    if (!value) {
      onChange(todayHebrew);
    }
  }, [onChange, todayHebrew, value]);

  useEffect(() => {
    if (!isEditingYear) {
      setYearInput(yearLabel);
    }
  }, [isEditingYear, yearLabel]);

  const preview = useMemo(() => formatHebrewDate({ day, month, year }), [day, month, year]);

  function updatePartial(next: Partial<HebrewDateValue>) {
    const merged = {
      day: next.day ?? day ?? 1,
      month: next.month ?? month ?? 1,
      year: normalizeHebrewYear(next.year ?? year ?? 5786),
    };
    if (next.year !== undefined) {
      setYearError(null);
      onValidityChange?.(true);
    }

    onChange(merged);
  }

  function updateYearFromInput(input: string): boolean {
    const parsedYear = parseHebrewYearInput(input, year);

    if (!parsedYear || parsedYear < 1) {
      setYearError(t('events.form.invalid_hebrew_year'));
      onValidityChange?.(false);
      return false;
    }

    setYearError(null);
    onValidityChange?.(true);
    updatePartial({ year: parsedYear });
    return true;
  }

  function handleYearInputChange(input: string) {
    setYearInput(input);

    if (!input.trim()) {
      setYearError(t('events.form.invalid_hebrew_year'));
      onValidityChange?.(false);
      return;
    }

    updateYearFromInput(input);
  }

  function handleYearInputBlur() {
    setIsEditingYear(false);

    if (yearInput === yearLabel) {
      setYearError(null);
      onValidityChange?.(true);
      return;
    }

    if (updateYearFromInput(yearInput)) {
      const parsedYear = parseHebrewYearInput(yearInput, year);
      setYearInput(getYearLabel(parsedYear ?? year));
      return;
    }

    setYearError(null);
    onValidityChange?.(true);
    setYearInput(yearLabel);
  }

  return (
    <div className="space-y-2">
      <div className="grid grid-cols-[0.8fr_0.8fr_1.4fr] gap-3">
        <label className="text-sm text-slate-700">
          {t('events.form.day')}
          <select className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={day ?? ''} onChange={(e) => updatePartial({ day: Number(e.target.value) })}>
            <option value="">{t('events.form.day')}</option>
            {Array.from({ length: 30 }, (_, i) => i + 1).map((d) => (
              <option key={d} value={d}>{getDayLabel(d)}</option>
            ))}
          </select>
        </label>

        <label className="text-sm text-slate-700">
          {t('events.form.hebrew_month')}
          <select className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" value={month ?? ''} onChange={(e) => updatePartial({ month: Number(e.target.value) })}>
            <option value="">{t('events.form.hebrew_month')}</option>
            {HEBREW_MONTHS.map((m) => (
              <option key={m.value} value={m.value}>{t(m.key)}</option>
            ))}
          </select>
        </label>

        <label className="text-sm text-slate-700">
          {t('events.form.year')}
          <div className="mt-1 flex items-center gap-2">
            <button className="h-10 w-10 shrink-0 rounded-md border border-slate-300 text-center leading-none" type="button" onClick={() => updatePartial({ year: Math.max(1, year - 1) })}>-</button>
            <input
              aria-invalid={yearError ? 'true' : 'false'}
              className="h-10 min-w-[110px] flex-shrink-0 rounded-md border border-slate-300 px-3 py-2 text-center"
              dir="rtl"
              inputMode="text"
              value={yearInput}
              onBlur={handleYearInputBlur}
              onChange={(event) => handleYearInputChange(event.target.value)}
              onFocus={(event) => {
                setIsEditingYear(true);
                event.target.select();
              }}
            />
            <button className="h-10 w-10 shrink-0 rounded-md border border-slate-300 text-center leading-none" type="button" onClick={() => updatePartial({ year: year + 1 })}>+</button>
          </div>
          {yearError ? <p className="mt-1 text-xs text-red-600">{yearError}</p> : null}
        </label>
      </div>

      <div className="rounded-md border border-blue-100 bg-blue-50 p-3">
        <p className="text-xs text-slate-600">{t('events.form.hebrew_preview_label')}</p>
        <div dir="rtl" className="text-lg font-medium text-slate-900">{preview || t('events.form.hebrew_preview_empty')}</div>
      </div>
    </div>
  );
}
