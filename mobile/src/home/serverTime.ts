// "Tue 17 Nov, 2 pm" for a server timestamp, in the app's language.
import { parseServerDate } from '../api/serverDate';
import { clock, shortDay } from '../season/dateWords';
import { t } from '../i18n';

export function formatServerTime(iso: string): string | null {
  const d = parseServerDate(iso);
  return d ? t('home.almanac.dateTime', { day: shortDay(d), time: clock(d) }) : null;
}
