import { EmptyMessage, ErrorMessage, LoadingMessage } from '../components/Feedback';
import { FormEvent, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';

import {
  createEvent,
  deleteEvent,
  getEventsByDate,
  getTodayEvents,
  getUpcomingEvents,
  updateEvent,
  type CalendarType,
  type EventCreate,
  type EventResponse,
  type RepeatType,
} from '../lib/api';

type EventsViewMode = 'date' | 'today' | 'upcoming';

interface EventFormState {
  title: string;
  description: string;
  familyId: string;
  month: string;
  day: string;
  year: string;
  startTime: string;
  endTime: string;
  calendarType: CalendarType;
  repeatType: RepeatType;
}

function toDateInputValue(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function parseDateInput(value: string): { year: number; month: number; day: number } {
  const [year, month, day] = value.split('-').map(Number);
  return { year, month, day };
}

function buildCreatePayload(form: EventFormState): EventCreate {
  return {
    title: form.title,
    description: form.description || null,
    family_id: Number(form.familyId),
    month: Number(form.month),
    day: Number(form.day),
    year: form.year ? Number(form.year) : null,
    calendar_type: form.calendarType,
    repeat_type: form.repeatType,
    start_time: form.startTime || null,
    end_time: form.endTime || null,
  };
}

function getDefaultFormState(date: string): EventFormState {
  const { year, month, day } = parseDateInput(date);

  return {
    title: '',
    description: '',
    familyId: '',
    month: String(month),
    day: String(day),
    year: String(year),
    startTime: '',
    endTime: '',
    calendarType: 'gregorian',
    repeatType: 'none',
  };
}

function hasInvalidTimeRange(startTime: string, endTime: string): boolean {
  if (!startTime || !endTime) {
    return false;
  }

  return endTime <= startTime;
}

export function EventsPage() {
  const { t } = useTranslation();

  const [selectedDate, setSelectedDate] = useState<string>(() => toDateInputValue(new Date()));
  const [events, setEvents] = useState<EventResponse[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [editingEventId, setEditingEventId] = useState<number | null>(null);
  const [viewMode, setViewMode] = useState<EventsViewMode>('date');

  const [form, setForm] = useState<EventFormState>(() => getDefaultFormState(toDateInputValue(new Date())));
  const monthMax = form.calendarType === 'hebrew' ? 13 : 12;

  function getEmptyMessage(mode: EventsViewMode): string {
  if (mode === 'today') {
    return t('events.empty.today');
  }

  if (mode === 'upcoming') {
    return t('events.empty.upcoming');
  }

  return t('events.empty.date');
  }

  async function loadEvents(mode: EventsViewMode, dateValue: string) {
    if (mode === 'date' && !dateValue) {
      setEvents([]);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      if (mode === 'today') {
        const result = await getTodayEvents();
        setEvents(result.events);
        return;
      }

      if (mode === 'upcoming') {
        const result = await getUpcomingEvents();
        setEvents(result.events);
        return;
      }

      const parsed = parseDateInput(dateValue);
      const result = await getEventsByDate(parsed);
      setEvents(result.events);
    } catch {
      if (mode === 'today') {
        setError(t('events.errors.load_today'));
      } else if (mode === 'upcoming') {
        setError(t('events.errors.load_upcoming'));
      } else {
        setError(t('events.errors.load_date'));
      }
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadEvents(viewMode, selectedDate);
  }, [selectedDate, viewMode]);

  function resetForm() {
    setForm(getDefaultFormState(selectedDate));
    setEditingEventId(null);
  }

  async function handleCreateOrUpdate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (hasInvalidTimeRange(form.startTime, form.endTime)) {
      setError(t('events.errors.invalid_time'));
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      if (editingEventId) {
        await updateEvent(editingEventId, {
          title: form.title,
          description: form.description || null,
          month: Number(form.month),
          day: Number(form.day),
          year: form.year ? Number(form.year) : null,
          repeat_type: form.repeatType,
          start_time: form.startTime || null,
          end_time: form.endTime || null,
        });
      } else {
        await createEvent(buildCreatePayload(form));
      }

      await loadEvents(viewMode, selectedDate);
      resetForm();
    } catch {
      setError(t('events.errors.save'));
    } finally {
      setIsSubmitting(false);
    }
  }

  function startEdit(eventItem: EventResponse) {
    setEditingEventId(eventItem.id);
    setForm({
      title: eventItem.title,
      description: eventItem.description ?? '',
      familyId: String(eventItem.family_id),
      month: String(eventItem.month),
      day: String(eventItem.day),
      year: eventItem.year ? String(eventItem.year) : '',
      startTime: eventItem.start_time ?? '',
      endTime: eventItem.end_time ?? '',
      calendarType: eventItem.calendar_type ?? 'gregorian',
      repeatType: eventItem.repeat_type ?? 'none',
    });
  }

  async function handleDelete(eventId: number) {
    setError(null);

    try {
      await deleteEvent(eventId);
      await loadEvents(viewMode, selectedDate);
      if (editingEventId === eventId) {
        resetForm();
      }
    } catch {
      setError(t('events.errors.delete'));
    }
  }

  return (
    <section className="space-y-6">
      <header className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h1 className="text-2xl font-semibold text-slate-900">{t('events.title')}</h1>
        <p className="mt-2 text-slate-600">{t('events.description')}</p>
      </header>

      <div className="grid gap-6 lg:grid-cols-2">
        <article className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">{editingEventId ? t('events.actions.edit') : t('events.actions.create')}</h2>

          <form className="mt-4 space-y-3" onSubmit={handleCreateOrUpdate}>
            <input
              className="w-full rounded-md border border-slate-300 px-3 py-2"
              placeholder={t('events.form.title')}
              value={form.title}
              onChange={(e) => setForm((prev) => ({ ...prev, title: e.target.value }))}
              required
            />

            <textarea
              className="w-full rounded-md border border-slate-300 px-3 py-2"
              placeholder={t('events.form.description')}
              value={form.description}
              onChange={(e) => setForm((prev) => ({ ...prev, description: e.target.value }))}
              rows={3}
            />

            <input
              className="w-full rounded-md border border-slate-300 px-3 py-2"
              placeholder={t('events.form.family_id')}
              type="number"
              min={1}
              value={form.familyId}
              onChange={(e) => setForm((prev) => ({ ...prev, familyId: e.target.value }))}
              required
              disabled={editingEventId !== null}
            />

            <div className="grid grid-cols-3 gap-3">
              <input
                className="rounded-md border border-slate-300 px-3 py-2"
                type="number"
                min={1}
                max={31}
                placeholder={t('events.form.day')}
                value={form.day}
                onChange={(e) => setForm((prev) => ({ ...prev, day: e.target.value }))}
                required
              />
              <input
                className="rounded-md border border-slate-300 px-3 py-2"
                type="number"
                min={1}
                max={monthMax}
                placeholder={t('events.form.month', { max: monthMax })}
                value={form.month}
                onChange={(e) => setForm((prev) => ({ ...prev, month: e.target.value }))}
                required
              />
              <input
                className="rounded-md border border-slate-300 px-3 py-2"
                type="number"
                min={1}
                max={9999}
                placeholder={t('events.form.year')}
                value={form.year}
                onChange={(e) => setForm((prev) => ({ ...prev, year: e.target.value }))}
                required={form.repeatType === 'none'}
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <input
                className="rounded-md border border-slate-300 px-3 py-2"
                type="time"
                placeholder={t('events.form.start_time')}
                value={form.startTime}
                onChange={(e) => setForm((prev) => ({ ...prev, startTime: e.target.value }))}
              />
              <input
                className="rounded-md border border-slate-300 px-3 py-2"
                type="time"
                placeholder={t('events.form.end_time')}
                value={form.endTime}
                onChange={(e) => setForm((prev) => ({ ...prev, endTime: e.target.value }))}
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <label className="text-sm text-slate-700">
                {t('events.form.calendar_type')}
                <select
                  className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
                  value={form.calendarType}
                  onChange={(e) => setForm((prev) => ({ ...prev, calendarType: e.target.value as CalendarType }))}
                  disabled={editingEventId !== null}
                  required
                >
                  <option value="gregorian">{t('events.calendar.gregorian')}</option>
                  <option value="hebrew">{t('events.calendar.hebrew')}</option>
                </select>
              </label>

              <label className="text-sm text-slate-700">
                {t('events.form.repeat_type')}
                <select
                  className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
                  value={form.repeatType}
                  onChange={(e) => setForm((prev) => ({ ...prev, repeatType: e.target.value as RepeatType }))}
                  required
                >
                  <option value="none">{t('events.repeat.none')}</option>
                  <option value="daily">{t('events.repeat.daily')}</option>
                  <option value="weekly">{t('events.repeat.weekly')}</option>
                  <option value="monthly">{t('events.repeat.monthly')}</option>
                  <option value="yearly">{t('events.repeat.yearly')}</option>
                </select>
              </label>
            </div>

            <div className="flex gap-3">
              <button
                className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:bg-blue-300"
                type="submit"
                disabled={isSubmitting}
              >
                {isSubmitting ? t('events.actions.saving') : editingEventId ? t('events.actions.update') : t('events.actions.create')}
              </button>
              {editingEventId ? (
                <button className="rounded-md border border-slate-300 px-4 py-2" type="button" onClick={resetForm}>
                  {t('common.cancel')}
                </button>
              ) : null}
            </div>
          </form>
        </article>

        <article className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <h2 className="text-lg font-semibold text-slate-900">{t('events.list_title')}</h2>
            <input
              className="rounded-md border border-slate-300 px-3 py-2"
              type="date"
              value={selectedDate}
              onChange={(event) => {
                setSelectedDate(event.target.value);
                setViewMode('date');
                if (!editingEventId) {
                  setForm(getDefaultFormState(event.target.value));
                }
              }}
              disabled={viewMode !== 'date'}
            />
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            <button
              className={`rounded-md px-3 py-2 text-sm ${viewMode === 'date' ? 'bg-blue-600 text-white' : 'border border-slate-300 text-slate-700 hover:bg-slate-50'}`}
              type="button"
              onClick={() => {
                setViewMode('date');
              }}
              disabled={isLoading}
            >
              {t('events.view.by_date')}
            </button>
            <button
              className={`rounded-md px-3 py-2 text-sm ${viewMode === 'today' ? 'bg-blue-600 text-white' : 'border border-slate-300 text-slate-700 hover:bg-slate-50'}`}
              type="button"
              onClick={() => {
                setViewMode('today');
              }}
              disabled={isLoading}
            >
              {t('events.view.today')}
            </button>
            <button
              className={`rounded-md px-3 py-2 text-sm ${viewMode === 'upcoming' ? 'bg-blue-600 text-white' : 'border border-slate-300 text-slate-700 hover:bg-slate-50'}`}
              type="button"
              onClick={() => {
                setViewMode('upcoming');
              }}
              disabled={isLoading}
            >
              {t('events.view.upcoming')}
            </button>
          </div>

          {viewMode === 'today' ? <p className="mt-3 text-xs text-slate-500">{t('events.messages.today')}</p> : null}
          {viewMode === 'upcoming' ? <p className="mt-3 text-xs text-slate-500">{t('events.messages.upcoming')}</p> : null}
          {viewMode !== 'date' ? <p className="mt-1 text-xs text-slate-500">{t('events.messages.date_mode')}</p> : null}

          {error ? <ErrorMessage message={error} /> : null}

          {isLoading ? <LoadingMessage message={t('events.loading')} /> : null}

          {!isLoading && events.length === 0 ? <EmptyMessage message={getEmptyMessage(viewMode)} /> : null}

          {!isLoading && events.length > 0 ? (
            <ul className="mt-4 space-y-3">
              {events.map((eventItem) => (
                <li key={eventItem.id} className="rounded-md border border-slate-200 p-3">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h3 className="font-medium text-slate-900">
                        <Link className="hover:text-blue-700 hover:underline" to={`/events/${eventItem.id}`}>
                          {eventItem.title}
                        </Link>
                      </h3>
                      <p className="text-sm text-slate-600">{eventItem.description || t('events.no_description')}</p>
                      <p className="mt-1 text-xs text-slate-500">
                        {t('events.family')} {eventItem.family_id} • {eventItem.month}/{eventItem.day}
                        {eventItem.year ? `/${eventItem.year}` : ''}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <button
                        className="rounded border border-slate-300 px-3 py-1 text-sm"
                        type="button"
                        onClick={() => startEdit(eventItem)}
                      >
                        {t('common.edit')}
                      </button>
                      <button
                        className="rounded border border-red-300 px-3 py-1 text-sm text-red-700"
                        type="button"
                        onClick={() => void handleDelete(eventItem.id)}
                      >
                        {t('common.delete')}
                      </button>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          ) : null}
        </article>
      </div>
    </section>
  );
}
