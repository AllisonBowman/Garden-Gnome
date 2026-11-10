// Dates as the server sends them, read the way a caretaker means them.
//
// A date-only field ('YYYY-MM-DD', such as a plant's acquired_on or a
// forecast day) names a day on the caretaker's calendar, not an instant. The
// JavaScript parser reads `new Date('2026-07-08')` as midnight UTC, which is
// the evening of July 7 anywhere west of UTC: a plant added on a New York
// morning came due a day early, in the to-do list and in its first reminder.
// So every date-only string from the server is read here, as a LOCAL date.
//
// Pure on purpose (no React Native imports) so jest can pin it.

const DATE_ONLY = /^(\d{4})-(\d{2})-(\d{2})$/;

/**
 * A server date as a Date: 'YYYY-MM-DD' is local midnight of that day; a
 * full timestamp ('2026-07-08T14:00:00Z') is the instant it names. Null for
 * anything that isn't a date at all, so a caller falls back on purpose
 * rather than doing arithmetic on NaN.
 */
export function parseServerDate(value: string | null | undefined): Date | null {
  if (!value) return null;
  const m = DATE_ONLY.exec(value);
  if (m) {
    const [y, mo, d] = [Number(m[1]), Number(m[2]), Number(m[3])];
    const local = new Date(y, mo - 1, d);
    // Reject a day that doesn't exist ('2026-02-30' would roll into March).
    if (local.getFullYear() !== y || local.getMonth() !== mo - 1 || local.getDate() !== d) {
      return null;
    }
    return local;
  }
  const instant = new Date(value);
  return Number.isNaN(instant.getTime()) ? null : instant;
}

/** Today (or `d`) on this phone's calendar, as the server writes a date:
 *  'YYYY-MM-DD'. What a new plant is sent as its acquired_on, so the day it
 *  was added is the caretaker's day rather than the server's. */
export function localDateString(d: Date = new Date()): string {
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  return `${d.getFullYear()}-${mm}-${dd}`;
}
