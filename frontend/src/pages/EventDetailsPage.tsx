import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import { getEventById, type EventResponse } from '../lib/api';

function formatDate(event: EventResponse): string {
  const month = String(event.month).padStart(2, '0');
  const day = String(event.day).padStart(2, '0');
  const year = event.year ? String(event.year) : 'Recurring';
  return `${year}-${month}-${day}`;
}

function formatTimeRange(event: EventResponse): string {
  if (!event.start_time && !event.end_time) {
    return 'No time specified';
  }

  if (event.start_time && event.end_time) {
    return `${event.start_time} - ${event.end_time}`;
  }

  return event.start_time ?? event.end_time ?? 'No time specified';
}

export function EventDetailsPage() {
  const { eventId } = useParams<{ eventId: string }>();
  const [event, setEvent] = useState<EventResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadEventDetails(idValue: string) {
      setIsLoading(true);
      setError(null);

      try {
        const eventDetails = await getEventById(Number(idValue));
        setEvent(eventDetails);
      } catch {
        setError('Unable to load event details.');
      } finally {
        setIsLoading(false);
      }
    }

    if (!eventId) {
      setError('Event ID is missing.');
      return;
    }

    if (Number.isNaN(Number(eventId))) {
      setError('Invalid event ID.');
      return;
    }

    void loadEventDetails(eventId);
  }, [eventId]);

  return (
    <section className="space-y-6">
      <header className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h1 className="text-2xl font-semibold text-slate-900">Event details</h1>
          <Link className="rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50" to="/events">
            Back to events
          </Link>
        </div>
      </header>

      <article className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        {error ? <p className="text-sm text-red-600">{error}</p> : null}

        {isLoading ? <p className="text-slate-600">Loading event details...</p> : null}

        {!isLoading && !error && event ? (
          <div className="space-y-4">
            <div>
              <h2 className="text-xl font-semibold text-slate-900">{event.title}</h2>
              <p className="mt-1 text-sm text-slate-500">Event ID: {event.id}</p>
            </div>

            <dl className="grid gap-3 text-sm sm:grid-cols-2">
              <div className="rounded-md border border-slate-200 p-3">
                <dt className="font-medium text-slate-700">Description</dt>
                <dd className="mt-1 text-slate-900">{event.description || 'No description'}</dd>
              </div>

              <div className="rounded-md border border-slate-200 p-3">
                <dt className="font-medium text-slate-700">Date</dt>
                <dd className="mt-1 text-slate-900">{formatDate(event)}</dd>
              </div>

              <div className="rounded-md border border-slate-200 p-3">
                <dt className="font-medium text-slate-700">Time</dt>
                <dd className="mt-1 text-slate-900">{formatTimeRange(event)}</dd>
              </div>

              <div className="rounded-md border border-slate-200 p-3">
                <dt className="font-medium text-slate-700">Repeat type</dt>
                <dd className="mt-1 text-slate-900">{event.repeat_type || 'none'}</dd>
              </div>
            </dl>
          </div>
        ) : null}
      </article>
    </section>
  );
}
