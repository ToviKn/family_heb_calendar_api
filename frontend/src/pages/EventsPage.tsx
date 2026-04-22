import { FormEvent, useEffect, useMemo, useState } from 'react';

import {
  createEvent,
  deleteEvent,
  getEventsByDate,
  updateEvent,
  type EventCreate,
  type EventResponse,
} from '../lib/api';

interface EventFormState {
  title: string;
  description: string;
  familyId: string;
  month: string;
  day: string;
  year: string;
}

function toDateString(date: Date): string {
  return date.toISOString().slice(0, 10);
}

function buildCreatePayload(form: EventFormState): EventCreate {
  return {
    title: form.title,
    description: form.description || null,
    family_id: Number(form.familyId),
    month: Number(form.month),
    day: Number(form.day),
    year: form.year ? Number(form.year) : null,
    calendar_type: 'gregorian',
    repeat_type: 'none',
  };
}

function getDefaultFormState(date: Date): EventFormState {
  return {
    title: '',
    description: '',
    familyId: '',
    month: String(date.getUTCMonth() + 1),
    day: String(date.getUTCDate()),
    year: String(date.getUTCFullYear()),
  };
}

export function EventsPage() {
  const today = useMemo(() => new Date(), []);
  const [selectedDate, setSelectedDate] = useState<string>(toDateString(today));
  const [events, setEvents] = useState<EventResponse[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [editingEventId, setEditingEventId] = useState<number | null>(null);

  const [form, setForm] = useState<EventFormState>(() => getDefaultFormState(today));

  async function loadEvents(dateValue: string) {
    setIsLoading(true);
    setError(null);

    try {
      const date = new Date(`${dateValue}T00:00:00Z`);
      const result = await getEventsByDate({
        year: date.getUTCFullYear(),
        month: date.getUTCMonth() + 1,
        day: date.getUTCDate(),
      });
      setEvents(result.events);
    } catch {
      setError('Unable to load events for the selected date.');
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadEvents(selectedDate);
  }, [selectedDate]);

  function resetForm() {
    const date = new Date(`${selectedDate}T00:00:00Z`);
    setForm(getDefaultFormState(date));
    setEditingEventId(null);
  }

  async function handleCreateOrUpdate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
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
          repeat_type: 'none',
        });
      } else {
        await createEvent(buildCreatePayload(form));
      }

      await loadEvents(selectedDate);
      resetForm();
    } catch {
      setError('Unable to save event. Please verify all required fields.');
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
    });
  }

  async function handleDelete(eventId: number) {
    setError(null);

    try {
      await deleteEvent(eventId);
      await loadEvents(selectedDate);
      if (editingEventId === eventId) {
        resetForm();
      }
    } catch {
      setError('Unable to delete event.');
    }
  }

  return (
    <section className="space-y-6">
      <header className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h1 className="text-2xl font-semibold text-slate-900">Events</h1>
        <p className="mt-2 text-slate-600">Create, edit, and delete family events.</p>
      </header>

      <div className="grid gap-6 lg:grid-cols-2">
        <article className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">{editingEventId ? 'Edit event' : 'Create event'}</h2>

          <form className="mt-4 space-y-3" onSubmit={handleCreateOrUpdate}>
            <input
              className="w-full rounded-md border border-slate-300 px-3 py-2"
              placeholder="Title"
              value={form.title}
              onChange={(e) => setForm((prev) => ({ ...prev, title: e.target.value }))}
              required
            />

            <textarea
              className="w-full rounded-md border border-slate-300 px-3 py-2"
              placeholder="Description"
              value={form.description}
              onChange={(e) => setForm((prev) => ({ ...prev, description: e.target.value }))}
              rows={3}
            />

            <input
              className="w-full rounded-md border border-slate-300 px-3 py-2"
              placeholder="Family ID"
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
                max={12}
                placeholder="Month"
                value={form.month}
                onChange={(e) => setForm((prev) => ({ ...prev, month: e.target.value }))}
                required
              />
              <input
                className="rounded-md border border-slate-300 px-3 py-2"
                type="number"
                min={1}
                max={31}
                placeholder="Day"
                value={form.day}
                onChange={(e) => setForm((prev) => ({ ...prev, day: e.target.value }))}
                required
              />
              <input
                className="rounded-md border border-slate-300 px-3 py-2"
                type="number"
                min={1900}
                max={3000}
                placeholder="Year"
                value={form.year}
                onChange={(e) => setForm((prev) => ({ ...prev, year: e.target.value }))}
              />
            </div>

            <div className="flex gap-3">
              <button
                className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:bg-blue-300"
                type="submit"
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Saving...' : editingEventId ? 'Update event' : 'Create event'}
              </button>
              {editingEventId ? (
                <button className="rounded-md border border-slate-300 px-4 py-2" type="button" onClick={resetForm}>
                  Cancel
                </button>
              ) : null}
            </div>
          </form>
        </article>

        <article className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between gap-4">
            <h2 className="text-lg font-semibold text-slate-900">Events list</h2>
            <input
              className="rounded-md border border-slate-300 px-3 py-2"
              type="date"
              value={selectedDate}
              onChange={(event) => setSelectedDate(event.target.value)}
            />
          </div>

          {error ? <p className="mt-4 text-sm text-red-600">{error}</p> : null}

          {isLoading ? <p className="mt-4 text-slate-600">Loading events...</p> : null}

          {!isLoading && events.length === 0 ? <p className="mt-4 text-slate-600">No events found for this date.</p> : null}

          {!isLoading && events.length > 0 ? (
            <ul className="mt-4 space-y-3">
              {events.map((eventItem) => (
                <li key={eventItem.id} className="rounded-md border border-slate-200 p-3">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h3 className="font-medium text-slate-900">{eventItem.title}</h3>
                      <p className="text-sm text-slate-600">{eventItem.description || 'No description'}</p>
                      <p className="mt-1 text-xs text-slate-500">
                        Family {eventItem.family_id} • {eventItem.month}/{eventItem.day}
                        {eventItem.year ? `/${eventItem.year}` : ''}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <button className="rounded border border-slate-300 px-3 py-1 text-sm" onClick={() => startEdit(eventItem)}>
                        Edit
                      </button>
                      <button
                        className="rounded border border-red-300 px-3 py-1 text-sm text-red-700"
                        onClick={() => void handleDelete(eventItem.id)}
                      >
                        Delete
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
