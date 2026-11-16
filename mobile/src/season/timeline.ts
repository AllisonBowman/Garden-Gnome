import { SeasonEventStatus, SeasonEventSummary, SeasonEventType } from '../types/site';
import { parseServerDate } from '../api/serverDate';
import { STATUS_WORDS } from './sections';

// The season timeline (map and visuals spec sections 1 and 4.2): each event's
// window as a band on a month axis, a single date as a mark, today as a
// line. The axis starts at the earliest window shown or the month before
// today, whichever is earlier, and spans at most twelve months. Bands are
// packed into rows so neither they nor their titles overlap. Events with no
// dates, or entirely outside the axis, are left out of the picture (they
// stay in the list under it). The axis shows short month names only; the
// span with its years is said once in a caption under the chart. Where the
// titles and the "Today" caption sit is worked out here too, so they can be
// checked not to overlap. Pure: no React Native imports.

/** The months the axis may span. */
export const MAX_MONTHS = 12;
/** The fewest months it spans, so a lone event is not stretched across. */
export const MIN_MONTHS = 4;

/** How a band is coloured. The component maps these to palette colours. */
export type TimelineTone = 'frost' | 'autumn' | 'spring' | 'settled';

const TYPE_TONE: Record<SeasonEventType, Exclude<TimelineTone, 'settled'>> = {
  first_frost: 'frost', first_freeze: 'frost', hard_freeze: 'frost', last_frost: 'frost',
  fall_hardening: 'autumn', leaf_drop: 'autumn', dormancy: 'autumn',
  spring_emergence: 'spring', tender_plants_out: 'spring', spring_cleanup: 'spring',
};

const SETTLED: SeasonEventStatus[] = ['happened', 'done', 'not_needed'];
const LIVE: SeasonEventStatus[] = ['happening', 'forecast'];

const MONTH = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const MONTH_LONG = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
  'September', 'October', 'November', 'December'];

export function eventTone(type: SeasonEventType, status: SeasonEventStatus): TimelineTone {
  if (SETTLED.includes(status)) return 'settled';
  return TYPE_TONE[type] ?? 'autumn';
}

export interface TimelineOptions {
  width: number;
  /** Estimated width of a title in pixels, per character. */
  charWidth?: number;
  /** Space kept between items in one row. */
  gap?: number;
  /** A mark's width, for packing. */
  markWidth?: number;
}

export interface MonthTick {
  x: number;
  /** The short month name, "Jan", with no year (see `spanText`). */
  label: string;
  /** The month's width on the axis. */
  width: number;
}

export interface TimelineItem {
  event_key: string;
  title: string;
  /** A band from x0 to x1, or a mark at x0 (x1 equal to it). */
  kind: 'band' | 'mark';
  x0: number;
  x1: number;
  /** Where the title starts, and its estimated width. */
  labelX: number;
  labelWidth: number;
  row: number;
  tone: TimelineTone;
  /** Happening now or in the forecast: drawn stronger. */
  live: boolean;
  /** Cut at an end of the axis. */
  clippedStart: boolean;
  clippedEnd: boolean;
  /** The event as one sentence for a screen reader. */
  a11y: string;
}

export interface TimelineLayout {
  /** First day of the axis's first month, and the day after its last. */
  start: Date;
  end: Date;
  months: MonthTick[];
  items: TimelineItem[];
  rows: number;
  /** Where today is, or null when it is outside the axis. */
  todayX: number | null;
  /** Events left out of the picture: no dates, or outside the axis. */
  leftOut: string[];
  /** The months the axis spans, for the caption under the chart:
   *  "September 2026 to August 2027". */
  spanText: string;
}

/** The chart's fixed sizes in view pixels, shared with SeasonTimeline. */
export const TIMELINE_GEOMETRY = {
  /** Month names above the rows. */
  axisH: 20,
  monthSize: 10,
  rowH: 34,
  bandH: 10,
  /** The "Today" caption's own row under the event rows. */
  footH: 14,
  todayWidth: 36,
  titleSize: 11.5,
  /** A title's top inside its row, and its height with the halo. */
  titleTop: 2,
  titleH: 16,
  /** The halo's padding either side of a title. */
  haloPad: 2,
} as const;

