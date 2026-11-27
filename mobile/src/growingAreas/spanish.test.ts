// The growing-area wording in Spanish: a phone set to es-MX gets it, with
// lists joined by "y" and counts that agree with their nouns.
type G = typeof globalThis & { __TEST_LOCALES__?: string[] };

afterEach(() => { delete (globalThis as G).__TEST_LOCALES__; });

function inSpanish<T>(path: string): T {
  (globalThis as G).__TEST_LOCALES__ = ['es-MX'];
  let mod: T | undefined;
  jest.isolateModules(() => { mod = require(path); });
  return mod!;
}

test('fit findings join a Spanish list with y', () => {
  const ff = inSpanish<typeof import('./fitFindings')>('./fitFindings');
  expect(ff.joinAnd(['sol', 'suelo', 'tamaño'])).toBe('sol, suelo y tamaño');
  expect(ff.confirmedLine([
    { axis: 'sun', verdict: 'fits', sentence: '' },
    { axis: 'soil', verdict: 'fits', sentence: '' },
  ] as never)).toBe('Confirmado aquí: sol y suelo.');
  expect(ff.misfitIntro('Patio')).toBe('Conviene saberlo antes de plantarla en Patio');
});

test('the area setup speaks Spanish', () => {
  const re = inSpanish<typeof import('./realEstate')>('./realEstate');
  expect(re.SURFACE_LABEL.raised_bed).toBe('🪵 Cama elevada');
  expect(re.surfaceName('raised_bed')).toBe('Cama elevada');
  expect(re.goalPhrase('edible')).toBe('algo para comer');
  expect(re.areaTypeLabel('community_garden')).toBe('🌳 Huerto comunitario');
  expect(re.dimensionPrompts('raised_bed').depth.label).toBe('Profundidad del suelo (pulgadas)');
  expect(re.setupBlocker(0, ' ')).toMatch(/^Ponle un nombre/);
});

test('the ranked list says its count in Spanish', () => {
  const r = inSpanish<typeof import('./ranking')>('./ranking');
  expect(r.listIntro(1, 1)).toMatch(/^Una especie/);
  expect(r.listIntro(30, 12)).toMatch(/^30 especies .* de la A a la Z\.$/);
  const c = (score: number) => ({ species_id: score, score, fits: [] }) as never;
  expect(r.cutNote([c(3), c(2)], c(1), 9)).toBe('Se muestran 2 de 9. Todas las que siguen tienen menos confirmado.');
});
