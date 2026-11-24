import { resolveLanguage } from './language';
import en from './en';
import es, { ES_META } from './es';

type Tree = { [k: string]: string | Tree };

function leaves(tree: Tree, prefix = ''): Map<string, string> {
  const out = new Map<string, string>();
  for (const [k, v] of Object.entries(tree)) {
    const key = prefix ? `${prefix}.${k}` : k;
    if (typeof v === 'string') out.set(key, v);
    else for (const [kk, vv] of leaves(v, key)) out.set(kk, vv);
  }
  return out;
}

const placeholders = (s: string) => [...s.matchAll(/\{\{\s*([\w.]+)\s*(?:,[^}]*)?\}\}/g)].map((m) => m[1]).sort();
// Spanish plurals may add a _many form (CLDR uses it for round millions).
const base = (k: string) => k.replace(/_many$/, '_other');

describe('resolveLanguage', () => {
  it.each(['es', 'es-US', 'es-MX', 'es-419', 'es-ES', 'ES-mx', 'es_US'])('%s is Spanish', (tag) => {
    expect(resolveLanguage([tag])).toBe('es');
  });
  it.each(['en-US', 'en', 'fr-FR', 'pt-BR', 'esperanto', 'et-EE', '', 'zz'])('%s is English', (tag) => {
    expect(resolveLanguage([tag])).toBe('en');
  });
  it('reads only the first preferred language', () => {
    expect(resolveLanguage(['fr-FR', 'es-MX'])).toBe('en');
    expect(resolveLanguage(['es-MX', 'en-US'])).toBe('es');
  });
  it('falls back to English with no languages at all', () => {
    expect(resolveLanguage([])).toBe('en');
    expect(resolveLanguage([null, undefined])).toBe('en');
  });
});

describe('the Spanish resource', () => {
  const enLeaves = leaves(en as unknown as Tree);
  const esLeaves = leaves(es as unknown as Tree);

  it('is marked as needing a native speaker’s review', () => {
    expect(ES_META.needsReview).toBe(true);
  });

  it('has every English key and no others', () => {
    const missing = [...enLeaves.keys()].filter((k) => !esLeaves.has(k));
    const extra = [...esLeaves.keys()].filter((k) => !enLeaves.has(base(k)));
    expect(missing).toEqual([]);
    expect(extra).toEqual([]);
  });

  it('keeps the same {{placeholders}} in every string', () => {
    const mismatched = [...esLeaves.entries()]
      .filter(([k, v]) => enLeaves.has(base(k)) && placeholders(v).join() !== placeholders(enLeaves.get(base(k))!).join())
      .map(([k]) => k);
    expect(mismatched).toEqual([]);
  });

  it('leaves no string empty', () => {
    expect([...esLeaves.entries()].filter(([, v]) => v.trim() === '').map(([k]) => k)).toEqual([]);
  });
});

describe('the device language', () => {
  afterEach(() => { delete (globalThis as { __TEST_LOCALES__?: string[] }).__TEST_LOCALES__; });

  function load(tags?: string[]) {
    if (tags) (globalThis as { __TEST_LOCALES__?: string[] }).__TEST_LOCALES__ = tags;
    let mod: typeof import('./index') | undefined;
    jest.isolateModules(() => { mod = require('./index'); });
    return mod!;
  }

  it('is English in tests unless a test asks otherwise', () => {
    expect(load().language).toBe('en');
  });

  it.each(['es-US', 'es-MX', 'es-419', 'es'])('a phone in %s speaks Spanish', (tag) => {
    const i = load([tag]);
    expect(i.language).toBe('es');
    expect(i.localeTag).toBe('es-US');
  });

  it('a phone in French speaks English', () => {
    expect(load(['fr-FR']).language).toBe('en');
  });
});
