import { useTranslation } from 'react-i18next';

import { useAuth } from '../features/auth/AuthContext';

export function LanguageSwitcher() {
  const { i18n, t } = useTranslation();
  const { setLanguage } = useAuth();

  return (
    <div className="flex items-center gap-2">
      <button
        type="button"
        onClick={() => void setLanguage('he')}
        className={`rounded-md px-3 py-1 text-sm ${
          i18n.language === 'he'
            ? 'bg-blue-600 text-white'
            : 'bg-slate-200 text-slate-700'
        }`}
      >
        {t('language.hebrew')}
      </button>

      <button
        type="button"
        onClick={() => void setLanguage('en')}
        className={`rounded-md px-3 py-1 text-sm ${
          i18n.language === 'en'
            ? 'bg-blue-600 text-white'
            : 'bg-slate-200 text-slate-700'
        }`}
      >
        {t('language.english')}
      </button>
    </div>
  );
}
