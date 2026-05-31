import type { ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import { NavLink, Outlet } from 'react-router-dom';

import { LanguageSwitcher } from '../components/LanguageSwitcher';

function navLinkClassName(isActive: boolean): string {
  return [
    'rounded-md px-3 py-2 text-sm font-medium transition-colors',
    isActive ? 'bg-blue-600 text-white' : 'text-slate-700 hover:bg-slate-100 hover:text-slate-900',
  ].join(' ');
}

export function AppLayout({ children }: { children?: ReactNode }) {
  const { t } = useTranslation();
  const navItems = [
    { to: '/', label: t('nav.home'), end: true },
    { to: '/events', label: t('nav.events') },
    { to: '/families', label: t('nav.families') },
    { to: '/notifications', label: t('nav.notifications') },
    { to: '/convert', label: t('nav.convert') },
    { to: '/settings', label: t('nav.settings') },
  ] as const;

  return (
    <main className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6">
          <nav className="flex flex-wrap items-center gap-2" aria-label="Primary">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                className={({ isActive }) => navLinkClassName(isActive)}
              >
                {item.label}
              </NavLink>
            ))}
          </nav>

          <LanguageSwitcher />
        </div>
      </header>

      <div className="mx-auto w-full max-w-6xl p-4 sm:p-6">
        {children ?? <Outlet />}
      </div>
    </main>
  );
}
