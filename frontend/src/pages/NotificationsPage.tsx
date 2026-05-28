import { EmptyMessage, ErrorMessage, LoadingMessage, SuccessMessage } from '../components/Feedback';
import { FormEvent, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { formatNotificationCreatedAt, getNotificationMetadata, getNotificationSummary } from '../lib/notifications/formatters';
import {
  createNotification,
  deleteNotification,
  getNotifications,
  markNotificationRead,
  processNotificationReminders,
  type NotificationResponse,
} from '../lib/api';

interface CreateNotificationForm {
  eventId: string;
}


export function NotificationsPage() {
  const { t, i18n } = useTranslation();

  const [notifications, setNotifications] = useState<NotificationResponse[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [updatingId, setUpdatingId] = useState<number | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const [createForm, setCreateForm] = useState<CreateNotificationForm>({ eventId: '' });
  const [isCreating, setIsCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [createSuccess, setCreateSuccess] = useState<string | null>(null);

  const [isProcessingReminders, setIsProcessingReminders] = useState(false);
  const [processSuccess, setProcessSuccess] = useState<string | null>(null);

  async function loadNotifications() {
    setIsLoading(true);
    setError(null);

    try {
      const response = await getNotifications();
      setNotifications(response.notifications ?? response.events);
    } catch {
      setError(t('notifications.errors.load'));
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadNotifications();
  }, []);

  async function handleMarkAsRead(notificationId: number) {
    setUpdatingId(notificationId);
    setError(null);
    setProcessSuccess(null);

    try {
      const updated = await markNotificationRead(notificationId);
      setNotifications((previous) =>
        previous.map((item) => {
          if (item.id !== notificationId) {
            return item;
          }

          return updated;
        })
      );
    } catch {
      setError(t('notifications.errors.mark_read'));
    } finally {
      setUpdatingId(null);
    }
  }

  async function handleDeleteNotification(notificationId: number) {
    setDeletingId(notificationId);
    setError(null);
    setProcessSuccess(null);

    try {
      await deleteNotification(notificationId);
      setNotifications((previous) => previous.filter((item) => item.id !== notificationId));
    } catch {
      setError(t('notifications.errors.delete'));
    } finally {
      setDeletingId(null);
    }
  }

  async function handleCreateNotification(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const parsedEventId = Number(createForm.eventId);
    if (!Number.isInteger(parsedEventId) || parsedEventId <= 0) {
      setCreateError(t('notifications.errors.invalid_event_id'));
      setCreateSuccess(null);
      return;
    }

    setCreateError(null);
    setCreateSuccess(null);
    setError(null);
    setIsCreating(true);

    try {
      const created = await createNotification({ event_id: parsedEventId });
      setNotifications((previous) => [created, ...previous]);
      setCreateForm({ eventId: '' });
      setCreateSuccess(t('notifications.success.created'));
    } catch {
      setCreateError(t('notifications.errors.create'));
    } finally {
      setIsCreating(false);
    }
  }

  async function handleProcessReminders() {
    setProcessSuccess(null);
    setCreateError(null);
    setCreateSuccess(null);
    setError(null);
    setIsProcessingReminders(true);

    try {
      const result = await processNotificationReminders();
      setProcessSuccess(t('notifications.success.processed', {count: result.created,}));
      await loadNotifications();
    } catch {
      setError(t('notifications.errors.process'));
    } finally {
      setIsProcessingReminders(false);
    }
  }

  return (
    <section className="space-y-6">
      <header className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h1 className="text-2xl font-semibold text-slate-900">{t('notifications.title')}</h1>
        <p className="mt-2 text-slate-600">{t('notifications.description')}</p>
      </header>

      <div className="grid gap-6 lg:grid-cols-2">
        <article className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">{t('notifications.create.title')}</h2>

          <form className="mt-4 space-y-3" onSubmit={handleCreateNotification}>
            <input
              className="w-full rounded-md border border-slate-300 px-3 py-2"
              type="number"
              min={1}
              placeholder={t('notifications.create.event_id_placeholder')}
              value={createForm.eventId}
              onChange={(event) => {
                setCreateForm({ eventId: event.target.value });
                if (createError) {
                  setCreateError(null);
                }
                if (createSuccess) {
                  setCreateSuccess(null);
                }
              }}
              required
            />

            <button
              className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:bg-blue-300"
              type="submit"
              disabled={isCreating}
            >
              {isCreating ? t('notifications.actions.creating') : t('notifications.actions.create')}
            </button>
          </form>

          {createError ? <ErrorMessage message={createError} /> : null}
          {createSuccess ? <SuccessMessage message={createSuccess} /> : null}
        </article>

        <article className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">{t('notifications.process.title')}</h2>
          <p className="mt-2 text-sm text-slate-600">{t('notifications.process.description')}</p>

          <button
            className="mt-4 rounded-md bg-indigo-600 px-4 py-2 text-white hover:bg-indigo-700 disabled:bg-indigo-300"
            type="button"
            onClick={() => void handleProcessReminders()}
            disabled={isProcessingReminders}
          >
            {isProcessingReminders ? t('notifications.actions.processing') : t('notifications.actions.process')}
          </button>

          {processSuccess ? <SuccessMessage message={processSuccess} /> : null}
        </article>
      </div>

      <article className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-900">{t('notifications.list.title')}</h2>
          <button
            className="rounded-md border border-slate-300 px-3 py-1 text-sm text-slate-700 hover:bg-slate-50"
            type="button"
            onClick={() => void loadNotifications()}
            disabled={isLoading}
          >
            {t('notifications.actions.refresh')}
          </button>
        </div>

        {error ? <ErrorMessage message={error} /> : null}
        {isLoading ? <LoadingMessage message={t('notifications.loading')} /> : null}

        {!isLoading && notifications.length === 0 ? <EmptyMessage message={t('notifications.empty')} /> : null}

        {!isLoading && notifications.length > 0 ? (
          <ul className="mt-4 space-y-3">
            {notifications.map((notification) => {
              const metadata = getNotificationMetadata(notification);
              console.log('Notification metadata:', metadata);
              console.log('formatted_hebrew_date:', metadata.formatted_hebrew_date);
              console.log('calendar_type:', metadata.calendar_type);
              const summary = getNotificationSummary(notification, t, i18n.language);

              return (
              <li
                key={notification.id}
                className={`rounded-md border p-3 ${notification.is_read ? 'border-slate-200 bg-slate-50' : 'border-blue-200 bg-blue-50'}`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-medium text-slate-900">{summary.title || t('notifications.default_title')}</p>
                    <p className="mt-1 text-sm text-slate-600" dir={summary.direction}>{summary.subtitle || t('notifications.default_subtitle')}</p>
                    <p className="mt-1 text-xs text-slate-500">
                      {t('notifications.created_label')}: {formatNotificationCreatedAt(notification.created_at, i18n.language)}
                      {notification.event_id ? ` • ${t('notifications.event_id_label')}: ${notification.event_id}` : ''}
                    </p>
                  </div>

                  <div className="flex gap-2">
                    {!notification.is_read ? (
                      <button
                        className="rounded-md bg-blue-600 px-3 py-1 text-sm text-white hover:bg-blue-700 disabled:bg-blue-300"
                        type="button"
                        onClick={() => void handleMarkAsRead(notification.id)}
                        disabled={updatingId === notification.id || deletingId === notification.id}
                      >
                        {updatingId === notification.id ? t('notifications.actions.marking') : t('notifications.actions.mark_read')}
                      </button>
                    ) : (
                      <span className="self-center text-xs text-slate-500">{t('notifications.read')}</span>
                    )}

                    <button
                      className="rounded-md border border-red-300 px-3 py-1 text-sm text-red-700 hover:bg-red-50 disabled:border-red-200 disabled:text-red-300"
                      type="button"
                      onClick={() => void handleDeleteNotification(notification.id)}
                      disabled={deletingId === notification.id || updatingId === notification.id}
                    >
                      {deletingId === notification.id ? t('notifications.actions.deleting') : t('notifications.actions.delete')}
                    </button>
                  </div>
                </div>
              </li>
            );
            })}
          </ul>
        ) : null}
      </article>
    </section>
  );
}
