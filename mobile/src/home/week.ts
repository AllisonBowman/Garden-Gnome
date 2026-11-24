import { CareType } from '../types';
import { Source, TaskState, VitalsWeekItem } from '../types/site';
import { CareTask, careTaskDueLabel } from '../care/schedule';
import { careActionLabel } from '../care/labels';
import { t } from '../i18n';

// Home's "This week": the seasonal tasks the server's plan puts in this week,
// merged with per-plant care that is due. Pure, so the order is pinned.
//
// Order: open seasonal tasks first, in the order the server gave them (it
// sorts by the event's date); then plant checks that are due, most overdue
// first, as the Plants to-do list orders them; then seasonal tasks already
// marked done or not needed, so a tap is not lost from view the moment it is
// made. Upcoming plant checks are not "this week" here; they live on each
// growing area's calendar.

export type WeekItem =
  | {
    kind: 'season';
    key: string;
    text: string;
    lowImpactNote: string | null;
    reason: string;
    sources: Source[];
    eventKey: string | null;
    state: TaskState;
  }
  | {
    kind: 'care';
    key: string;
    text: string;
    detail: string;
    plantId: number;
    careType: CareType;
    overdue: boolean;
  };

/** How many plant checks Home lists before summarising the rest. */
export const MAX_CARE_ROWS = 6;

export interface ThisWeek {
  items: WeekItem[];
  /** Plant checks due but not listed (past MAX_CARE_ROWS). */
  moreCare: number;
}

export function mergeThisWeek(
  season: VitalsWeekItem[],
  care: CareTask[],
  maxCare: number = MAX_CARE_ROWS,
): ThisWeek {
  const seen = new Set<string>();
  const open: WeekItem[] = [];
  const settled: WeekItem[] = [];
  for (const { event_key, task } of season) {
    if (seen.has(task.task_key)) continue;
    seen.add(task.task_key);
    const item: WeekItem = {
      kind: 'season',
      key: `season:${task.task_key}`,
      text: task.text,
      lowImpactNote: task.low_impact_note ?? null,
      reason: task.reason,
      sources: task.sources,
      eventKey: event_key ?? null,
      state: task.state,
    };
    (task.state === 'open' ? open : settled).push(item);
  }

  const due = care
    .filter((t) => t.status === 'overdue' || t.status === 'due')
    .sort((a, b) => a.daysUntilDue - b.daysUntilDue
      || a.nickname.localeCompare(b.nickname));
  const careItems: WeekItem[] = due.slice(0, Math.max(0, maxCare)).map((t) => ({
    kind: 'care',
    key: `care:${t.plantId}:${t.careType}`,
    text: careActionLabel(t.careType, t.nickname),
    detail: careTaskDueLabel(t),
    plantId: t.plantId,
    careType: t.careType,
    overdue: t.status === 'overdue',
  }));

  return {
    items: [...open, ...careItems, ...settled],
    moreCare: Math.max(0, due.length - careItems.length),
  };
}

/** The line under a list that left plant checks out. */
export function moreCareLine(n: number): string | null {
  if (n <= 0) return null;
  return t('home.week.moreCare', { count: n });
}

/** Counts the headline speaks of. */
export function weekCounts(week: ThisWeek): { openSeason: number; careDue: number } {
  let openSeason = 0;
  let careDue = week.moreCare;
  for (const item of week.items) {
    if (item.kind === 'season' && item.state === 'open') openSeason += 1;
    if (item.kind === 'care') careDue += 1;
  }
  return { openSeason, careDue };
}
