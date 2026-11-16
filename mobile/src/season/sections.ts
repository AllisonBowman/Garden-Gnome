import {
  ForecastDay, FrostRisk, OwnerAction, SeasonEvent, SeasonEventPut, SeasonEventStatus,
  SeasonTask,
} from '../types/site';
import { localDateString, parseServerDate } from '../api/serverDate';

// The Season screen's logic: which events need attention now, which come in
// the next twelve months, which are settled, and the words for statuses,
// owner actions and the forecast strip. Pure.

export const STATUS_WORDS: Record<SeasonEventStatus, string> = {
  happened: 'Recorded for your area',
  happening: 'Happening now',
  forecast: 'In the forecast',
  expected: 'Expected',
  typically_around: 'Typically around',
  done: 'Done',
  not_needed: 'Not needed this year',
};

export const ACTION_LABELS: Record<OwnerAction, string> = {
  mark_happened: 'It happened here',
  mark_not_yet: 'Not yet at my place',
  mark_done: 'Done',
  mark_not_needed: 'Not needed',
  clear: 'Clear my answer',
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
    out.push({ value: localDateString(d), label: i === 0 ? 'Today' : i === 1 ? 'Yesterday' : shortDay(d) });
  }
  return out;
}

const WEEKDAY = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const MONTH = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

/** "Tue 17 Nov" */
export function shortDay(d: Date): string {
  return `${WEEKDAY[d.getDay()]} ${d.getDate()} ${MONTH[d.getMonth()]}`;
}

/** How far ahead the screen plans: the next twelve months. */
export const PLAN_AHEAD_DAYS = 366;

/** How soon an event's window must open to count as "needs attention now". */
export const NOW_DAYS = 7;

export type SectionKey = 'now' | 'ahead' | 'settled';

export const SECTION_TITLES: Record<SectionKey, string> = {
  now: 'Needs attention now',
  ahead: 'The next twelve months',
  settled: 'Already happened or settled',
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
  open: 'To do',
  done: 'Done',
  not_needed: 'Not needed',
};

// ── Forecast strip ───────────────────────────────────────────────────────────

export const FROST_RISK_WORDS: Record<FrostRisk, string> = {
  none: '',
  frost: 'Frost possible',
  freeze: 'Freeze',
  hard_freeze: 'Hard freeze',
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
  const t = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  const diff = Math.round((d.getTime() - t.getTime()) / 86_400_000);
  if (diff === 0) return 'Today';
  if (diff === 1) return 'Tomorrow';
  return WEEKDAY[d.getDay()];
}

const deg = (n: number | null | undefined) => (n == null ? null : `${Math.round(n)}°F`);

export function forecastCells(days: ForecastDay[], today: Date = new Date()): ForecastCell[] {
  return days.map((d) => {
    const hi = deg(d.high_f);
    const lo = deg(d.low_f);
    const temps = [hi, lo].filter(Boolean).join(' / ') || 'No temperature';
    const rain = d.precipitation_chance == null ? null : `${Math.round(d.precipitation_chance)}% rain`;
    const frost = FROST_RISK_WORDS[d.frost_risk] || null;
    const day = dayLabel(d.date, today);
    const a11y = [
      day,
      hi ? `high ${hi.replace('°F', ' degrees Fahrenheit')}` : null,
      lo ? `low ${lo.replace('°F', ' degrees Fahrenheit')}` : null,
      rain ? `${Math.round(d.precipitation_chance!)} percent chance of rain` : null,
      frost, d.summary,
    ].filter(Boolean).join(', ');
    return { date: d.date, day, temps, rain, frost, summary: d.summary, a11y };
  });
}

/** "Forecast: National Weather Service, as of 2 pm Tue 17 Nov." */
export function forecastCredit(providerName: string, fetchedAt: string): string {
  const name = providerName.trim() || 'the forecast provider';
  const d = new Date(fetchedAt);
  if (Number.isNaN(d.getTime())) return `Forecast: ${name}.`;
  const h = d.getHours();
  const time = `${h % 12 === 0 ? 12 : h % 12}${d.getMinutes() ? `:${String(d.getMinutes()).padStart(2, '0')}` : ''} ${h < 12 ? 'am' : 'pm'}`;
  return `Forecast: ${name}, as of ${time} ${shortDay(d)}.`;
}

/**
 * The frost nights in words, for under the forecast bars, which mark them
 * with a snowflake but cannot show how hard: "Frost in the forecast: Today
 * (freeze), Wed (frost possible)." Null when no night has a frost risk.
 */
export function frostNightsLine(days: ForecastDay[], today: Date = new Date()): string | null {
  const nights = forecastCells(days, today)
    .filter((c) => c.frost)
    .map((c) => `${c.day} (${c.frost!.toLowerCase()})`);
  return nights.length ? `Frost in the forecast: ${nights.join(', ')}.` : null;
}
