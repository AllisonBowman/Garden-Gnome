import {
  ForecastDay, FrostRisk, OwnerAction, SeasonEvent, SeasonEventPut, SeasonEventStatus,
  SeasonTask,
} from '../types/site';
import { localDateString, parseServerDate } from '../api/serverDate';
import { t } from '../i18n';
import { clock, shortDay as shortDayWords, weekdayShort } from './dateWords';

// The Season screen's logic: which events need attention now, which come in
// the next twelve months, which are settled, and the words for statuses,
// owner actions and the forecast strip. Pure.

export const STATUS_WORDS: Record<SeasonEventStatus, string> = {
  happened: t('season.status.happened'),
  happening: t('season.status.happening'),
  forecast: t('season.status.forecast'),
  expected: t('season.status.expected'),
  typically_around: t('season.status.typically_around'),
  done: t('season.status.done'),
  not_needed: t('season.status.not_needed'),
};

export const ACTION_LABELS: Record<OwnerAction, string> = {
  mark_happened: t('season.actions.mark_happened'),
  mark_not_yet: t('season.actions.mark_not_yet'),
  mark_done: t('season.actions.mark_done'),
  mark_not_needed: t('season.actions.mark_not_needed'),
  clear: t('season.actions.clear'),
};

/** The order the actions are offered in, whatever order the server sends. */
const ACTION_ORDER: OwnerAction[] = [
  'mark_done', 'mark_happened', 'mark_not_yet', 'mark_not_needed', 'clear',
];

export function orderedActions(actions: OwnerAction[]): OwnerAction[] {
  return ACTION_ORDER.filter((a) => actions.includes(a));
}

/** The PUT body for an owner action. "It happened here" carries the day the
 *  owner picked (today when none was picked). */
export function actionBody(action: OwnerAction, observedOn?: string): SeasonEventPut {
  switch (action) {
    case 'mark_happened': return { state: 'happened', observed_on: observedOn ?? localDateString() };
    case 'mark_not_yet': return { state: 'not_yet' };
    case 'mark_done': return { state: 'done' };
    case 'mark_not_needed': return { state: 'not_needed' };
    case 'clear': return { state: 'clear' };
  }
}

/** The days an owner can say something happened: today and the six before,
 *  as tap choices (no date picker module is in the app). */
export function observedDayChoices(today: Date = new Date(), count = 7): { value: string; label: string }[] {
  const out: { value: string; label: string }[] = [];
  for (let i = 0; i < count; i++) {
    const d = new Date(today.getFullYear(), today.getMonth(), today.getDate() - i);
    out.push({
      value: localDateString(d),
      label: i === 0 ? t('season.dates.today') : i === 1 ? t('season.dates.yesterday') : shortDay(d),
    });
  }
  return out;
}

/** What a screen reader says for a day choice: "It happened today",
 *  "It happened on Tue 17 Nov". `index` is the choice's place in the list. */
export function observedDayA11y(index: number, label: string): string {
  if (index === 0) return t('season.screen.happenedToday');
  if (index === 1) return t('season.screen.happenedYesterday');
  return t('season.screen.happenedOn', { day: label });
}

/** "Tue 17 Nov" */
export function shortDay(d: Date): string {
  return shortDayWords(d);
}

/** How far ahead the screen plans: the next twelve months. */
export const PLAN_AHEAD_DAYS = 366;

/** How soon an event's window must open to count as "needs attention now". */
export const NOW_DAYS = 7;

export type SectionKey = 'now' | 'ahead' | 'settled';

export const SECTION_TITLES: Record<SectionKey, string> = {
  now: t('season.sections.now'),
  ahead: t('season.sections.ahead'),
  settled: t('season.sections.settled'),
};

export interface SeasonSection {
  key: SectionKey;
  title: string;
  events: SeasonEvent[];
}

const SETTLED: SeasonEventStatus[] = ['happened', 'done', 'not_needed'];
const LIVE: SeasonEventStatus[] = ['happening', 'forecast'];

function eventDate(e: SeasonEvent): Date | null {
  return parseServerDate(e.sort_date ?? e.window.start ?? null);
}

function hasOpenTask(e: SeasonEvent): boolean {
  return e.tasks.some((t) => t.state === 'open');
}

/** Whether today falls inside the event's window, or its window opens within
 *  NOW_DAYS. */
function opensSoon(e: SeasonEvent, today: Date): boolean {
  const start = parseServerDate(e.window.start ?? e.sort_date ?? null);
  const end = parseServerDate(e.window.end ?? null);
  const t0 = new Date(today.getFullYear(), today.getMonth(), today.getDate()).getTime();
  if (start && start.getTime() <= t0 && (!end || end.getTime() >= t0)) return true;
  return !!start && start.getTime() > t0 && start.getTime() - t0 <= NOW_DAYS * 86_400_000;
}

function byDate(a: SeasonEvent, b: SeasonEvent): number {
  const x = eventDate(a)?.getTime();
  const y = eventDate(b)?.getTime();
  if (x != null && y != null && x !== y) return x - y;
  if (x != null && y == null) return -1;
  if (x == null && y != null) return 1;
  return 0;
}

