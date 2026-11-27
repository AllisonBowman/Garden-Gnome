// The app's translations: English and Spanish, chosen once at launch from the
// phone's language (language.ts).
//
// i18next on its own, without react-i18next: there is no in-app language
// switch, and iOS relaunches an app when its language changes, so nothing
// ever needs to re-render on a language change. One plain `t` works the same
// in a component, in the pure modules that compose sentences, and in jest.
//
// Initialised synchronously on import, so a module that builds a string at
// load time (or exports one) gets the right language as long as it imports
// `t` from here. Under jest, expo-localization is mapped to a stub
// (testing/expoLocalization.ts) that says en-US unless a test says otherwise.
import i18next from 'i18next';
import { getLocales } from 'expo-localization';
import en from './en';
import es from './es';
import { resolveLanguage } from './language';
import type { Language } from './types';

export type { Language } from './types';
export { resolveLanguage } from './language';

function deviceLanguage(): Language {
  try {
    return resolveLanguage(getLocales().map((l) => l.languageTag));
  } catch {
    return 'en';
  }
}

export const language: Language = deviceLanguage();

const i18n = i18next.createInstance();
i18n.init({
  lng: language,
  fallbackLng: 'en',
  resources: { en: { translation: en }, es: { translation: es } },
  initAsync: false,
  interpolation: { escapeValue: false },
  returnNull: false,
});

export const t = i18n.t.bind(i18n);
export default i18n;

/** The BCP 47 tag for Intl and toLocale* calls that should follow the app's
 *  language rather than the phone's region (en-US / es-US). */
export const localeTag = language === 'es' ? 'es-US' : 'en-US';
