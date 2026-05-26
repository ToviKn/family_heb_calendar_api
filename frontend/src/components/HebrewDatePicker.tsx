import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';

import { formatHebrewDate } from '../lib/dates/hebrewDateFormatter';

type HebrewDateValue = {
  day: number;
  month: number;
  year: number;
};

type HebrewDatePickerProps = {
  day: number | null;
  month: number | null;
  year: number | null;
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
  const rendered = formatHebrewDate({ day, month: 1, year: 5786 });
  return rendered.split(' ')[0] ?? String(day);
}

function getYearLabel(year: number): string {
  const rendered = formatHebrewDate({ day: 1, month: 1, year });
  const parts = rendered.split(' ');
  return parts[parts.length - 1] ?? String(year);
}

export function HebrewDatePicker({ day, month, year, onChange }: HebrewDatePickerProps) {
  const { t } = useTranslation();

  const preview = useMemo(() => {
    if (!day || !month || !year) return '';
    return formatHebrewDate({ day, month, year });
  }, [day, month, year]);

  function updatePartial(next: Partial<HebrewDateValue>) {
    const merged = {
      day: next.day ?? day ?? 1,
      month: next.month ?? month ?? 1,
      year: next.year ?? year ?? 5786,
    };
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
            <button className="rounded-md border border-slate-300 px-3 py-2" type="button" onClick={() => updatePartial({ year: Math.max(1, (year ?? 5786) - 1) })}>-</button>
            <div className="min-w-[110px] rounded-md border border-slate-300 px-3 py-2 text-center" dir="rtl">
              {year ? getYearLabel(year) : t('events.form.year')}
            </div>
            <button className="rounded-md border border-slate-300 px-3 py-2" type="button" onClick={() => updatePartial({ year: (year ?? 5786) + 1 })}>+</button>
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
