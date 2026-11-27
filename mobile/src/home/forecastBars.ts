import { ForecastDay, FrostRisk } from '../types/site';
import { forecastCells } from '../season/sections';
import { parseServerDate } from '../api/serverDate';
import { t } from '../i18n';
import { formatDegrees, formatTemp, unitSymbol } from '../units/temperature';
import { weekdayShort } from '../season/dateWords';

// The forecast as bars (map and visuals spec sections 1 and 4.2): one
// high-to-low bar per day on a scale shared by every day, a line at 32 °F when
// that falls inside the scale (otherwise a note saying so), frost nights
// marked, and a weather icon per day. The spoken sentence for each day is the
// one the text strip already used. Pure: no React Native imports.

export const FREEZING_F = 32;

/** The label on the freezing line: "32 °F" or "0 °C". */
export function freezingLabel(): string {
  return formatTemp(FREEZING_F);
}

/** The caption under the chart: the per-bar labels are bare degrees, so the
 *  unit is said once here, with what the percentages are when shown. */
export function forecastCaption(anyRain: boolean): string {
  return anyRain ? t('home.bars.captionRain', { unit: unitSymbol() }) : t('home.bars.caption', { unit: unitSymbol() });
}

/** What a day with neither temperature shows in its column (short words, so
 *  they wrap at the space in a narrow column and never inside a word). */
export const NO_TEMPERATURE_TEXT = t('home.bars.notKnown');

/** The chart's fixed parts, in view pixels: the day name and icon above the
 *  bars, and the rain line under them. */
export const FORECAST_HEAD = 40;
export const FORECAST_RAIN_ROW = 16;

/**
 * The height the chart takes, known before its width is measured, so the
 * space is reserved on first paint and the notes under it do not jump.
 */
export function forecastChartHeight(barsHeight: number, anyRain: boolean): number {
  return FORECAST_HEAD + barsHeight + (anyRain ? FORECAST_RAIN_ROW : 0);
}

/** Font sizes of the chart's labels, and a safe average character width as
 *  a share of the font size, to check that labels fit their columns. */
export const CHART_TEXT = { day: 11.5, temp: 11, rain: 11, none: 10, charWidth: 0.62 } as const;

/** A day's name over its bar: "Today", then the short weekday for every
 *  other day (tomorrow too: "Tomorrow" does not fit a narrow column). The
 *  spoken sentence keeps saying "Tomorrow". */
export function chartDayLabel(dateStr: string, today: Date = new Date()): string {
  const d = parseServerDate(dateStr);
  if (!d) return dateStr;
  const t0 = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  const diff = Math.round((d.getTime() - t0.getTime()) / 86_400_000);
  return diff === 0 ? t('season.dates.today') : weekdayShort(d);
}

/** MaterialCommunityIcons names, all in the bundled icon font. */
export type WeatherIcon =
  | 'weather-sunny' | 'weather-partly-cloudy' | 'weather-cloudy' | 'weather-fog'
  | 'weather-windy' | 'weather-partly-rainy' | 'weather-rainy' | 'weather-pouring'
  | 'weather-lightning' | 'weather-lightning-rainy' | 'weather-snowy' | 'weather-snowy-rainy'
  | 'weather-hail';

export interface BarsBox {
  /** Drawing width and height in view pixels. */
  width: number;
  height: number;
  /** Room above the bars (the high's label) and below (the low's label). */
  padTop?: number;
  padBottom?: number;
  /** Space between neighbouring days' bars, as a share of a day's column. */
  gapShare?: number;
}

export interface DayBar {
  date: string;
  /** "Today", then "Tue", "Wed" (see chartDayLabel). */
  day: string;
  /** The day's column: left edge and width; `cx` its middle. */
  x: number;
  columnWidth: number;
  cx: number;
  /** The bar's own width (narrower than the column). */
  barWidth: number;
  high: number | null;
  low: number | null;
  /** Where the high and low sit, or null when that temperature is missing. */
  yHigh: number | null;
  yLow: number | null;
  /** `range`: both known, draw a bar. `high`/`low`: one known, draw a dot.
   *  `none`: neither known, draw nothing but the day. */
  shape: 'range' | 'high' | 'low' | 'none';
  /** "54°", or null (the caption says the degrees are °F). */
  highText: string | null;
  lowText: string | null;
  /** "40% rain", or null. */
  rainText: string | null;
  frost: FrostRisk;
  /** Whether to mark the night as frost (any risk but none). */
  frostMark: boolean;
  icon: WeatherIcon;
  /** The day as one sentence for a screen reader. */
  a11y: string;
}

export interface ForecastBarsLayout {
  /** The shared scale in °F, or null when no day has a temperature. */
  scale: { min: number; max: number } | null;
  days: DayBar[];
  /** Where the 32 °F line sits, or null when it is outside the scale. */
  freezingY: number | null;
  /** Said when the 32 °F line is not drawn, or null. */
  freezingNote: string | null;
  /** Lines across the chart every 10 °F (or 5 °F on a narrow scale). */
  ticks: Array<{ value: number; y: number }>;
}

const deg = (n: number | null) => (n == null ? null : formatDegrees(n));

const has = (s: string, ...words: string[]) => words.some((w) => s.includes(w));

