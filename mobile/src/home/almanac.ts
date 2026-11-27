// The almanac line at the top of Home: the date, the week of the season,
// and the one thing that matters this week. Pure and dated by `today`.
//
// Seasons are the calendar's (meteorological) seasons, said plainly in the
// How we know sheet: spring from March 1, summer from June 1, fall from
// September 1, winter from December 1. The app's maps cover the United
// States, so the northern hemisphere's seasons are the right ones.
import { t } from '../i18n';
import { monthLong, weekdayLong } from '../season/dateWords';

export type SeasonName = 'spring' | 'summer' | 'fall' | 'winter';

export function seasonOf(today: Date): { season: SeasonName; start: Date } {
  const y = today.getFullYear();
  const m = today.getMonth(); // 0 = January
  if (m >= 2 && m <= 4) return { season: 'spring', start: new Date(y, 2, 1) };
  if (m >= 5 && m <= 7) return { season: 'summer', start: new Date(y, 5, 1) };
  if (m >= 8 && m <= 10) return { season: 'fall', start: new Date(y, 8, 1) };
  // December starts this year's winter; January and February belong to the
  // winter that began last December.
  return { season: 'winter', start: new Date(m === 11 ? y : y - 1, 11, 1) };
}

/** 1 for the season's first seven days. */
export function weekOfSeason(today: Date): number {
  const { start } = seasonOf(today);
  const day = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  const days = Math.round((day.getTime() - start.getTime()) / 86_400_000);
  return Math.floor(days / 7) + 1;
}

/** "Week 13 of fall". */
export function seasonWeekLine(today: Date): string {
  return t(`home.almanac.week.${seasonOf(today).season}`, { week: weekOfSeason(today) });
}

/** "Tuesday, November 24", in the app's language (the app's own calendar
 *  words, as the season screen uses). */
export function almanacDate(today: Date): string {
  const s = t('home.almanac.date', { weekday: weekdayLong(today), month: monthLong(today), day: today.getDate() });
  // A heading starts with a capital in either language ("Martes 24 de noviembre").
  return s.charAt(0).toUpperCase() + s.slice(1);
}

/**
 * The one thing that matters: the first sentence of the headline. The rest
 * of a long server headline moves to the How we know sheet. When the
 * person reads °C and that sentence quotes a °F reading, the phone's own
 * headline (which quotes no temperature) speaks instead.
 */
export function oneThing(serverHeadline: string | null | undefined, localHeadline: string, celsius: boolean): {
  line: string; fromServer: boolean; full: string | null;
} {
  const full = serverHeadline?.trim() || null;
  if (!full) return { line: firstSentence(localHeadline), fromServer: false, full: null };
  const first = firstSentence(full);
  if (celsius && /°\s?F/.test(first)) return { line: firstSentence(localHeadline), fromServer: false, full };
  return { line: first, fromServer: true, full };
}

export function firstSentence(s: string): string {
  const trimmed = s.trim();
  // A full stop after a digit is a decimal point, not a sentence end.
  const m = trimmed.match(/^.*?[^\d][.!?](?=\s|$)/);
  return m ? m[0] : trimmed;
}
