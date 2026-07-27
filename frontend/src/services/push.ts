import { apiClient } from '../lib/api/axios';

export type BrowserNotificationPermission = NotificationPermission | 'unsupported';

function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = window.atob(base64);
  return Uint8Array.from([...rawData].map((char) => char.charCodeAt(0)));
}

export function getBrowserNotificationPermission(): BrowserNotificationPermission {
  if (!('Notification' in window) || !('serviceWorker' in navigator) || !('PushManager' in window)) {
    return 'unsupported';
  }
  return Notification.permission;
}

export async function registerServiceWorker(): Promise<ServiceWorkerRegistration> {
  return navigator.serviceWorker.register('/service-worker.js');
}

export async function subscribeToPushNotifications(): Promise<PushSubscription | null> {
  if (getBrowserNotificationPermission() === 'unsupported') return null;
  const permission = await Notification.requestPermission();
  if (permission !== 'granted') return null;
  const vapidPublicKey = import.meta.env.VITE_VAPID_PUBLIC_KEY as string | undefined;
  if (!vapidPublicKey) throw new Error('VITE_VAPID_PUBLIC_KEY is required');
  const registration = await registerServiceWorker();
  const subscription = await registration.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: urlBase64ToUint8Array(vapidPublicKey) });
  await apiClient.post('/api/push/subscribe', subscription.toJSON());
  return subscription;
}
