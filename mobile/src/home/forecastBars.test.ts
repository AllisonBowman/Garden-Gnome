import {
  CHART_TEXT, FORECAST_HEAD, FORECAST_RAIN_ROW, NO_TEMPERATURE_TEXT, chartDayLabel, forecastBars, forecastCaption,
  forecastChartHeight, weatherIcon,
} from './forecastBars';
import { forecastCells } from '../season/sections';
import { ForecastDay } from '../types/site';

const today = new Date(2026, 10, 16); // Mon 16 Nov 2026
const day = (date: string, high: number | null, low: number | null, over: Partial<ForecastDay> = {}): ForecastDay => ({
  date, high_f: high, low_f: low, precipitation_chance: null, summary: 'Sunny', frost_risk: 'none', ...over,
});
const box = { width: 280, height: 120, padTop: 10, padBottom: 10 };

test('a shared scale rounded out to 5°F, one column per day', () => {
  const layout = forecastBars([day('2026-11-16', 52, 31), day('2026-11-17', 47, 36), day('2026-11-18', 58, 40)], box, today);
  expect(layout.scale).toEqual({ min: 30, max: 60 });
  expect(layout.days.map((d) => [d.day, d.x, d.columnWidth])).toEqual([
    ['Today', 0, 280 / 3], ['Tue', 280 / 3, 280 / 3], ['Wed', 560 / 3, 280 / 3],
  ]);
  const [d0] = layout.days;
  // 100 px of plot from y=10: 60°F at 10, 30°F at 110.
  expect(d0.yHigh).toBeCloseTo(10 + (8 / 30) * 100);
  expect(d0.yLow).toBeCloseTo(10 + (29 / 30) * 100);
  expect(d0.shape).toBe('range');
  expect(d0.highText).toBe('52°');
  expect(d0.lowText).toBe('31°');
  expect(d0.cx).toBeCloseTo(280 / 6);
  expect(d0.barWidth).toBeGreaterThanOrEqual(4);
  expect(d0.barWidth).toBeLessThanOrEqual(18);
});

test('the 32°F line sits inside the scale when it can', () => {
  const layout = forecastBars([day('2026-11-16', 40, 28)], box, today);
  expect(layout.scale).toEqual({ min: 25, max: 40 });
  expect(layout.freezingY).toBeCloseTo(10 + (8 / 15) * 100);
  expect(layout.freezingNote).toBeNull();
});

test('all days above freezing: no line, a note instead', () => {
  const layout = forecastBars([day('2026-11-16', 70, 50), day('2026-11-17', 75, 55)], box, today);
  expect(layout.freezingY).toBeNull();
  expect(layout.freezingNote).toBe('Every day in this forecast stays above freezing (32 °F).');
});

test('all days below freezing: no line, a note instead', () => {
  const layout = forecastBars([day('2026-11-16', 20, 5)], box, today);
  expect(layout.scale).toEqual({ min: 5, max: 20 });
  expect(layout.freezingY).toBeNull();
  expect(layout.freezingNote).toBe('Every day in this forecast stays below freezing (32 °F).');
});

test('a single day with equal high and low still gets a 10°F scale', () => {
  const layout = forecastBars([day('2026-11-16', 50, 50)], box, today);
  expect(layout.scale!.max - layout.scale!.min).toBe(10);
  expect(layout.days).toHaveLength(1);
  expect(layout.days[0].columnWidth).toBe(280);
  expect(layout.days[0].yHigh).toBe(layout.days[0].yLow);
});

test('a missing high or low draws what is known; neither draws nothing', () => {
  const layout = forecastBars([
    day('2026-11-16', null, 30), day('2026-11-17', 45, null), day('2026-11-18', null, null),
  ], box, today);
  expect(layout.days.map((d) => d.shape)).toEqual(['low', 'high', 'none']);
  expect(layout.days[0].yHigh).toBeNull();
  expect(layout.days[0].yLow).not.toBeNull();
  expect(layout.days[1].yLow).toBeNull();
  expect(layout.days[2].yHigh).toBeNull();
  expect(layout.scale).toEqual({ min: 30, max: 45 });
});

test('no temperatures at all: no scale, no line, no note, the days still listed', () => {
  const layout = forecastBars([day('2026-11-16', null, null)], box, today);
  expect(layout.scale).toBeNull();
  expect(layout.freezingY).toBeNull();
  expect(layout.freezingNote).toBeNull();
  expect(layout.ticks).toEqual([]);
  expect(layout.days[0].shape).toBe('none');
});

test('no days: an empty layout', () => {
  expect(forecastBars([], box, today)).toEqual({ scale: null, days: [], freezingY: null, freezingNote: null, ticks: [] });
});

test('a high below its low is drawn as the range between them', () => {
  const [d] = forecastBars([day('2026-11-16', 30, 40)], box, today).days;
  expect([d.high, d.low]).toEqual([40, 30]);
  expect(d.yHigh!).toBeLessThan(d.yLow!);
});

test('a temperature that is not a number counts as missing', () => {
  const [d] = forecastBars([day('2026-11-16', NaN, 40)], box, today).days;
  expect(d.shape).toBe('low');
});

