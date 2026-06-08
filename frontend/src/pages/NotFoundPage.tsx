import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

export function NotFoundPage() {
  const { t } = useTranslation();

  return (
    <section className="flex min-h-screen flex-col items-center justify-center gap-4 bg-slate-50 px-4 text-center">
      <h1 className="text-3xl font-semibold text-slate-900">{t('notFound.title')}</h1>
      <p className="max-w-md text-slate-600">{t('notFound.description')}</p>
      <Link className="text-blue-600 hover:text-blue-700" to="/">
        {t('notFound.backHome')}
      </Link>
    </section>
  );
}
