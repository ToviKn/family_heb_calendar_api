import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import enCommon from './locales/en/common.json';
import heCommon from './locales/he/common.json';

const LANGUAGE_STORAGE_KEY = 'language';
const SUPPORTED_LANGUAGES = ['en', 'he'] as const;

type SupportedLanguage = (typeof SUPPORTED_LANGUAGES)[number];

function isSupportedLanguage(language: string | null): language is SupportedLanguage {
  return SUPPORTED_LANGUAGES.includes(language as SupportedLanguage);
}

function getInitialLanguage(): SupportedLanguage {
  const savedLanguage = localStorage.getItem(LANGUAGE_STORAGE_KEY);

  if (isSupportedLanguage(savedLanguage)) {
    return savedLanguage;
  }

  return navigator.language.toLowerCase().startsWith('he') ? 'he' : 'en';
}

function applyDocumentLanguage(language: string): void {
  const resolvedLanguage = language.startsWith('he') ? 'he' : 'en';

  document.documentElement.lang = resolvedLanguage;
  document.documentElement.dir = resolvedLanguage === 'he' ? 'rtl' : 'ltr';
}

const initialLanguage = getInitialLanguage();
applyDocumentLanguage(initialLanguage);

i18n.use(initReactI18next).init({
  resources: {
    en: {
      translation: enCommon,
    },
    he: {
      translation: heCommon,
    },
  },
  lng: initialLanguage,
  fallbackLng: 'en',
  interpolation: {
    escapeValue: false,
  },
});

i18n.on('languageChanged', (language) => {
  applyDocumentLanguage(language);
  localStorage.setItem(LANGUAGE_STORAGE_KEY, language.startsWith('he') ? 'he' : 'en');
});

export default i18n;
