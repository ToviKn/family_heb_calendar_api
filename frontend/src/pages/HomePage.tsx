import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

import { useAuth } from '../features/auth/AuthContext';

export function HomePage() {
  const { t } = useTranslation();

  const { logout, user } = useAuth();

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <h1 className="text-2xl font-semibold text-slate-900">{t('home.title')}</h1>
      <p className="mt-2 text-slate-600">{t('home.description')}</p>
      <p className="text-sm text-slate-500">
        {t('home.welcome', { id: user?.id ?? '', name: user?.name ?? '' })}
      </p>
      <div className="mt-6 flex flex-wrap gap-3">
        <Link className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700" to="/events">
          {t('home.actions.events')}
        </Link>
        <Link className="rounded-md bg-indigo-600 px-4 py-2 text-white hover:bg-indigo-700" to="/families">
          {t('home.actions.families')}
        </Link>
        <Link className="rounded-md bg-violet-600 px-4 py-2 text-white hover:bg-violet-700" to="/notifications">
          {t('home.actions.notifications')}
        </Link>
        <button className="rounded-md bg-slate-800 px-4 py-2 text-white hover:bg-slate-900" onClick={logout} type="button">
          {t('home.actions.logout')}
        </button>
      </div>
    </section>
  );
}
