import { SeasonAlert, SeasonEvent, SeasonEventType, SeasonalPlan } from '../types/site';
import { sourceText } from '../components/explainedText';

// The seasonal plan's alerts, turned into on-device notifications. Pure: the
// one planner (notifications/plan.ts) takes what this returns as an input to
// the same planning pass as care reminders, so the full cancel-and-replace in
// reminders.ts rebuilds them every time (PLAN.md decision D21, section 7).
//
// The rules are PLAN.md section 7, "Notifications alongside reminders.ts":
// nothing between 21:00 and 08:00, at most one a day and three a week, a
// freeze alert replaces a frost alert for the same night, a small fixed share
// of the 64 pending notifications iOS allows, and every body ends with the
// time of the forecast it was built from.

/** Earliest hour an alert may arrive, and the hour after which it may not. */
export const QUIET_END_HOUR = 8;
export const QUIET_START_HOUR = 21;

export const MAX_ALERTS_PER_DAY = 1;
export const MAX_ALERTS_PER_WEEK = 3;

/** The share of the pending-notification budget kept for seasonal alerts. */
export const SEASONAL_RESERVE = 6;

/** How far ahead a seasonal alert is scheduled. An alert further out than
 *  this would be built from a forecast too old to trust when it fires. */
export const SEASONAL_HORIZON_DAYS = 10;

export interface SeasonalNotice {
  /** The notification identifier: the server's alert key, so a reschedule
   *  replaces rather than doubles it. */
  identifier: string;
  alertKey: string;
  eventKey: string;
  date: Date;
  title: string;
  body: string;
  builtFromForecastAt: string;
}

/** A plan's alerts with what the planner needs from its events. */
export interface SeasonalInput {
  alerts: SeasonAlert[];
  /** The plan's events, so an alert can name its source and its severity. */
  events?: Pick<SeasonEvent, 'event_key' | 'type' | 'explained'>[];
}

export function seasonalInputFromPlan(plan: SeasonalPlan): SeasonalInput {
  return { alerts: plan.alerts, events: plan.events };
}

// A freeze outranks a frost on the same night; the rest come after.
const SEVERITY: Partial<Record<SeasonEventType, number>> = {
  hard_freeze: 3, first_freeze: 2, first_frost: 1,
};

function severity(type: SeasonEventType | undefined): number {
  return type ? SEVERITY[type] ?? 0 : 0;
}

/** Move a time out of quiet hours: 21:00 or later goes to 08:00 next day,
 *  before 08:00 goes to 08:00 the same day. */
export function outOfQuietHours(at: Date): Date {
  const d = new Date(at);
  if (d.getHours() >= QUIET_START_HOUR) {
    d.setDate(d.getDate() + 1);
    d.setHours(QUIET_END_HOUR, 0, 0, 0);
  } else if (d.getHours() < QUIET_END_HOUR) {
    d.setHours(QUIET_END_HOUR, 0, 0, 0);
  }
  return d;
}

function dayKey(d: Date): string {
  return `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`;
}

const WEEKDAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
  'August', 'September', 'October', 'November', 'December'];

function clock(d: Date): string {
  const h = d.getHours();
  const m = d.getMinutes();
  const hour12 = h % 12 === 0 ? 12 : h % 12;
  const ampm = h < 12 ? 'am' : 'pm';
  return m === 0 ? `${hour12} ${ampm}` : `${hour12}:${String(m).padStart(2, '0')} ${ampm}`;
}

/**
 * "Forecast as of 2 pm on Tuesday 17 November." The day is always written
 * out, because the notification may be read days after it was built, when
 * "today" would be wrong.
 */
export function forecastAsOfLine(iso: string): string | null {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return null;
  return `Forecast as of ${clock(d)} on ${WEEKDAYS[d.getDay()]} ${d.getDate()} ${MONTHS[d.getMonth()]}.`;
}

