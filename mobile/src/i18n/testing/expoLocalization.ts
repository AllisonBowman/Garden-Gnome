// jest stand-in for expo-localization (mapped in jest.config.js): the native
// module can't load in node. Reports en-US unless a test sets
// globalThis.__TEST_LOCALES__ before (re)loading src/i18n, for example:
//
//   (globalThis as any).__TEST_LOCALES__ = ['es-MX'];
//   jest.isolateModules(() => { const { t } = require('../i18n'); ... });
export function getLocales(): { languageTag: string; languageCode: string }[] {
  const tags: string[] = (globalThis as { __TEST_LOCALES__?: string[] }).__TEST_LOCALES__ ?? ['en-US'];
  return tags.map((tag) => ({ languageTag: tag, languageCode: tag.split(/[-_]/)[0] }));
}
