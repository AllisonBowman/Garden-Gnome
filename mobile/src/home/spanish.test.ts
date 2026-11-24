// Home, the forecast and the season in Spanish: a phone whose first language
// is Spanish gets these words (src/i18n). The English is pinned by the other
// tests in these folders, which run in English.

type G = { __TEST_LOCALES__?: string[] };

function inSpanish<T>(load: () => T): T {
  (globalThis as G).__TEST_LOCALES__ = ['es-MX'];
  let mod: T | undefined;
  jest.isolateModules(() => { mod = load(); });
  return mod!;
}

afterEach(() => { delete (globalThis as G).__TEST_LOCALES__; });

describe('in Spanish', () => {
  it('the headline speaks of frost, care and a quiet day', () => {
    const { pickHeadline } = inSpanish(() => require('./headline') as typeof import('./headline'));
    const today = new Date(2026, 10, 24); // a Tuesday
    expect(pickHeadline({ days: [], careDue: 0, openSeasonTasks: 0, today })).toBe('Hoy no hay nada pendiente.');
    expect(pickHeadline({ days: [], careDue: 3, openSeasonTasks: 0, today })).toBe('Vale la pena revisar 3 plantas.');
    expect(pickHeadline({ days: [], careDue: 1, openSeasonTasks: 0, today })).toBe('Vale la pena revisar 1 planta.');
    expect(pickHeadline({
      days: [{ date: '2026-11-26', low_f: 30 }], careDue: 0, openSeasonTasks: 1, today,
    })).toBe('Es posible que haya congelación el jueves en la noche. 1 cosa por hacer esta semana.');
    expect(pickHeadline({ days: [{ date: '2026-11-24', low_f: 35 }], careDue: 0, openSeasonTasks: 0, today }))
      .toBe('Es posible que haya helada esta noche.');
  });

  it('a growing space and the season use Spanish words and dates', () => {
    const { spaceLine } = inSpanish(() => require('./spaces') as typeof import('./spaces'));
    expect(spaceLine({ growing_area_id: 1, name: 'x', kind: 'space', vegetation_type: null, indoor: true, plant_count: 2 }))
      .toBe('2 plantas, en interiores');
    const sections = inSpanish(() => require('../season/sections') as typeof import('../season/sections'));
    expect(sections.shortDay(new Date(2026, 10, 17))).toBe('mar 17 nov');
    expect(sections.observedDayChoices(new Date(2026, 10, 17)).map((c) => c.label).slice(0, 3))
      .toEqual(['Hoy', 'Ayer', 'dom 15 nov']);
    expect(sections.forecastCredit('Servicio Meteorológico', new Date(2026, 10, 17, 14).toISOString()))
      .toBe('Pronóstico: Servicio Meteorológico, actualizado a las 2 p. m. del mar 17 nov.');
  });

  it('a local reminder is written in Spanish', () => {
    const { waterCheck } = inSpanish(() => require('../notifications/plan') as typeof import('../notifications/plan'));
    expect(waterCheck({ waterRegime: null, checkDepthCm: null })).toBe('Toca el suelo antes de regar.');
    const { conditionText } = inSpanish(() => require('../weather/translate') as typeof import('../weather/translate'));
    expect(conditionText('PartlyCloudy')).toBe('Parcialmente nublado');
  });
});
