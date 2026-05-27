import { useEffect, useMemo } from 'react';
import { useTranslation } from 'react-i18next';

import { formatHebrewDate, getCurrentHebrewDate, normalizeHebrewYear } from '../lib/dates/hebrewDateFormatter';

type HebrewDateValue = {
  day: number;
  month: number;
  year: number;
};

type HebrewDatePickerProps = {
  value: HebrewDateValue | null;
  onChange: (value: HebrewDateValue) => void;
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
  try {
    const parts = formatHebrewDate({ day: 1, month: 1, year: normalizeHebrewYear(year) }).split(' ');
    return parts[parts.length - 1] ?? String(year);
  } catch {
    return String(year);
  }
}

export function HebrewDatePicker({ value, onChange }: HebrewDatePickerProps) {
  const { t } = useTranslation();
  const todayHebrew = useMemo(() => getCurrentHebrewDate(), []);
  const day = value?.day ?? todayHebrew.day;
  const month = value?.month ?? todayHebrew.month;
  const year = normalizeHebrewYear(value?.year ?? todayHebrew.year);

  useEffect(() => {
    console.log('HebrewDatePicker mounted/updated', { day, month, year });
  }, [day, month, year]);

  useEffect(() => {
    if (!value) {
      onChange(todayHebrew);
    }
  }, [onChange, todayHebrew, value]);

  const preview = useMemo(() => formatHebrewDate({ day, month, year }), [day, month, year]);

  function updatePartial(next: Partial<HebrewDateValue>) {
    const merged = {
      day: next.day ?? day ?? 1,
      month: next.month ?? month ?? 1,
      year: normalizeHebrewYear(next.year ?? year ?? 5786),
    };
    console.log('HebrewDatePicker onChange', merged);
    console.log('Hebrew year:', merged.year);
    onChange(merged);
  }

  return (
    <div className="space-y-2">
      <div className="grid grid-cols-3 gap-3">
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
            <div className="min-w-[110px] flex-shrink-0 whitespace-nowrap rounded-md border border-slate-300 px-3 py-2 text-center" dir="rtl">
              {getYearLabel(year)}
            </div>
            <button className="h-10 w-10 shrink-0 rounded-md border border-slate-300 text-center leading-none" type="button" onClick={() => updatePartial({ year: year + 1 })}>+</button>
          </div>
        </label>
      </div>

      <div className="rounded-md border border-blue-100 bg-blue-50 p-3">
        <p className="text-xs text-slate-600">{t('events.form.hebrew_preview_label')}</p>
        <div dir="rtl" className="text-lg font-medium text-slate-900">{preview || t('events.form.hebrew_preview_empty')}</div>
      </div>
    </div>
  );
}
