import { Link } from 'react-router-dom';

import { useAuth } from '../features/auth/AuthContext';

export function HomePage() {
  const { logout } = useAuth();

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <h1 className="text-2xl font-semibold text-slate-900">Family Hebrew Calendar</h1>
      <p className="mt-2 text-slate-600">You are logged in. Manage events and family membership from the dashboard.</p>
      <div className="mt-6 flex flex-wrap gap-3">
        <Link className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700" to="/events">
          Open events
        </Link>
        <Link className="rounded-md bg-indigo-600 px-4 py-2 text-white hover:bg-indigo-700" to="/families">
          Open families
        </Link>
        <button className="rounded-md bg-slate-800 px-4 py-2 text-white hover:bg-slate-900" onClick={logout} type="button">
          Logout
        </button>
      </div>
    </section>
  );
}
