// Typed keys: t('home.title') is checked against the English resource.
import 'i18next';
import type en from './en';

declare module 'i18next' {
  interface CustomTypeOptions {
    defaultNS: 'translation';
    resources: { translation: typeof en };
  }
}
