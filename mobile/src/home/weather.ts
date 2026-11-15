import { Weather } from '../types';
import { VitalCard, VitalCardKey } from '../types/site';
import { parseServerDate } from '../api/serverDate';
import { startOfDay } from '../care/schedule';
import { conditionText } from '../weather/translate';
import { dayWord, nextFrostNight, nightWord } from './headline';

// Home's weather vitals: today, the next frost or freeze risk, and rain.
// From the server's cards when it sends them; built from the older weather
// route when the feature is off. Pure.

/** The cards that are weather, in the order Home shows them. */
export const WEATHER_CARD_KEYS: VitalCardKey[] = ['weather_now', 'frost', 'rain', 'heat'];

export function weatherCards(cards: VitalCard[]): VitalCard[] {
  return WEATHER_CARD_KEYS
    .map((k) => cards.find((c) => c.key === k))
    .filter((c): c is VitalCard => c != null);
}

/** The season card, shown with "The season ahead" when the server sends one. */
export function seasonCard(cards: VitalCard[]): VitalCard | null {
  return cards.find((c) => c.key === 'season') ?? null;
}

const RAIN_LOOKAHEAD_DAYS = 3;

/**
 * Weather vitals from the older `/growing-areas/{id}/weather` answer, for a
 * server with the new routes off. `placeName` is the growing area the
 * forecast is for: every detail line says where the number comes from.
 */
export function legacyWeatherCards(
  weather: Weather, placeName: string, today: Date = new Date(),
): VitalCard[] {
  const cards: VitalCard[] = [];
  const where = `Forecast for ${placeName}.`;
  const start = startOfDay(today).getTime();
  const ahead = weather.daily
    .map((d) => ({ d, at: parseServerDate(d.date) }))
    .filter((x) => x.at != null && x.at.getTime() >= start)
    .sort((a, b) => a.at!.getTime() - b.at!.getTime());
  const first = ahead[0]?.d;

  const t = weather.current.temp_f;
  const cond = conditionText(weather.current.condition);
  if (t != null || cond) {
    const range = first && first.high_f != null && first.low_f != null
      ? ` High ${Math.round(first.high_f)}°F, low ${Math.round(first.low_f)}°F.` : '';
    cards.push({
      key: 'weather_now',
      title: 'Today',
      value_text: [t != null ? `${Math.round(t)}°F` : null, cond || null].filter(Boolean).join(', '),
      detail: `${where}${range}`,
      tone: 'ok',
    });
  }

  if (ahead.length > 0) {
    const frost = nextFrostNight(ahead.map(({ d }) => ({ date: d.date, low_f: d.low_f })), today);
    if (frost) {
      const day = ahead.find(({ at }) => at!.getTime() === frost.date.getTime())?.d;
      const low = day?.low_f != null ? ` Forecast low of ${Math.round(day.low_f)}°F.` : '';
      cards.push({
        key: 'frost',
        title: frost.risk === 'frost' ? 'Frost' : 'Freeze',
        value_text: `Possible ${nightWord(frost.date, today)}`,
        detail: `${where}${low} Tender plants outdoors may want covering or bringing in.`,
        tone: 'act',
      });
    } else {
      const lows = ahead.slice(0, 3).map(({ d }) => d.low_f).filter((v): v is number => v != null);
      if (lows.length > 0) {
        cards.push({
          key: 'frost',
          title: 'Frost',
          value_text: 'None in the next 3 days',
          detail: `${where} Lowest forecast low ${Math.round(Math.min(...lows))}°F.`,
          tone: 'ok',
        });
      }
    }

    const rain = ahead.slice(0, RAIN_LOOKAHEAD_DAYS)
      .filter(({ d }) => d.precip_chance_pct != null)
      .sort((a, b) => (b.d.precip_chance_pct ?? 0) - (a.d.precip_chance_pct ?? 0))[0];
    if (rain) {
      const pct = Math.round(rain.d.precip_chance_pct!);
      const when = dayWord(rain.at!, today);
      cards.push({
        key: 'rain',
        title: 'Rain',
        value_text: pct === 0 ? 'None in the forecast' : `${pct}% chance ${when}`,
        detail: `${where} The highest chance of rain in the next 3 days.`,
        tone: pct >= 60 ? 'watch' : 'ok',
      });
    }
  }
  return cards;
}
