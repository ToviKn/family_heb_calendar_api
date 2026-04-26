import { NavLink, Outlet } from 'react-router-dom';

import { useAuth } from '../features/auth/AuthContext';

const navItems = [
  { to: '/', label: 'Home', end: true },
  { to: '/events', label: 'Events' },
  { to: '/families', label: 'Families' },
  { to: '/notifications', label: 'Notifications' },
  { to: '/convert', label: 'Conversion' },
] as const;

function navLinkClassName(isActive: boolean): string {
  return [
    'rounded-md px-3 py-2 text-sm font-medium transition-colors',
    isActive ? 'bg-blue-600 text-white' : 'text-slate-700 hover:bg-slate-100 hover:text-slate-900',
  ].join(' ');
}

export function AppLayout() {
  const { isAuthenticated } = useAuth();

  return (
    <main className="min-h-screen bg-slate-50">
      {isAuthenticated ? (
        <header className="border-b border-slate-200 bg-white">
          <nav className="mx-auto flex max-w-6xl flex-wrap items-center gap-2 px-4 py-3 sm:px-6" aria-label="Primary">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) => navLinkClassName(isActive)}
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </header>
      ) : null}

      <div className="mx-auto w-full max-w-6xl p-4 sm:p-6">
        <Outlet />
      </div>
    </main>
  );
}
