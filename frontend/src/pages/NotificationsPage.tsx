import { useEffect, useState } from 'react';

import { getNotifications, markNotificationRead, type NotificationResponse } from '../lib/api';

export function NotificationsPage() {
  const [notifications, setNotifications] = useState<NotificationResponse[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [updatingId, setUpdatingId] = useState<number | null>(null);

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

  return (
    <section className="space-y-6">
      <header className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h1 className="text-2xl font-semibold text-slate-900">Notifications</h1>
        <p className="mt-2 text-slate-600">Review notifications and mark them as read.</p>
      </header>

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

        {!isLoading && notifications.length === 0 ? (
          <p className="mt-4 text-slate-600">No notifications available.</p>
        ) : null}

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

                  {!notification.is_read ? (
                    <button
                      className="rounded-md bg-blue-600 px-3 py-1 text-sm text-white hover:bg-blue-700 disabled:bg-blue-300"
                      type="button"
                      onClick={() => void handleMarkAsRead(notification.id)}
                      disabled={updatingId === notification.id}
                    >
                      {updatingId === notification.id ? 'Marking...' : 'Mark as read'}
                    </button>
                  ) : (
                    <span className="text-xs text-slate-500">Read</span>
                  )}
                </div>
              </li>
            ))}
          </ul>
        ) : null}
      </article>
    </section>
  );
}
