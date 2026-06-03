import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';

export function LandingPage() {
  const { t } = useTranslation();

  return (
    <section className="mx-auto mt-16 max-w-3xl rounded-lg border border-slate-200 bg-white p-8 text-center shadow-sm">
      <p className="text-sm font-medium uppercase tracking-wide text-blue-600">
        {t('landing.app_name')}
      </p>
      <h1 className="mt-3 text-3xl font-semibold text-slate-900 sm:text-4xl">
        {t('landing.title')}
      </h1>
      <p className="mx-auto mt-4 max-w-2xl text-base text-slate-600">
        {t('landing.description')}
      </p>

      <div className="mt-8 flex flex-wrap justify-center gap-3">
        <Link className="rounded-md bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700" to="/login">
          {t('landing.actions.login')}
        </Link>
        <Link className="rounded-md bg-slate-800 px-4 py-2 font-medium text-white hover:bg-slate-900" to="/register">
          {t('landing.actions.register')}
        </Link>
      </div>
    </section>
  );
}
