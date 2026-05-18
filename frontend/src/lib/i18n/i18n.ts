import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import enCommon from './locales/en/common.json';
import heCommon from './locales/he/common.json';

i18n.use(initReactI18next).init({
  resources: {
    en: {
      translation: enCommon,
    },
    he: {
      translation: heCommon,
    },
  },
  lng: localStorage.getItem('language') || 'he',
  fallbackLng: 'en',
  interpolation: {
    escapeValue: false,
  },
});

export default i18n;

i18n.on('languageChanged', (lng) => {
  document.documentElement.lang = lng;
  document.documentElement.dir = lng === 'he' ? 'rtl' : 'ltr';

  localStorage.setItem('language', lng);
});

document.documentElement.lang = i18n.language;
document.documentElement.dir = i18n.language === 'he' ? 'rtl' : 'ltr';