import { legacyWeatherCards, seasonCard, weatherCards } from './weather';
import { Weather } from '../types';
import { VitalCard } from '../types/site';

const today = new Date(2026, 10, 15, 9, 0);
const day = (date: string, low: number | null, rain: number | null, high: number | null = 55) => ({
  date, high_f: high, low_f: low, precip_chance_pct: rain, uv_max: null, sunrise: null,
  sunset: null, daylight_hours: null, condition: null,
});
const weather = (daily: ReturnType<typeof day>[]): Weather => ({
  current: { temp_f: 47.6, humidity_pct: 60, uv_index: 1, condition: 'PartlyCloudy' },
  daily, attribution: { text: 'Weather', url: 'https://example.invalid' },
});

test('server cards: weather ones in order, season apart', () => {
  const c = (key: VitalCard['key']): VitalCard => ({ key, title: key, value_text: '', detail: '', tone: 'ok' });
  const cards = [c('sun'), c('rain'), c('season'), c('weather_now'), c('frost')];
  expect(weatherCards(cards).map((x) => x.key)).toEqual(['weather_now', 'frost', 'rain']);
  expect(seasonCard(cards)?.key).toBe('season');
});

test('the older weather route: today, a freeze, and rain, each saying where from', () => {
  const cards = legacyWeatherCards(weather([
    day('2026-11-15', 41, 10), day('2026-11-16', 30, 70), day('2026-11-17', 38, 20),
  ]), 'Back yard', today);
  expect(cards.map((c) => [c.key, c.value_text])).toEqual([
    ['weather_now', '48°F, Partly cloudy'],
    ['frost', 'Possible tomorrow night'],
    ['rain', '70% chance tomorrow'],
  ]);
  for (const c of cards) expect(c.detail).toMatch(/^Forecast for Back yard\./);
  expect(cards[1].detail).toContain('Forecast low of 30°F.');
  expect(cards[1].tone).toBe('act');
});

test('no frost says so with the lowest low, and no rain says so', () => {
  const cards = legacyWeatherCards(weather([
    day('2026-11-15', 45, 0), day('2026-11-16', 44, 0),
  ]), 'Patio', today);
  expect(cards.find((c) => c.key === 'frost')?.value_text).toBe('None in the next 3 days');
  expect(cards.find((c) => c.key === 'frost')?.detail).toContain('Lowest forecast low 44°F.');
  expect(cards.find((c) => c.key === 'rain')?.value_text).toBe('None in the forecast');
});

test('past days in the answer are not read as ahead', () => {
  const cards = legacyWeatherCards(weather([day('2026-11-14', 20, 90)]), 'Patio', today);
  expect(cards.map((c) => c.key)).toEqual(['weather_now']);
});