/** A safe average character width as a share of the font size. */
export const TIMELINE_CHAR_SHARE = 0.62;

export interface Rect { left: number; top: number; width: number; height: number }

/** The chart's height for this many rows of events. */
export function timelineHeight(rows: number): number {
  const g = TIMELINE_GEOMETRY;
  return g.axisH + Math.max(1, rows) * g.rowH + g.footH;
}

/** Where an event's title is drawn, halo included, in chart pixels. */
export function titleRect(item: TimelineItem): Rect {
  const g = TIMELINE_GEOMETRY;
  return {
    left: item.labelX - g.haloPad, top: g.axisH + item.row * g.rowH + g.titleTop,
    width: item.labelWidth + 2 * g.haloPad, height: g.titleH,
  };
}

/** Where the "Today" caption is drawn: in its own row under the events,
 *  centred on the today line and kept inside the chart; null with no today
 *  line. It never shares a row with a title, so it cannot cover one. */
export function todayCaptionRect(layout: TimelineLayout, width: number): Rect | null {
  if (layout.todayX == null) return null;
  const g = TIMELINE_GEOMETRY;
  const w = g.todayWidth;
  return {
    left: Math.max(0, Math.min(width - w, layout.todayX - w / 2)),
    top: timelineHeight(layout.rows) - g.footH, width: w, height: g.footH,
  };
}

/** Whole days since 1970 for a local calendar day, safe across clock changes. */
function dayNumber(d: Date): number {
  return Math.round(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()) / 86_400_000);
}

function monthStart(d: Date): Date {
  return new Date(d.getFullYear(), d.getMonth(), 1);
}

function addMonths(d: Date, n: number): Date {
  return new Date(d.getFullYear(), d.getMonth() + n, 1);
}

function monthsBetween(a: Date, b: Date): number {
  return (b.getFullYear() - a.getFullYear()) * 12 + (b.getMonth() - a.getMonth());
}

/** "12 November" */
function spokenDay(d: Date): string {
  return `${d.getDate()} ${MONTH_LONG[d.getMonth()]}`;
}

interface Dated { e: SeasonEventSummary; from: Date; to: Date; point: boolean }

function datesOf(e: SeasonEventSummary): Dated | null {
  const s = parseServerDate(e.window?.start ?? null);
  const t = parseServerDate(e.window?.end ?? null);
  if (!s && !t) return null;
  let from = s ?? t!;
  let to = t ?? s!;
  if (dayNumber(to) < dayNumber(from)) [from, to] = [to, from];
  return { e, from, to, point: dayNumber(from) === dayNumber(to) };
}

/**
 * The timeline for these events, `width` pixels across. Today defaults to
 * now. A window that runs past an end of the axis is cut there and says so.
 */