test('frost nights are marked', () => {
  const layout = forecastBars([
    day('2026-11-16', 40, 30, { frost_risk: 'frost' }), day('2026-11-17', 35, 20, { frost_risk: 'hard_freeze' }),
    day('2026-11-18', 50, 40),
  ], box, today);
  expect(layout.days.map((d) => d.frostMark)).toEqual([true, true, false]);
  expect(layout.days[1].frost).toBe('hard_freeze');
});

test('ticks every 10°F on a wide scale and 5°F on a narrow one', () => {
  expect(forecastBars([day('2026-11-16', 60, 30)], box, today).ticks.map((t) => t.value)).toEqual([30, 40, 50, 60]);
  expect(forecastBars([day('2026-11-16', 45, 30)], box, today).ticks.map((t) => t.value)).toEqual([30, 35, 40, 45]);
});

test('each day speaks the same sentence as the text strip', () => {
  const days = [day('2026-11-16', 52, 31, { precipitation_chance: 40, frost_risk: 'frost', summary: 'Chance of showers' })];
  const [d] = forecastBars(days, box, today).days;
  expect(d.a11y).toBe(forecastCells(days, today)[0].a11y);
  expect(d.a11y).toContain('high 52 degrees Fahrenheit');
  expect(d.rainText).toBe('40% rain');
});

describe('weatherIcon', () => {
  test.each([
    ['Sunny', null, 'weather-sunny'],
    ['Clear', null, 'weather-sunny'],
    ['Mostly Sunny', null, 'weather-partly-cloudy'],
    ['Partly Cloudy', null, 'weather-partly-cloudy'],
    ['Cloudy', null, 'weather-cloudy'],
    ['Overcast', 10, 'weather-cloudy'],
    ['Patchy Fog', null, 'weather-fog'],
    ['Breezy', null, 'weather-windy'],
    ['Chance Rain Showers', 40, 'weather-partly-rainy'],
    ['Chance Rain Showers', 70, 'weather-rainy'],
    ['Rain', 90, 'weather-rainy'],
    ['Heavy Rain', 90, 'weather-pouring'],
    ['Showers And Thunderstorms', 60, 'weather-lightning-rainy'],
    ['Light Snow', 50, 'weather-snowy'],
    ['Rain And Snow', 60, 'weather-snowy-rainy'],
    ['Freezing Rain', 60, 'weather-snowy-rainy'],
    ['Hail', null, 'weather-hail'],
    ['Partly Cloudy', 35, 'weather-partly-rainy'],
    ['Sunny', 65, 'weather-rainy'],
    ['', null, 'weather-partly-cloudy'],
  ])('%s at %s%% is %s', (summary, chance, icon) => {
    expect(weatherIcon(summary, chance)).toBe(icon);
  });
  test('no summary at all', () => {
    expect(weatherIcon(undefined)).toBe('weather-partly-cloudy');
  });
});

describe('labels fit a phone', () => {
  // Seven days across a 313 pt chart (375 pt screen less the card's padding).
  const week = [
    day('2026-11-16', 58, 31, { precipitation_chance: 100 }), day('2026-11-17', 47, -12, { precipitation_chance: 40 }),
    day('2026-11-18', 102, 70), day('2026-11-19', null, null), day('2026-11-20', 45, 30),
    day('2026-11-21', 44, 29), day('2026-11-22', 43, 28),
  ];
  const layout = forecastBars(week, { width: 313, height: 120 }, today);
  const px = (text: string, size: number) => text.length * size * CHART_TEXT.charWidth;

  test('Today, then short weekday names, tomorrow included; nothing wider than its column', () => {
    expect(layout.days.map((d) => d.day)).toEqual(['Today', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']);
    for (const d of layout.days) {
      expect(d.day.length).toBeLessThanOrEqual(5);
      expect(px(d.day, CHART_TEXT.day)).toBeLessThanOrEqual(d.columnWidth);
      for (const t of [d.highText, d.lowText]) if (t) expect(px(t, CHART_TEXT.temp)).toBeLessThanOrEqual(d.columnWidth);
      if (d.rainText) expect(px(d.rainText.replace(' rain', ''), CHART_TEXT.rain)).toBeLessThanOrEqual(d.columnWidth);
    }
    for (const word of NO_TEMPERATURE_TEXT.split(' ')) {
      expect(px(word, CHART_TEXT.none)).toBeLessThanOrEqual(layout.days[0].columnWidth);
    }
  });

  test('the spoken sentence still says Tomorrow and degrees Fahrenheit', () => {
    expect(layout.days[1].a11y).toMatch(/^Tomorrow, high 47 degrees Fahrenheit/);
    expect(layout.days[1].highText).toBe('47°');
  });

  test('chartDayLabel', () => {
    expect(chartDayLabel('2026-11-16', today)).toBe('Today');
    expect(chartDayLabel('2026-11-17', today)).toBe('Tue');
    expect(chartDayLabel('not a date', today)).toBe('not a date');
  });
});

test('one caption says the unit once, and what the percentages are when shown', () => {
  expect(forecastCaption(true)).toBe('Highs and lows in °F. Percentages are the chance of rain.');
  expect(forecastCaption(false)).toBe('Highs and lows in °F.');
});

test('the chart height is known before its width is measured', () => {
  expect(forecastChartHeight(120, false)).toBe(FORECAST_HEAD + 120);
  expect(forecastChartHeight(120, true)).toBe(FORECAST_HEAD + 120 + FORECAST_RAIN_ROW);
});
