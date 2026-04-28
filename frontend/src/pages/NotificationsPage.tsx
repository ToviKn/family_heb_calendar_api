import { FormEvent, useEffect, useState } from 'react';

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
      setError('Unable to load notifications.');
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
      setError('Unable to mark notification as read.');
    } finally {
      setUpdatingId(null);
    }
  }

  async function handleDeleteNotification(notificationId: number) {
    setDeletingId(notificationId);
    setError(null);

    try {
      await deleteNotification(notificationId);
      setNotifications((previous) => previous.filter((item) => item.id !== notificationId));
    } catch {
      setError('Unable to delete notification.');
    } finally {
      setDeletingId(null);
    }
  }

  async function handleCreateNotification(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setCreateError(null);
    setCreateSuccess(null);
    setIsCreating(true);

    try {
      const created = await createNotification({ event_id: Number(createForm.eventId) });
      setNotifications((previous) => [created, ...previous]);
      setCreateForm({ eventId: '' });
      setCreateSuccess('Notification created successfully.');
    } catch {
      setCreateError('Unable to create notification. Verify event ID.');
    } finally {
      setIsCreating(false);
    }
  }

  async function handleProcessReminders() {
    setProcessSuccess(null);
    setError(null);
    setIsProcessingReminders(true);

    try {
      const result = await processNotificationReminders();
      setProcessSuccess(`Processed reminders. Created ${result.created} notifications.`);
      await loadNotifications();
    } catch {
      setError('Unable to process reminders.');
    } finally {
      setIsProcessingReminders(false);
    }
  }

  return (
    <section className="space-y-6">
      <header className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h1 className="text-2xl font-semibold text-slate-900">Notifications</h1>
        <p className="mt-2 text-slate-600">Review notifications, create new notifications, and process reminders.</p>
      </header>

      <div className="grid gap-6 lg:grid-cols-2">
        <article className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Create notification</h2>

          <form className="mt-4 space-y-3" onSubmit={handleCreateNotification}>
            <input
              className="w-full rounded-md border border-slate-300 px-3 py-2"
              type="number"
              min={1}
              placeholder="Event ID"
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
              {isCreating ? 'Creating...' : 'Create notification'}
            </button>
          </form>

          {createError ? <p className="mt-3 text-sm text-red-600">{createError}</p> : null}
          {createSuccess ? <p className="mt-3 text-sm text-emerald-700">{createSuccess}</p> : null}
        </article>

        <article className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Process reminders</h2>
          <p className="mt-2 text-sm text-slate-600">Generate notifications for due event reminders.</p>

          <button
            className="mt-4 rounded-md bg-indigo-600 px-4 py-2 text-white hover:bg-indigo-700 disabled:bg-indigo-300"
            type="button"
            onClick={() => void handleProcessReminders()}
            disabled={isProcessingReminders}
          >
            {isProcessingReminders ? 'Processing...' : 'Process reminders'}
          </button>

          {processSuccess ? <p className="mt-3 text-sm text-emerald-700">{processSuccess}</p> : null}
        </article>
      </div>

      <article className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-900">Your notifications</h2>
          <button
            className="rounded-md border border-slate-300 px-3 py-1 text-sm text-slate-700 hover:bg-slate-50"
            type="button"
            onClick={() => void loadNotifications()}
            disabled={isLoading}
          >
            Refresh
          </button>
        </div>

        {error ? <p className="mt-4 text-sm text-red-600">{error}</p> : null}
        {isLoading ? <p className="mt-4 text-slate-600">Loading...</p> : null}

        {!isLoading && notifications.length === 0 ? <p className="mt-4 text-slate-600">No notifications available.</p> : null}

        {!isLoading && notifications.length > 0 ? (
          <ul className="mt-4 space-y-3">
            {notifications.map((notification) => (
              <li
                key={notification.id}
                className={`rounded-md border p-3 ${notification.is_read ? 'border-slate-200 bg-slate-50' : 'border-blue-200 bg-blue-50'}`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-medium text-slate-900">{notification.message}</p>
                    <p className="mt-1 text-xs text-slate-500">Type: {notification.type}</p>
                  </div>

                  <div className="flex gap-2">
                    {!notification.is_read ? (
                      <button
                        className="rounded-md bg-blue-600 px-3 py-1 text-sm text-white hover:bg-blue-700 disabled:bg-blue-300"
                        type="button"
                        onClick={() => void handleMarkAsRead(notification.id)}
                        disabled={updatingId === notification.id || deletingId === notification.id}
                      >
                        {updatingId === notification.id ? 'Marking...' : 'Mark as read'}
                      </button>
                    ) : (
                      <span className="self-center text-xs text-slate-500">Read</span>
                    )}

                    <button
                      className="rounded-md border border-red-300 px-3 py-1 text-sm text-red-700 hover:bg-red-50 disabled:border-red-200 disabled:text-red-300"
                      type="button"
                      onClick={() => void handleDeleteNotification(notification.id)}
                      disabled={deletingId === notification.id || updatingId === notification.id}
                    >
                      {deletingId === notification.id ? 'Deleting...' : 'Delete'}
                    </button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        ) : null}
      </article>
    </section>
  );
}
