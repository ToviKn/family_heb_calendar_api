import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, useParams } from 'react-router-dom';

import { getEventById, type EventResponse } from '../lib/api';

function formatDate(event: EventResponse): string {
  const month = String(event.month).padStart(2, '0');
  const day = String(event.day).padStart(2, '0');

  if (!event.year) {
    return `${month}/${day}`;
  }

  return `${event.year}-${month}-${day}`;
}

function formatTimeRange(event: EventResponse, t: (key: string) => string): string {
  if (!event.start_time && !event.end_time) {
    return t('event_details.no_time');
  }

  if (event.start_time && event.end_time) {
    return `${event.start_time} - ${event.end_time}`;
  }

  return event.start_time ?? event.end_time ?? t('event_details.no_time');
}

export function EventDetailsPage() {
  const { t } = useTranslation();

  const { eventId } = useParams<{ eventId: string }>();
  const [event, setEvent] = useState<EventResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadEventDetails(idValue: string) {
      setIsLoading(true);
      setError(null);
      setEvent(null);

      try {
        const eventDetails = await getEventById(Number(idValue));
        setEvent(eventDetails);
      } catch {
        setError(t('event_details.errors.load'));
      } finally {
        setIsLoading(false);
      }
    }

    if (!eventId) {
      setEvent(null);
      setError(t('event_details.errors.missing_id'));
      return;
    }

    if (Number.isNaN(Number(eventId))) {
      setEvent(null);
      setError(t('event_details.errors.invalid_id'));
      return;
    }

    void loadEventDetails(eventId);
  }, [eventId]);

  return (
    <section className="space-y-6">
      <header className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h1 className="text-2xl font-semibold text-slate-900">{t('event_details.title')}</h1>
          <Link className="rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50" to="/events">
            {t('event_details.back')}
          </Link>
        </div>
      </header>

      <article className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        {error ? <p className="text-sm text-red-600">{error}</p> : null}

        {isLoading ? <p className="text-slate-600">{t('event_details.loading')}</p> : null}

        {!isLoading && !error && event ? (
          <div className="space-y-4">
            <div>
              <h2 className="text-xl font-semibold text-slate-900">{event.title}</h2>
              <p className="mt-1 text-sm text-slate-500">{t('event_details.event_id')}: {event.id}</p>
            </div>

            <dl className="grid gap-3 text-sm sm:grid-cols-2">
              <div className="rounded-md border border-slate-200 p-3">
                <dt className="font-medium text-slate-700">{t('event_details.fields.description')}</dt>
                <dd className="mt-1 text-slate-900">{event.description || t('event_details.no_description')}</dd>
              </div>

              <div className="rounded-md border border-slate-200 p-3">
                <dt className="font-medium text-slate-700">{t('event_details.fields.date')}</dt>
                <dd className="mt-1 text-slate-900">{formatDate(event)}</dd>
              </div>

              <div className="rounded-md border border-slate-200 p-3">
                <dt className="font-medium text-slate-700">{t('event_details.fields.time')}</dt>
                <dd className="mt-1 text-slate-900">{formatTimeRange(event, t)}</dd>
              </div>

              <div className="rounded-md border border-slate-200 p-3">
                <dt className="font-medium text-slate-700">{t('event_details.fields.repeat_type')}</dt>
                <dd className="mt-1 text-slate-900">event.repeat_type? t(`events.repeat.${event.repeat_type}`): t('events.repeat.none')</dd>
              </div>
            </dl>
          </div>
        ) : null}
      </article>
    </section>
  );
}
