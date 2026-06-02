import { Navigate, Route, Routes } from 'react-router-dom';

import { ProtectedRoute } from './ProtectedRoute';
import { AppLayout } from '../layouts/AppLayout';
import { PublicLayout } from '../layouts/PublicLayout';
import { useAuth } from '../features/auth/AuthContext';
import { ConvertPage } from '../pages/ConvertPage';
import { EventDetailsPage } from '../pages/EventDetailsPage';
import { EventsPage } from '../pages/EventsPage';
import { FamiliesPage } from '../pages/FamiliesPage';
import { HomePage } from '../pages/HomePage';
import { LandingPage } from '../pages/LandingPage';
import { LoginPage } from '../pages/LoginPage';
import { NotFoundPage } from '../pages/NotFoundPage';
import { NotificationsPage } from '../pages/NotificationsPage';
import { RegisterPage } from '../pages/RegisterPage';
import { SettingsPage } from '../pages/SettingsPage';

function RootPage() {
  const { isAuthenticated } = useAuth();

  if (isAuthenticated) {
    return (
      <AppLayout>
        <HomePage />
      </AppLayout>
    );
  }

  return (
    <PublicLayout>
      <LandingPage />
    </PublicLayout>
  );
}

export function AppRouter() {
  return (
    <Routes>
      <Route index element={<RootPage />} />

      <Route element={<PublicLayout />}>
        <Route path="/landing" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="convert" element={<ConvertPage />} />
      </Route>

      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="events" element={<EventsPage />} />
          <Route path="events/:eventId" element={<EventDetailsPage />} />
          <Route path="families" element={<FamiliesPage />} />
          <Route path="notifications" element={<NotificationsPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
      </Route>

      <Route path="/404" element={<NotFoundPage />} />
      <Route path="*" element={<Navigate to="/404" replace />} />
    </Routes>
  );
}
