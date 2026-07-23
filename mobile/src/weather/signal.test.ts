import { computeWeatherSignal } from './signal';
import { Environment, Weather, WeatherDay } from '../types';

function makeEnv(partial: Partial<Environment> = {}): Environment {
  return {
    id: 1, uuid: 'u', name: 'Balcony', type: 'community_garden',
    city: '', region: '', country: '',
    shelter: 'exposed', temp_exposure: 'outdoor', sun_exposure: 'full_sun',
    created_at: '2026-07-23T00:00:00Z', plant_count: 1, ...partial,
  };
}

function day(partial: Partial<WeatherDay> = {}): WeatherDay {
  return {
    date: '2026-07-24', high_f: 78, low_f: 60, precip_chance_pct: 0, uv_max: 5,
    sunrise: null, sunset: null, daylight_hours: 14, condition: 'Clear', ...partial,
  };
}

function makeWeather(days: WeatherDay[]): Weather {
  return {
    current: { temp_f: 75, humidity_pct: 40, uv_index: 5, condition: 'Clear' },
    daily: days,
    attribution: { text: ' Weather', url: 'x' },
  };
}

test('rain on an unsheltered plant delays watering (+2)', () => {
  const w = makeWeather([day({ precip_chance_pct: 70 })]);
  expect(computeWeatherSignal(makeEnv(), w).waterShiftDays).toBe(2);
});

test('heat on an outdoor plant advances watering (-1)', () => {
  const w = makeWeather([day({ high_f: 96 })]);
  expect(computeWeatherSignal(makeEnv(), w).waterShiftDays).toBe(-1);
});

test('rain wins over heat when both are forecast', () => {
  const w = makeWeather([day({ precip_chance_pct: 80, high_f: 98 })]);
  expect(computeWeatherSignal(makeEnv(), w).waterShiftDays).toBe(2);
});

test('sheltered indoor plant is never shifted', () => {
  const w = makeWeather([day({ precip_chance_pct: 100, high_f: 110 })]);
  const env = makeEnv({ shelter: 'sheltered', temp_exposure: 'indoor' });
  expect(computeWeatherSignal(env, w).waterShiftDays).toBe(0);
});

test('rain beyond the 3-day lookahead does not shift', () => {
  const w = makeWeather([
    day({ date: '2026-07-24', precip_chance_pct: 0 }),
    day({ date: '2026-07-25', precip_chance_pct: 0 }),
    day({ date: '2026-07-26', precip_chance_pct: 0 }),
    day({ date: '2026-07-27', precip_chance_pct: 90 }), // day 4 — ignored
  ]);
  expect(computeWeatherSignal(makeEnv(), w).waterShiftDays).toBe(0);
});

test('roofed-but-outdoor gets heat but not rain', () => {
  const env = makeEnv({ shelter: 'sheltered', temp_exposure: 'outdoor' });
  expect(computeWeatherSignal(env, makeWeather([day({ precip_chance_pct: 90 })])).waterShiftDays).toBe(0);
  expect(computeWeatherSignal(env, makeWeather([day({ high_f: 95 })])).waterShiftDays).toBe(-1);
});

test('empty forecast yields no shift', () => {
  expect(computeWeatherSignal(makeEnv(), makeWeather([])).waterShiftDays).toBe(0);
});
