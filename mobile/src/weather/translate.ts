// Pure "outside → in here" translation of a forecast for a grow environment.
// No React/React-Native imports so it can be unit-tested directly (mirrors the
// backend advisor's weather nudges — kept deliberately conservative and
// display-only; the precise, species-aware timing lives in each plant's advice).
import { Environment, Weather } from '../types';

// WeatherKit reports camelCase condition codes (e.g. "MostlyCloudy"). Friendly
// text for the common ones; fall back to spacing the camelCase.
const CONDITION_LABEL: Record<string, string> = {
  Clear: 'Clear',
  MostlyClear: 'Mostly clear',
  PartlyCloudy: 'Partly cloudy',
  MostlyCloudy: 'Mostly cloudy',
  Cloudy: 'Cloudy',
  Rain: 'Rain',
  Drizzle: 'Drizzle',
  Showers: 'Showers',
  Thunderstorms: 'Thunderstorms',
  Snow: 'Snow',
  Windy: 'Windy',
  Haze: 'Haze',
  Foggy: 'Fog',
};

export function conditionText(code: string | null): string {
  if (!code) return '';
  return CONDITION_LABEL[code] ?? code.replace(/([a-z])([A-Z])/g, '$1 $2');
}

export function weekday(dateStr: string): string {
  // dateStr is a plain YYYY-MM-DD; parse as local noon to avoid TZ drift.
  const d = new Date(`${dateStr}T12:00:00`);
  if (Number.isNaN(d.getTime())) return dateStr;
  return d.toLocaleDateString(undefined, { weekday: 'short' });
}

// One plain sentence describing how much weather reaches this spot, from its
// own exposure characteristics.
export function exposureSummary(env: Environment): string {
  const sheltered = env.shelter === 'sheltered';
  const indoor = env.temp_exposure === 'indoor';
  if (sheltered && indoor) {
    return 'Sheltered and indoors — the forecast barely reaches your plants here. Treat weather as context, not a to-do.';
  }
  if (!sheltered && !indoor) {
    return 'Open to the sky and outdoors — plants here feel the full forecast.';
  }
  if (indoor) {
    return 'Some weather reaches this spot, but the temperature stays indoor-steady — mostly rain and light to think about, not cold.';
  }
  return 'Roofed but out in the open air — plants here feel the temperature swings, though rain mostly misses them.';
}

// Translated implications, each gated by the environment's physical exposure so
// a desk plant surfaces nothing beyond day-length. Thresholds mirror the
// backend's stub nudges (rain ≥60%, UV ≥8); heat/cold use generic outdoor
// bands here since the environment view has no single species.
export function translateWeather(env: Environment, weather: Weather): string[] {
  const lines: string[] = [];
  const days = weather.daily ?? [];
  const unsheltered = env.shelter === 'partial' || env.shelter === 'exposed';
  const outdoor = env.temp_exposure === 'outdoor';
  const openSun = unsheltered && env.sun_exposure !== 'shade';

  const today = days[0];
  if (today && today.daylight_hours != null) {
    lines.push(`☀️ ~${today.daylight_hours}h of daylight — the light budget outdoor plants get right now.`);
  }

  if (unsheltered) {
    const wet = days.find((d) => (d.precip_chance_pct ?? 0) >= 60);
    if (wet) {
      lines.push(`🌧️ Rain likely (${wet.precip_chance_pct}% ${weekday(wet.date)}) — the sky waters unsheltered plants here; you can skip a round.`);
    }
  }
  if (outdoor) {
    const hot = days.find((d) => (d.high_f ?? -999) >= 90);
    if (hot) {
      lines.push(`🔥 Hot stretch (high ${hot.high_f}°F ${weekday(hot.date)}) — plants here dry out faster; check soil sooner.`);
    }
    const cold = days.find((d) => (d.low_f ?? 999) <= 40);
    if (cold) {
      lines.push(`❄️ Cold night (low ${cold.low_f}°F ${weekday(cold.date)}) — tender plants here may want cover or a move inside.`);
    }
  }
  if (openSun) {
    const uvVals = [weather.current?.uv_index ?? -1, ...days.map((d) => d.uv_max ?? -1)];
    const peak = Math.max(...uvVals);
    if (peak >= 8) {
      lines.push(`😎 Very high UV (up to ${peak}) — even sun-lovers here can scorch at midday.`);
    }
  }
  return lines;
}
