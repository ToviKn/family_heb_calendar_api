import { useAuth } from '../features/auth/AuthContext';

export function HomePage() {
  const { logout } = useAuth();

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <h1 className="text-2xl font-semibold text-slate-900">Family Hebrew Calendar</h1>
      <p className="mt-2 text-slate-600">You are logged in. Feature screens can now be built on top of this auth flow.</p>
      <button
        className="mt-6 rounded-md bg-slate-800 px-4 py-2 text-white hover:bg-slate-900"
        onClick={logout}
        type="button"
      >
        Logout
      </button>
    </section>
  );
}