/** The body as sent, with its data source when the server did not already
 *  name it, ending with the forecast time. */
export function alertBody(
  alert: SeasonAlert, event?: Pick<SeasonEvent, 'explained'>,
): string {
  let body = alert.body.trim();
  const source = event?.explained.sources[0];
  if (source && !body.includes(source.name)) {
    const line = sourceText(source);
    body = `${body}${body && !/[.!?]$/.test(body) ? '.' : ''} Data: ${line}.`;
  }
  const asOf = forecastAsOfLine(alert.built_from_forecast_at);
  if (asOf && !body.includes('Forecast as of')) {
    body = `${body}${body && !/[.!?]$/.test(body) ? '.' : ''} ${asOf}`;
  }
  return body.trim();
}

/**
 * The alerts to schedule now, in time order. Past alerts, alerts too far
 * ahead and alerts with no forecast time are dropped; quiet hours move an
 * alert to 08:00; on a day with two, the more severe one stays (a freeze
 * over a frost), then the earlier; at most three in any seven days, and at
 * most `reserve` in all.
 */
export function planSeasonalNotices(
  input: SeasonalInput | null | undefined,
  { now = new Date(), reserve = SEASONAL_RESERVE, horizonDays = SEASONAL_HORIZON_DAYS }:
  { now?: Date; reserve?: number; horizonDays?: number } = {},
): SeasonalNotice[] {
  if (!input?.alerts?.length || reserve <= 0) return [];
  const eventByKey = new Map((input.events ?? []).map((e) => [e.event_key, e]));
  const horizonEnd = now.getTime() + horizonDays * 86_400_000;

  const candidates = input.alerts.flatMap((alert) => {
    const fire = new Date(alert.fire_at);
    if (Number.isNaN(fire.getTime())) return [];
    if (!forecastAsOfLine(alert.built_from_forecast_at)) return [];
    const date = outOfQuietHours(fire);
    if (date.getTime() <= now.getTime() || date.getTime() > horizonEnd) return [];
    const event = eventByKey.get(alert.event_key);
    return [{ alert, event, date, rank: severity(event?.type) }];
  });

  // One a day: the most severe, then the earliest.
  const byDay = new Map<string, typeof candidates[number]>();
  for (const c of candidates) {
    const k = dayKey(c.date);
    const held = byDay.get(k);
    if (!held || c.rank > held.rank
      || (c.rank === held.rank && c.date.getTime() < held.date.getTime())) {
      byDay.set(k, c);
    }
  }

  const kept: typeof candidates = [];
  for (const c of [...byDay.values()].sort((a, b) => a.date.getTime() - b.date.getTime())) {
    if (kept.length >= reserve) break;
    const weekStart = c.date.getTime() - 7 * 86_400_000;
    const inWeek = kept.filter((k) => k.date.getTime() > weekStart).length;
    if (inWeek >= MAX_ALERTS_PER_WEEK) continue;
    kept.push(c);
  }

  return kept.map(({ alert, event, date }) => ({
    identifier: alert.alert_key,
    alertKey: alert.alert_key,
    eventKey: alert.event_key,
    date,
    title: alert.title,
    body: alertBody(alert, event),
    builtFromForecastAt: alert.built_from_forecast_at,
  }));
}

/** When fall hardening began for this plan, if it has: the date after which
 *  outdoor plants on the property get no feeding check. */
export function fallHardeningStart(
  plan: Pick<SeasonalPlan, 'events'> | null | undefined, today: Date = new Date(),
): Date | null {
  const ev = plan?.events.find((e) => e.type === 'fall_hardening');
  if (!ev) return null;
  const raw = ev.window.start ?? ev.sort_date;
  if (!raw) return null;
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(raw);
  if (!m) return null;
  const start = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
  // Only a hardening that has begun, or begins inside the next year, counts.
  if (start.getTime() - today.getTime() > 365 * 86_400_000) return null;
  return start;
}