/**
 * The plan in three sections. "Needs attention now": happening or in the
 * forecast, or a window open now or opening within a week, with something
 * still to do. "The next twelve months": the rest that lie ahead, in date
 * order. "Already happened or settled": recorded, done or not needed, most
 * recent first. An event dated more than twelve months out is left off.
 * Empty sections are dropped.
 */
export function seasonSections(events: SeasonEvent[], today: Date = new Date()): SeasonSection[] {
  const horizon = today.getTime() + PLAN_AHEAD_DAYS * 86_400_000;
  const now: SeasonEvent[] = [];
  const ahead: SeasonEvent[] = [];
  const settled: SeasonEvent[] = [];
  for (const e of [...events].sort(byDate)) {
    if (SETTLED.includes(e.status) && !hasOpenTask(e)) { settled.push(e); continue; }
    const d = eventDate(e);
    if (d && d.getTime() > horizon) continue;
    if (LIVE.includes(e.status) || (opensSoon(e, today) && (hasOpenTask(e) || !SETTLED.includes(e.status)))) {
      now.push(e);
    } else {
      ahead.push(e);
    }
  }
  settled.reverse();
  const out: SeasonSection[] = [
    { key: 'now', title: SECTION_TITLES.now, events: now },
    { key: 'ahead', title: SECTION_TITLES.ahead, events: ahead },
    { key: 'settled', title: SECTION_TITLES.settled, events: settled },
  ];
  return out.filter((s) => s.events.length > 0);
}

/** Which section holds an event, so a link from Home can open it there. */
export function sectionOf(sections: SeasonSection[], eventKey: string): SectionKey | null {
  return sections.find((s) => s.events.some((e) => e.event_key === eventKey))?.key ?? null;
}

/** The tasks under an event: open ones first, settled ones after. */
export function orderedTasks(tasks: SeasonTask[]): SeasonTask[] {
  return [...tasks].sort((a, b) => Number(a.state !== 'open') - Number(b.state !== 'open'));
}

export const TASK_STATE_WORDS: Record<SeasonTask['state'], string> = {
  open: t('season.taskStates.open'),
  done: t('season.taskStates.done'),
  not_needed: t('season.taskStates.not_needed'),
};

// ── Forecast strip ───────────────────────────────────────────────────────────

export const FROST_RISK_WORDS: Record<FrostRisk, string> = {
  none: '',
  frost: t('season.frostRisk.frost'),
  freeze: t('season.frostRisk.freeze'),
  hard_freeze: t('season.frostRisk.hard_freeze'),
};

export interface ForecastCell {
  date: string;
  day: string;
  temps: string;
  rain: string | null;
  frost: string | null;
  summary: string;
  a11y: string;
}

function dayLabel(dateStr: string, today: Date): string {
  const d = parseServerDate(dateStr);
  if (!d) return dateStr;
  const t0 = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  const diff = Math.round((d.getTime() - t0.getTime()) / 86_400_000);
  if (diff === 0) return t('season.dates.today');
  if (diff === 1) return t('season.dates.tomorrow');
  return weekdayShort(d);
}

const deg = (n: number | null | undefined) => (n == null ? null : t('season.cells.degreesF', { temp: Math.round(n) }));

export function forecastCells(days: ForecastDay[], today: Date = new Date()): ForecastCell[] {
  return days.map((d) => {
    const hi = deg(d.high_f);
    const lo = deg(d.low_f);
    const temps = [hi, lo].filter(Boolean).join(' / ') || t('season.cells.noTemperature');
    const rain = d.precipitation_chance == null ? null
      : t('season.cells.rain', { pct: Math.round(d.precipitation_chance) });
    const frost = FROST_RISK_WORDS[d.frost_risk] || null;
    const day = dayLabel(d.date, today);
    const a11y = [
      day,
      hi ? t('season.cells.a11yHigh', { temp: Math.round(d.high_f!) }) : null,
      lo ? t('season.cells.a11yLow', { temp: Math.round(d.low_f!) }) : null,
      rain ? t('season.cells.a11yRain', { pct: Math.round(d.precipitation_chance!) }) : null,
      frost, d.summary,
    ].filter(Boolean).join(', ');
    return { date: d.date, day, temps, rain, frost, summary: d.summary, a11y };
  });
}

/** "Forecast: National Weather Service, as of 2 pm Tue 17 Nov." */
export function forecastCredit(providerName: string, fetchedAt: string): string {
  const name = providerName.trim() || t('season.credit.providerFallback');
  const d = new Date(fetchedAt);
  if (Number.isNaN(d.getTime())) return t('season.credit.forecastBy', { name });
  return t('season.credit.forecastByAsOf', { name, time: clock(d), day: shortDay(d) });
}

/**
 * The frost nights in words, for under the forecast bars, which mark them
 * with a snowflake but cannot show how hard: "Frost in the forecast: Today
 * (freeze), Wed (frost possible)." Null when no night has a frost risk.
 */
export function frostNightsLine(days: ForecastDay[], today: Date = new Date()): string | null {
  const nights = forecastCells(days, today)
    .filter((c) => c.frost)
    .map((c) => t('season.frostNight', { day: c.day, risk: c.frost!.toLowerCase() }));
  return nights.length ? t('season.frostNights', { nights: nights.join(', ') }) : null;
}
