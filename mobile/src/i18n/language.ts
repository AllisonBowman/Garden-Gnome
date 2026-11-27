// Which language the app speaks, from the phone's own language list.
//
// Pure, so jest can pin it. Only the first preferred language counts: a phone
// whose first language is Spanish, in any region (es, es-US, es-MX, es-419,
// ...), gets Spanish; everything else gets English, the language the app was
// written in.
import type { Language } from './types';

export function resolveLanguage(tags: readonly (string | null | undefined)[]): Language {
  const first = (tags[0] ?? '').trim().toLowerCase();
  return first === 'es' || first.startsWith('es-') || first.startsWith('es_') ? 'es' : 'en';
}