export function seasonTimeline(
  events: SeasonEventSummary[], opts: TimelineOptions, today: Date = new Date(),
): TimelineLayout {
  const width = Math.max(1, opts.width);
  const charWidth = opts.charWidth ?? 6.5;
  const gap = opts.gap ?? 6;
  const markWidth = opts.markWidth ?? 8;

  const dated: Dated[] = [];
  const leftOut: string[] = [];
  for (const e of events) {
    const d = datesOf(e);
    if (d) dated.push(d); else leftOut.push(e.event_key);
  }

  // The month before today is the latest the axis may start; it starts
  // earlier for a window still open that began before then.
  const floor = addMonths(monthStart(today), -1);
  const relevant = dated.filter((d) => dayNumber(d.to) >= dayNumber(floor));
  let start = floor;
  for (const d of relevant) if (d.from < start) start = monthStart(d.from);
  // Never so early that today falls off the end.
  if (monthsBetween(start, monthStart(today)) >= MAX_MONTHS) start = addMonths(monthStart(today), -(MAX_MONTHS - 1));
  const lastShown = relevant.reduce<Date | null>((acc, d) => {
    const m = monthStart(d.to);
    return acc == null || m > acc ? m : acc;
  }, null);
  // Through the last window shown, and always through the month after today.
  const wanted = Math.max(
    lastShown ? monthsBetween(start, lastShown) + 1 : MIN_MONTHS,
    monthsBetween(start, monthStart(today)) + 2,
  );
  const months = Math.max(MIN_MONTHS, Math.min(MAX_MONTHS, wanted));
  const end = addMonths(start, months);

  const d0 = dayNumber(start);
  const span = dayNumber(end) - d0;
  const xOf = (d: Date) => ((dayNumber(d) - d0) / span) * width;

  const ticks: MonthTick[] = [];
  for (let i = 0; i < months; i++) {
    const m = addMonths(start, i);
    const next = addMonths(start, i + 1);
    ticks.push({ x: xOf(m), label: MONTH[m.getMonth()], width: xOf(next) - xOf(m) });
  }

  const items: Omit<TimelineItem, 'row'>[] = [];
  for (const d of dated) {
    const fromN = dayNumber(d.from);
    const toN = dayNumber(d.to);
    if (toN < d0 || fromN >= dayNumber(end)) { leftOut.push(d.e.event_key); continue; }
    const clippedStart = fromN < d0;
    const clippedEnd = toN >= dayNumber(end);
    const x0 = clippedStart ? 0 : xOf(d.from);
    // A band covers its last day too.
    const x1 = d.point ? x0 : clippedEnd ? width : Math.min(width, ((toN + 1 - d0) / span) * width);
    const labelWidth = Math.min(width, Math.ceil(d.e.title.length * charWidth));
    const labelX = Math.max(0, Math.min(x0, width - labelWidth));
    const status = STATUS_WORDS[d.e.status] ?? '';
    const when = d.e.window?.text?.trim()
      || (d.point ? spokenDay(d.from) : `${spokenDay(d.from)} to ${spokenDay(d.to)}`);
    const a11y = [
      `${d.e.title}: ${when.replace(/[.\s]+$/, '')}`,
      status,
      clippedEnd ? 'Runs past the end of this timeline' : '',
      clippedStart ? 'Began before the start of this timeline' : '',
    ].filter(Boolean).join('. ') + '.';
    items.push({
      event_key: d.e.event_key, title: d.e.title, kind: d.point ? 'mark' : 'band',
      x0, x1, labelX, labelWidth, tone: eventTone(d.e.type, d.e.status), live: LIVE.includes(d.e.status),
      clippedStart, clippedEnd, a11y,
    });
  }

  // Pack into rows: earliest first, each into the first row it fits.
  const order = items.map((it, i) => ({ it, i })).sort((a, b) => a.it.x0 - b.it.x0 || a.i - b.i);
  const rowEnds: number[] = [];
  const placed: TimelineItem[] = new Array(items.length);
  for (const { it, i } of order) {
    const left = Math.min(it.x0, it.labelX);
    const right = Math.max(it.kind === 'mark' ? it.x0 + markWidth : it.x1, it.labelX + it.labelWidth);
    let row = rowEnds.findIndex((r) => r + gap <= left);
    if (row < 0) { row = rowEnds.length; rowEnds.push(right); } else rowEnds[row] = right;
    placed[i] = { ...it, row };
  }

  const tN = dayNumber(today);
  const todayX = tN >= d0 && tN < dayNumber(end) ? xOf(today) : null;

  const last = addMonths(end, -1);
  const spanText = `${MONTH_LONG[start.getMonth()]} ${start.getFullYear()} to ${MONTH_LONG[last.getMonth()]} ${last.getFullYear()}`;

  return { start, end, months: ticks, items: placed, rows: rowEnds.length, todayX, leftOut, spanText };
}

/**
 * Whether the timeline draws any event (the axis and which events fall on
 * it do not depend on the width). A screen shows the timeline's heading
 * only when this is true, so the heading never stands alone.
 */
export function timelineDrawsAnything(events: SeasonEventSummary[], today?: Date): boolean {
  return seasonTimeline(events, { width: 1 }, today).items.length > 0;
}
