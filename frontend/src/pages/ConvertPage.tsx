import { FormEvent, useState } from 'react';

import {
  convertGregorianToHebrew,
  convertHebrewToGregorian,
  getTodayConvertedDates,
  type DateConversionResponse,
} from '../lib/api';

interface HebrewFormState {
  year: string;
  month: string;
  day: string;
}

function getErrorMessage(error: unknown): string {
  if (typeof error === 'object' && error !== null && 'response' in error) {
    const response = (error as { response?: { data?: { message?: string } } }).response;
    const message = response?.data?.message;
    if (message) {
      return message;
    }
  }

  return 'Unable to convert date. Please verify your input and try again.';
}

export function ConvertPage() {
  const [gregorianDate, setGregorianDate] = useState('');
  const [hebrewForm, setHebrewForm] = useState<HebrewFormState>({ year: '', month: '', day: '' });

  const [result, setResult] = useState<DateConversionResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleGregorianToHebrew(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!gregorianDate) {
      setError('Please select a Gregorian date in YYYY-MM-DD format.');
      return;
    }

    const [year, month, day] = gregorianDate.split('-').map(Number);

    setIsLoading(true);
    setError(null);

    try {
      const data = await convertGregorianToHebrew({ year, month, day });
      setResult(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  }

  async function handleHebrewToGregorian(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setIsLoading(true);
    setError(null);

    try {
      const data = await convertHebrewToGregorian({
        year: Number(hebrewForm.year),
        month: Number(hebrewForm.month),
        day: Number(hebrewForm.day),
      });
      setResult(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  }

  async function handleGetToday() {
    setIsLoading(true);
    setError(null);

    try {
      const data = await getTodayConvertedDates();
      setResult(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <section className="space-y-6">
      <header className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h1 className="text-2xl font-semibold text-slate-900">Date Conversion</h1>
        <p className="mt-2 text-slate-600">Convert between Gregorian and Hebrew dates using the API.</p>
      </header>

      <div className="grid gap-6 lg:grid-cols-2">
        <article className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Gregorian → Hebrew</h2>

          <form className="mt-4 space-y-3" onSubmit={handleGregorianToHebrew}>
            <label className="block text-sm font-medium text-slate-700" htmlFor="gregorian-date">
              Gregorian date
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
              {isLoading ? 'Converting...' : 'Convert Gregorian → Hebrew'}
            </button>
          </form>
        </article>

        <article className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Hebrew → Gregorian</h2>

          <form className="mt-4 space-y-3" onSubmit={handleHebrewToGregorian}>
            <div className="grid grid-cols-3 gap-3">
              <input
                className="rounded-md border border-slate-300 px-3 py-2"
                type="number"
                min={1}
                placeholder="Year"
                value={hebrewForm.year}
                onChange={(event) => setHebrewForm((prev) => ({ ...prev, year: event.target.value }))}
                required
              />
              <input
                className="rounded-md border border-slate-300 px-3 py-2"
                type="number"
                min={1}
                max={13}
                placeholder="Month"
                value={hebrewForm.month}
                onChange={(event) => setHebrewForm((prev) => ({ ...prev, month: event.target.value }))}
                required
              />
              <input
                className="rounded-md border border-slate-300 px-3 py-2"
                type="number"
                min={1}
                max={31}
                placeholder="Day"
                value={hebrewForm.day}
                onChange={(event) => setHebrewForm((prev) => ({ ...prev, day: event.target.value }))}
                required
              />
            </div>

            <button
              className="rounded-md bg-indigo-600 px-4 py-2 text-white hover:bg-indigo-700 disabled:bg-indigo-300"
              type="submit"
              disabled={isLoading}
            >
              {isLoading ? 'Converting...' : 'Convert Hebrew → Gregorian'}
            </button>
          </form>
        </article>
      </div>

      <article className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-lg font-semibold text-slate-900">Today&apos;s date</h2>
          <button
            className="rounded-md bg-slate-800 px-4 py-2 text-white hover:bg-slate-900 disabled:bg-slate-400"
            type="button"
            onClick={() => void handleGetToday()}
            disabled={isLoading}
          >
            {isLoading ? 'Loading...' : "Get today's date (both formats)"}
          </button>
        </div>

        {error ? <p className="mt-4 text-sm text-red-600">{error}</p> : null}

        {result ? (
          <div className="mt-4 rounded-md border border-emerald-200 bg-emerald-50 p-4">
            <h3 className="font-semibold text-emerald-900">Converted result</h3>
            <div className="mt-2 grid gap-2 text-sm text-emerald-900 md:grid-cols-2">
              <p>
                <span className="font-medium">Gregorian:</span> {result.gregorian_date.year}-{String(result.gregorian_date.month).padStart(2, '0')}-
                {String(result.gregorian_date.day).padStart(2, '0')}
              </p>
              <p>
                <span className="font-medium">Hebrew:</span> {result.hebrew_date.year}-{String(result.hebrew_date.month).padStart(2, '0')}-
                {String(result.hebrew_date.day).padStart(2, '0')}
              </p>
            </div>
          </div>
        ) : null}
      </article>
    </section>
  );
}
