// Calendar words in the app's language, for the Home, Season and forecast
// code that writes its own dates (it predates Intl on the phone and its
// English format is pinned by tests). Pure apart from reading `t`.
import { t } from '../i18n';

const list = (s: string) => s.split(',');

export const weekdayShort = (d: Date): string => list(t('season.dates.weekdaysShort'))[d.getDay()];
export const weekdayLong = (d: Date): string => list(t('season.dates.weekdaysLong'))[d.getDay()];
export const monthShort = (d: Date): string => list(t('season.dates.monthsShort'))[d.getMonth()];
export const monthLong = (d: Date): string => list(t('season.dates.monthsLong'))[d.getMonth()];

/** "2 pm", "2:30 pm" (Spanish: "2 p. m."). */
export function clock(d: Date): string {
  const h = d.getHours();
  const m = d.getMinutes();
  const hour = String(h % 12 === 0 ? 12 : h % 12);
  const ampm = h < 12 ? t('season.dates.am') : t('season.dates.pm');
  return m === 0
    ? t('season.dates.clockHour', { hour, ampm })
    : t('season.dates.clockMinute', { hour, minute: String(m).padStart(2, '0'), ampm });
}

/** "Tue 17 Nov" */
export function shortDay(d: Date): string {
  return t('season.dates.shortDay', { weekday: weekdayShort(d), day: d.getDate(), month: monthShort(d) });
}

/** "12 November" */
export function spokenDay(d: Date): string {
  return t('season.dates.spokenDay', { day: d.getDate(), month: monthLong(d) });
}
