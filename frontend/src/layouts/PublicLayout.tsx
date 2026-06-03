import type { ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, Outlet } from 'react-router-dom';

import { LanguageSwitcher } from '../components/LanguageSwitcher';

export function PublicLayout({ children }: { children?: ReactNode }) {
  const { t } = useTranslation();

  return (
    <main className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6">
          <Link className="text-sm font-semibold text-slate-900 hover:text-blue-700" to="/">
            {t('landing.app_name')}
          </Link>

          <LanguageSwitcher />
        </div>
      </header>

      <div className="mx-auto w-full max-w-6xl p-4 sm:p-6">
        {children ?? <Outlet />}
      </div>
    </main>
  );
}
