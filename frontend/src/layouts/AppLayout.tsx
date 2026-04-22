import { Outlet } from 'react-router-dom';

export function AppLayout() {
  return (
    <main className="min-h-screen p-6">
      <Outlet />
    </main>
  );
}
