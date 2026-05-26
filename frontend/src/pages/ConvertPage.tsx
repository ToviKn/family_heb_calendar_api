import { ErrorMessage } from '../components/Feedback';
import { useState } from 'react';
import type { FormEvent } from 'react';
import { useTranslation } from 'react-i18next';

import { formatHebrewDate, formatHebrewDateNumeric } from '../lib/dates/hebrewDateFormatter';
import { formatGregorianDateNumeric } from '../lib/dates/eventDateFormatter';

import {
  convertGregorianToHebrew,
  convertHebrewToGregorian,
  getTodayConvertedDates,
  getApiErrorMessage,
  type DateConversionResponse,
} from '../lib/api';

interface HebrewFormState {
  year: string;
  month: string;
  day: string;
}

type ActiveAction = 'gregorian_to_hebrew' | 'hebrew_to_gregorian' | 'today' | null;

function parseGregorianDate(value: string): { year: number; month: number; day: number } | null {
  const [year, month, day] = value.split('-').map(Number);

  if ([year, month, day].some((part) => Number.isNaN(part))) {
    return null;
  }

  return { year, month, day };
}


function validateHebrewInput(form: HebrewFormState): { year: number; month: number; day: number } | null {
  const year = Number(form.year);
  const month = Number(form.month);
  const day = Number(form.day);

  if ([year, month, day].some((part) => Number.isNaN(part))) {
    return null;
  }

  if (month < 1 || month > 13) {
    return null;
  }

  if (day < 1 || day > 30) {
    return null;
  }

  return { year, month, day };
}

export function ConvertPage() {
  const { t } = useTranslation();

  const [gregorianDate, setGregorianDate] = useState('');
  const [hebrewForm, setHebrewForm] = useState<HebrewFormState>({ year: '', month: '', day: '' });

  const [result, setResult] = useState<DateConversionResponse | null>(null);
  const [activeAction, setActiveAction] = useState<ActiveAction>(null);
  const [error, setError] = useState<string | null>(null);

  const isLoading = activeAction !== null;

  function getConvertError(err: unknown): string {
      return getApiErrorMessage(err, t('convert.errors.convert_failed'));
    }
  async function handleGregorianToHebrew(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const parsedDate = parseGregorianDate(gregorianDate);
    if (!parsedDate) {
      setResult(null);
      setError(t('convert.errors.invalid_gregorian'));
      return;
    }

    setActiveAction('gregorian_to_hebrew');
    setError(null);

    try {
      const data = await convertGregorianToHebrew(parsedDate);
      setResult(data);
    } catch (err) {
      setResult(null);
      setError(getConvertError(err));
    } finally {
      setActiveAction(null);
    }
  }

  async function handleHebrewToGregorian(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const parsed = validateHebrewInput(hebrewForm);
    if (!parsed) {
      setResult(null);
      setError(t('convert.errors.invalid_hebrew'));
      return;
    }

    setActiveAction('hebrew_to_gregorian');
    setError(null);

    try {
      const data = await convertHebrewToGregorian(parsed);
      setResult(data);
    } catch (err) {
      setResult(null);
      setError(getConvertError(err));
    } finally {
      setActiveAction(null);
    }
  }

  async function handleGetToday() {
    setActiveAction('today');
    setError(null);

    try {
      const data = await getTodayConvertedDates();
      setResult(data);
    } catch (err) {
      setResult(null);
      setError(getConvertError(err));
    } finally {
      setActiveAction(null);
    }
  }

  return (
    <section className="space-y-6">
      <header className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h1 className="text-2xl font-semibold text-slate-900">{t('convert.title')}</h1>
        <p className="mt-2 text-slate-600">{t('convert.description')}</p>
      </header>

      <div className="grid gap-6 lg:grid-cols-2">
        <article className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">{t('convert.gregorian_to_hebrew.title')}</h2>

          <form className="mt-4 space-y-3" onSubmit={handleGregorianToHebrew}>
            <label className="block text-sm font-medium text-slate-700" htmlFor="gregorian-date">
              {t('convert.gregorian_to_hebrew.label')}
            </label>
            <input
              id="gregorian-date"
              className="w-full rounded-md border border-slate-300 px-3 py-2"
              type="date"
              value={gregorianDate}
              onChange={(event) => setGregorianDate(event.target.value)}
              required
            />

            <button
              className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:bg-blue-300"
              type="submit"
              disabled={isLoading}
            >
              {activeAction === 'gregorian_to_hebrew' ? t('convert.actions.converting') : t('convert.actions.convert_gregorian')}
            </button>
          </form>
        </article>

        <article className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">{t('convert.hebrew_to_gregorian.title')}</h2>

          <form className="mt-4 space-y-3" onSubmit={handleHebrewToGregorian}>
            <div className="grid grid-cols-3 gap-3">
              <input
                className="rounded-md border border-slate-300 px-3 py-2"
                type="number"
                min={1}
                placeholder={t('convert.form.year')}
                value={hebrewForm.year}
                onChange={(event) => setHebrewForm((prev) => ({ ...prev, year: event.target.value }))}
                required
              />
              <input
                className="rounded-md border border-slate-300 px-3 py-2"
                type="number"
                min={1}
                max={13}
                placeholder={t('convert.form.month')}
                value={hebrewForm.month}
                onChange={(event) => setHebrewForm((prev) => ({ ...prev, month: event.target.value }))}
                required
              />
              <input
                className="rounded-md border border-slate-300 px-3 py-2"
                type="number"
                min={1}
                max={30}
                placeholder={t('convert.form.day')}
                value={hebrewForm.day}
                onChange={(event) => setHebrewForm((prev) => ({ ...prev, day: event.target.value }))}
                required
              />
            </div>
            <p className="text-xs text-slate-500">{t('convert.hebrew_to_gregorian.day_range')}</p>

            <button
              className="rounded-md bg-indigo-600 px-4 py-2 text-white hover:bg-indigo-700 disabled:bg-indigo-300"
              type="submit"
              disabled={isLoading}
            >
              {activeAction === 'hebrew_to_gregorian' ? t('convert.actions.converting') : t('convert.actions.convert_hebrew')}
            </button>
          </form>
        </article>
      </div>

      <article className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-lg font-semibold text-slate-900">{t('convert.today.title')}</h2>
          <button
            className="rounded-md bg-slate-800 px-4 py-2 text-white hover:bg-slate-900 disabled:bg-slate-400"
            type="button"
            onClick={() => void handleGetToday()}
            disabled={isLoading}
          >
            {activeAction === 'today' ? t('convert.actions.loading') : t('convert.actions.get_today')}
          </button>
        </div>

        {error ? <ErrorMessage message={error} /> : null}

        {!result && !error && !isLoading ? (
            <p className="mt-4 text-sm text-slate-500">
            {t('convert.messages.no_result')}
            </p>
        ) : null}

        {result ? (
          <div className="mt-4 rounded-md border border-emerald-200 bg-emerald-50 p-4">
            <h3 className="font-semibold text-emerald-900">{t('convert.result.title')}</h3>
            <div className="mt-2 grid gap-2 text-sm text-emerald-900 md:grid-cols-2">
              <p>
                <span className="font-medium">{t('convert.result.gregorian')}:</span> {formatGregorianDateNumeric(result.gregorian_date)}
              </p>
              <p dir="rtl">
                <span className="font-medium">{t('convert.result.hebrew')}:</span> {formatHebrewDate(result.hebrew_date)}
                <span className="sr-only"> ({formatHebrewDateNumeric(result.hebrew_date)})</span>
              </p>
            </div>
          </div>
        ) : null}
      </article>
    </section>
  );
}
