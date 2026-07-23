// Pure forecast → reminder-nudge signal. No React/expo imports so it can be
// unit-tested directly. Deliberately conservative: it looks only a few days
// out and returns a small whole-day shift for WATERING, gated by the same
// physical exposure the advisor uses. Sheltered/indoor spots always yield 0.
import { Environment, Weather } from '../types';
import { WeatherSignal } from '../notifications/plan';

// How far ahead the reminder nudge reacts. Kept short so a distant day-5
// forecast can't move a reminder that's due tomorrow.
const LOOKAHEAD_DAYS = 3;
const RAIN_CHANCE_PCT = 60;
const HOT_HIGH_F = 90;

export function computeWeatherSignal(env: Environment, weather: Weather): WeatherSignal {
  const days = (weather.daily ?? []).slice(0, LOOKAHEAD_DAYS);
  const unsheltered = env.shelter === 'partial' || env.shelter === 'exposed';
  const outdoor = env.temp_exposure === 'outdoor';

  // Rain reaching an unsheltered plant → hold off; nature waters it. Rain wins
  // over heat: skipping a round is safer than risking an over-water.
  if (unsheltered && days.some((d) => (d.precip_chance_pct ?? 0) >= RAIN_CHANCE_PCT)) {
    return { waterShiftDays: 2 };
  }

  // Heat spike for an outdoor plant → water a touch sooner (dries out faster).
  if (outdoor && days.some((d) => (d.high_f ?? -Infinity) >= HOT_HIGH_F)) {
    return { waterShiftDays: -1 };
  }

  return { waterShiftDays: 0 };
}