/** The icon for a day: its summary first, then the chance of rain. */
export function weatherIcon(summary: string | null | undefined, precipitationChance?: number | null): WeatherIcon {
  const s = (summary ?? '').toLowerCase();
  const chance = precipitationChance ?? null;
  if (has(s, 'thunder', 't-storm', 'tstorm', 'lightning')) return has(s, 'rain', 'shower', 'storm') ? 'weather-lightning-rainy' : 'weather-lightning';
  if (has(s, 'hail')) return 'weather-hail';
  if (has(s, 'sleet', 'freezing rain', 'freezing drizzle', 'wintry mix', 'ice pellets', 'rain and snow', 'snow and rain')) return 'weather-snowy-rainy';
  if (has(s, 'snow', 'flurr', 'blizzard')) return 'weather-snowy';
  if (has(s, 'heavy rain', 'downpour', 'torrential')) return 'weather-pouring';
  if (has(s, 'rain', 'shower', 'drizzle')) {
    return has(s, 'slight chance', 'chance', 'isolated', 'scattered', 'partly') && (chance == null || chance < 60)
      ? 'weather-partly-rainy' : 'weather-rainy';
  }
  if (chance != null && chance >= 60) return 'weather-rainy';
  if (has(s, 'fog', 'mist', 'haze', 'smoke')) return 'weather-fog';
  if (has(s, 'wind', 'breez', 'gust', 'blustery')) return 'weather-windy';
  if (chance != null && chance >= 30) return 'weather-partly-rainy';
  if (has(s, 'partly', 'mostly sunny', 'mostly clear', 'few clouds', 'some clouds', 'intervals')) return 'weather-partly-cloudy';
  if (has(s, 'cloud', 'overcast', 'gray', 'grey', 'dull')) return 'weather-cloudy';
  if (has(s, 'sun', 'clear', 'fair', 'bright')) return 'weather-sunny';
  return 'weather-partly-cloudy';
}

function finite(n: number | null | undefined): number | null {
  return typeof n === 'number' && Number.isFinite(n) ? n : null;
}

/**
 * The bars for a forecast, in a box `width` by `height`. The scale is shared
 * by every day and rounded out to 5°F, at least 10°F tall. A day missing its
 * high or low draws what is known; a high below its low (it happens when
 * the provider's day and night do not line up) is drawn as the range between
 * them. The 32°F line is drawn only when it falls inside the scale.
 */
export function forecastBars(days: ForecastDay[], box: BarsBox, today: Date = new Date()): ForecastBarsLayout {
  const padTop = box.padTop ?? 16;
  const padBottom = box.padBottom ?? 16;
  const gapShare = box.gapShare ?? 0.55;
  const cells = forecastCells(days, today);
  const temps = days.flatMap((d) => [finite(d.high_f), finite(d.low_f)]).filter((t): t is number => t != null);

  let scale: { min: number; max: number } | null = null;
  if (temps.length > 0) {
    let min = Math.floor(Math.min(...temps) / 5) * 5;
    let max = Math.ceil(Math.max(...temps) / 5) * 5;
    if (max - min < 10) {
      const mid = (min + max) / 2;
      min = Math.floor((mid - 5) / 5) * 5;
      max = min + 10;
    }
    scale = { min, max };
  }

  const plotTop = padTop;
  const plotHeight = Math.max(1, box.height - padTop - padBottom);
  const yOf = (t: number) => (scale ? plotTop + ((scale.max - t) / (scale.max - scale.min)) * plotHeight : 0);

  const n = Math.max(days.length, 1);
  const columnWidth = box.width / n;
  const barWidth = Math.max(4, Math.min(18, columnWidth * (1 - gapShare)));

  const out: DayBar[] = days.map((d, i) => {
    let high = finite(d.high_f);
    let low = finite(d.low_f);
    if (high != null && low != null && high < low) [high, low] = [low, high];
    const shape: DayBar['shape'] = high != null && low != null ? 'range' : high != null ? 'high' : low != null ? 'low' : 'none';
    const x = i * columnWidth;
    return {
      date: d.date,
      day: chartDayLabel(d.date, today),
      x,
      columnWidth,
      cx: x + columnWidth / 2,
      barWidth,
      high,
      low,
      yHigh: high == null ? null : yOf(high),
      yLow: low == null ? null : yOf(low),
      shape,
      highText: deg(high),
      lowText: deg(low),
      rainText: cells[i].rain,
      frost: d.frost_risk,
      frostMark: d.frost_risk != null && d.frost_risk !== 'none',
      icon: weatherIcon(d.summary, d.precipitation_chance),
      a11y: cells[i].a11y,
    };
  });

  let freezingY: number | null = null;
  let freezingNote: string | null = null;
  if (scale) {
    if (FREEZING_F >= scale.min && FREEZING_F <= scale.max) {
      freezingY = yOf(FREEZING_F);
    } else if (FREEZING_F < scale.min) {
      freezingNote = t('home.bars.aboveFreezing', { temp: freezingLabel() });
    } else {
      freezingNote = t('home.bars.belowFreezing', { temp: freezingLabel() });
    }
  }

  const ticks: Array<{ value: number; y: number }> = [];
  if (scale) {
    const step = scale.max - scale.min > 20 ? 10 : 5;
    for (let v = Math.ceil(scale.min / step) * step; v <= scale.max; v += step) ticks.push({ value: v, y: yOf(v) });
  }

  return { scale, days: out, freezingY, freezingNote, ticks };
}
