// The care words in Spanish: a phone set to Spanish gets the care checks,
// the care facts and the load failures in Spanish, with the same structure.
import type { Species } from '../types';

afterEach(() => { delete (globalThis as { __TEST_LOCALES__?: string[] }).__TEST_LOCALES__; });

function inSpanish<T>(load: () => T): T {
  (globalThis as { __TEST_LOCALES__?: string[] }).__TEST_LOCALES__ = ['es-MX'];
  let mod: T | undefined;
  jest.isolateModules(() => { mod = load(); });
  return mod!;
}

test('a care check and its due label read in Spanish', () => {
  const labels = inSpanish(() => require('./labels') as typeof import('./labels'));
  expect(labels.careActionLabel('water', 'Ferny')).toBe('💧 Revisa a Ferny');
  expect(labels.CARE_PRESENTATION.repot.done).toBe('Trasplantada');
  expect(labels.careActionName('prune')).toBe('Poda');
  const schedule = inSpanish(() => require('./schedule') as typeof import('./schedule'));
  const task = { status: 'due', daysSinceLastCare: 3, daysUntilDue: 0 } as import('./schedule').CareTask;
  expect(schedule.careTaskDueLabel(task)).toBe('Última vez hace 3 días');
  expect(schedule.careTaskDueLabel({ ...task, daysSinceLastCare: 1 })).toBe('Última vez hace 1 día');
  expect(schedule.unreadLine(2)).toMatch(/^No se pudieron leer los registros de cuidados de 2 plantas/);
});

test('care facts are worded in Spanish, units and server text left alone', () => {
  const facts = inSpanish(() => require('./facts') as typeof import('./facts'));
  const rows = facts.careFactRows({
    id: 1, common_name: 'Fern', scientific_name: 'Nephrolepis exaltata',
    water_regime: 'keep_moist', water_check_depth_cm: 2.54,
    fertilize_active_months: [3, 4, 5, 6, 7, 8, 9, 10], fertilize_interval_days: 30,
    mature_height_in_min: 12, mature_height_in_max: 36,
  } as unknown as Species);
  const byKey = Object.fromEntries(rows.map((r) => [r.key, r]));
  expect(byKey.water.label).toBe('Riego');
  expect(byKey.water.value).toBe('Mantén el sustrato húmedo de manera uniforme; revisa a 1 pulgada de profundidad');
  expect(byKey.fertilize.value).toBe('Mar–oct; cada 30 días');
  expect(byKey.size.value).toBe('12 pulg-3 pies de alto');
  expect(facts.monthSpan([3, 9])).toBe('mar y sep');
  expect(facts.INFERRED_PILL).toBe('inferido del género');
});

test('a failed load says so in Spanish, naming what it could not load', () => {
  const lf = inSpanish(() => require('./loadFailed') as typeof import('./loadFailed'));
  expect(lf.loadFailedTitle('this plant')).toBe('No se pudo cargar esta planta');
  expect(lf.loadFailedTitle('plant')).toBe('No se pudo cargar esta planta');
  expect(lf.loadFailedTitle('the Almanac')).toBe('No se pudo cargar el Almanaque');
  expect(lf.LOAD_FAILED.action).toBe('Intentar de nuevo');
  expect(lf.loadFailedBody(null)).toMatch(/^PlantAdvocate no pudo conectarse/);
});
