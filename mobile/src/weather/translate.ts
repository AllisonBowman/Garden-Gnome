// Pure "outside → in here" translation of a forecast for a growing area.
// No React/React-Native imports so it can be unit-tested directly (mirrors the
// backend advisor's weather nudges — kept deliberately conservative and
// display-only; the precise, species-aware timing lives in each plant's advice).
import { GrowingArea, Weather } from '../types';
import { parseServerDate } from '../api/serverDate';
import { language, localeTag, t } from '../i18n';

// WeatherKit reports camelCase condition codes (e.g. "MostlyCloudy"). Friendly
// text for the common ones (i18n weather.conditions); fall back to spacing the
// camelCase, in English, for the rest.
const KNOWN_CONDITIONS = [
  'Clear', 'MostlyClear', 'PartlyCloudy', 'MostlyCloudy', 'Cloudy', 'Rain', 'Drizzle',
  'Showers', 'Thunderstorms', 'Snow', 'Windy', 'Haze', 'Foggy',
] as const;
type KnownCondition = (typeof KNOWN_CONDITIONS)[number];
const isKnown = (code: string): code is KnownCondition => (KNOWN_CONDITIONS as readonly string[]).includes(code);

export function conditionText(code: string | null): string {
  if (!code) return '';
  return isKnown(code) ? t(`weather.conditions.${code}`) : code.replace(/([a-z])([A-Z])/g, '$1 $2');
}

export function weekday(dateStr: string): string {
  // dateStr is a plain YYYY-MM-DD: a day on the caretaker's calendar.
  const d = parseServerDate(dateStr);
  if (!d) return dateStr;
  // Spanish says the whole name: the short "mar" would read as "the sea".
  return d.toLocaleDateString(localeTag, { weekday: language === 'es' ? 'long' : 'short' });
}

// One plain sentence describing how much weather reaches this spot, from its
// own exposure characteristics.
export function exposureSummary(env: GrowingArea): string {
  const sheltered = env.shelter === 'sheltered';
  const indoor = env.temp_exposure === 'indoor';
  if (sheltered && indoor) {
    return t('weather.exposure.shelteredIndoor');
  }
  // A covered porch or balcony is not open sky: the server's own reading of
  // "partial" is some rain and wind, never the full forecast.
  if (env.shelter === 'partial' && !indoor) {
    return t('weather.exposure.partial');
  }
  if (!sheltered && !indoor) {
    return t('weather.exposure.open');
  }
  if (indoor) {
    return t('weather.exposure.indoorSome');
  }
  return t('weather.exposure.roofed');
}

// Translated implications, each gated by the growing area's physical exposure so
// a desk plant surfaces nothing beyond day-length. Thresholds mirror the
// backend's stub nudges (rain ≥60%, UV ≥8); heat/cold use generic outdoor
// bands here since the growing area view has no single species.
export function translateWeather(env: GrowingArea, weather: Weather): string[] {
  const lines: string[] = [];
  const days = weather.daily ?? [];
  const unsheltered = env.shelter === 'partial' || env.shelter === 'exposed';
  const outdoor = env.temp_exposure === 'outdoor';
  const openSun = unsheltered && env.sun_exposure !== 'shade';

  const today = days[0];
  if (today && today.daylight_hours != null) {
    lines.push(t('weather.lines.daylight', { hours: today.daylight_hours }));
  }

  if (unsheltered) {
    // A chance of rain is not a watering, so it never becomes "skip a round":
    // the soil after the rain decides. Under partial cover only some of it
    // arrives at all.
    const wet = days.find((d) => (d.precip_chance_pct ?? 0) >= 60);
    if (wet) {
      const reach = env.shelter === 'partial'
        ? t('weather.lines.reachPartial')
        : t('weather.lines.reachOpen');
      lines.push(t('weather.lines.rainLikely', { pct: wet.precip_chance_pct, day: weekday(wet.date), reach }));
    }
  }
  if (outdoor) {
    const hot = days.find((d) => (d.high_f ?? -999) >= 90);
    if (hot) {
      lines.push(t('weather.lines.hot', { high: hot.high_f, day: weekday(hot.date) }));
    }
    const cold = days.find((d) => (d.low_f ?? 999) <= 40);
    if (cold) {
      lines.push(t('weather.lines.cold', { low: cold.low_f, day: weekday(cold.date) }));
    }
  }
  if (openSun) {
    const uvVals = [weather.current?.uv_index ?? -1, ...days.map((d) => d.uv_max ?? -1)];
    const peak = Math.max(...uvVals);
    if (peak >= 8) {
      lines.push(t('weather.lines.uv', { peak }));
    }
  }
  return lines;
}
