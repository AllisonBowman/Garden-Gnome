// Home's "To do this week": at most three tasks, each with Done and Skip.
// Pure; the skip list is stored by homeSkips.ts.
//
// What the buttons do, honestly:
// - A season task belongs to an event; Done marks that event done and Skip
//   marks it not needed, the same answers the season screen offers.
// - A plant check keeps the check's own endings. Water: Done logs
//   "watered" and Skip logs "checked, still damp" (both re-anchor the
//   schedule, as on the Plants list). Roots: Done logs "checked, all fine".
//   Any other check: Done logs it done. Skip on those logs nothing; it hides
//   the row on Home until next week, so Home never claims a chore was done.
import type { CareOutcome } from '../types';
import type { WeekItem } from './week';
import { t } from '../i18n';

export const HOME_TASKS = 3;

export function pickHomeTasks(items: WeekItem[], skipped: ReadonlySet<string>, max = HOME_TASKS): {
  shown: WeekItem[]; more: number;
} {
  const open = items.filter((i) => (i.kind === 'care' || i.state === 'open') && !skipped.has(i.key));
  return { shown: open.slice(0, max), more: Math.max(0, open.length - max) };
}

export type TaskAnswer =
  | { kind: 'season'; state: 'done' | 'not_needed' }
  | { kind: 'log'; outcome?: CareOutcome }
  | { kind: 'hide' };

export function taskAnswer(item: WeekItem, button: 'done' | 'skip'): TaskAnswer {
  if (item.kind === 'season') return { kind: 'season', state: button === 'done' ? 'done' : 'not_needed' };
  if (item.careType === 'water') return { kind: 'log', outcome: button === 'done' ? 'watered' : 'checked_not_needed' };
  if (button === 'skip') return { kind: 'hide' };
  if (item.careType === 'repot') return { kind: 'log', outcome: 'checked_fine' };
  return { kind: 'log' };
}

/** The buttons' words: the check's own endings for water, else Done and Skip. */
export function taskButtons(item: WeekItem): { done: string; skip: string; doneA11y: string; skipA11y: string } {
  const text = item.text.replace(/^\p{Extended_Pictographic}️?\s*/u, '');
  if (item.kind === 'care' && item.careType === 'water') {
    return {
      done: t('home.almanac.doneWater'), skip: t('home.almanac.skipWater'),
      doneA11y: t('home.almanac.doneWaterA11y', { text }), skipA11y: t('home.almanac.skipWaterA11y', { text }),
    };
  }
  return {
    done: t('home.almanac.done'), skip: t('home.almanac.skip'),
    doneA11y: t('home.almanac.doneA11y', { text }), skipA11y: t('home.almanac.skipA11y', { text }),
  };
}

/** "2026-W48": the ISO week a skip lasts for. */
export function isoWeek(d: Date): string {
  const day = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()));
  const dow = day.getUTCDay() || 7;
  day.setUTCDate(day.getUTCDate() + 4 - dow);
  const yearStart = new Date(Date.UTC(day.getUTCFullYear(), 0, 1));
  const week = Math.ceil(((day.getTime() - yearStart.getTime()) / 86_400_000 + 1) / 7);
  return `${day.getUTCFullYear()}-W${String(week).padStart(2, '0')}`;
}
