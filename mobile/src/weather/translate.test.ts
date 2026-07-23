import {
  conditionText, weekday, exposureSummary, translateWeather,
} from './translate';
import { Environment, Weather, WeatherDay } from '../types';

function makeEnv(partial: Partial<Environment> = {}): Environment {
  return {
    id: 1,
    uuid: 'u',
    name: 'Balcony',
    type: 'community_garden',
    city: 'Denver',
    region: 'CO',
    country: 'US',
    shelter: 'exposed',
    temp_exposure: 'outdoor',
    sun_exposure: 'full_sun',
    created_at: '2026-07-23T00:00:00Z',
    plant_count: 3,
    ...partial,
  };
}

function day(partial: Partial<WeatherDay> = {}): WeatherDay {
  return {
    date: '2026-07-24',
    high_f: 80,
    low_f: 60,
    precip_chance_pct: 0,
    uv_max: 5,
    sunrise: null,
    sunset: null,
    daylight_hours: 14.2,
    condition: 'Clear',
    ...partial,
  };
}

function makeWeather(days: WeatherDay[], uvNow = 6): Weather {
  return {
    current: { temp_f: 78, humidity_pct: 45, uv_index: uvNow, condition: 'Clear' },
    daily: days,
    attribution: { text: ' Weather', url: 'https://example/legal' },
  };
}

// --- conditionText ----------------------------------------------------------

test('conditionText maps known codes and spaces unknown camelCase', () => {
  expect(conditionText('MostlyCloudy')).toBe('Mostly cloudy');
  expect(conditionText('Clear')).toBe('Clear');
  expect(conditionText('BlowingDust')).toBe('Blowing Dust'); // not in map → spaced
  expect(conditionText(null)).toBe('');
});

// --- weekday -----------------------------------------------------------------

test('weekday returns a short weekday and passes through bad input', () => {
  const DOW = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  expect(DOW).toContain(weekday('2026-07-24'));
  expect(weekday('not-a-date')).toBe('not-a-date');
});

// --- exposureSummary ---------------------------------------------------------

test('exposureSummary distinguishes the four exposure combos', () => {
  expect(exposureSummary(makeEnv({ shelter: 'sheltered', temp_exposure: 'indoor' })))
    .toMatch(/barely reaches/i);
  expect(exposureSummary(makeEnv({ shelter: 'exposed', temp_exposure: 'outdoor' })))
    .toMatch(/full forecast/i);
  expect(exposureSummary(makeEnv({ shelter: 'partial', temp_exposure: 'indoor' })))
    .toMatch(/indoor-steady/i);
  expect(exposureSummary(makeEnv({ shelter: 'sheltered', temp_exposure: 'outdoor' })))
    .toMatch(/temperature swings/i);
});

// --- translateWeather --------------------------------------------------------

test('exposed/outdoor/full-sun surfaces rain, heat and UV plus day-length', () => {
  const w = makeWeather([
    day({ date: '2026-07-24', high_f: 95, low_f: 70, precip_chance_pct: 70, uv_max: 9 }),
  ]);
  const lines = translateWeather(makeEnv(), w).join('\n');
  expect(lines).toMatch(/daylight/);
  expect(lines).toMatch(/Rain likely \(70%/);
  expect(lines).toMatch(/Hot stretch \(high 95/);
  expect(lines).toMatch(/Very high UV \(up to 9/);
});

test('indoor + sheltered surfaces only the day-length line', () => {
  const w = makeWeather([
    day({ high_f: 110, low_f: 20, precip_chance_pct: 100, uv_max: 11 }),
  ]);
  const lines = translateWeather(
    makeEnv({ shelter: 'sheltered', temp_exposure: 'indoor', sun_exposure: 'shade' }), w);
  expect(lines).toHaveLength(1);
  expect(lines[0]).toMatch(/daylight/);
});

test('roofed-but-outdoor feels heat, not rain', () => {
  const w = makeWeather([
    day({ high_f: 95, low_f: 70, precip_chance_pct: 90, uv_max: 6 }),
  ]);
  const lines = translateWeather(
    makeEnv({ shelter: 'sheltered', temp_exposure: 'outdoor' }), w).join('\n');
  expect(lines).toMatch(/Hot stretch/);
  expect(lines).not.toMatch(/Rain likely/);
});

test('no forecast days yields no lines', () => {
  expect(translateWeather(makeEnv(), makeWeather([]))).toEqual([]);
});
