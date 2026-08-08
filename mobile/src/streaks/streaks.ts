import { CareLog, CareType, Plant, Species } from '../types';

// All derived from existing care-log data — no storage, no backend. Because
// care logs are append-only, earned milestones stay earned.

const DAY = 86_400_000;

// Forgiving buffer: a plant only counts as "behind" once it's this many days
// PAST the far end of its care window (interval_days_max). Keeps the streak
// calm rather than punishing — a "water every 7–14 days" plant isn't behind
// until day 17.
export const GRACE_DAYS = 3;

// Only these care types have species schedules / can fall behind.
// Mist is absent on purpose — see the note in notifications/plan.ts. It can no
// longer earn a reminder, so it must not be able to break a streak either.
// Repot is absent too (plan 1.3): it became a February inspection with no due
// date, and a check-up with no deadline is not something you can be behind on.
const SCHEDULED: CareType[] = ['water', 'fertilize', 'prune', 'rotate'];

export interface StreakResult {
  /** Consecutive "good-standing" days ending today (no plant left behind). */
  current: number;
  /** Longest good-standing run in the household's history (for badges). */
  best: number;
  /**
   * Share of tracked plantings currently inside their care window, 0–100.
   *
   * The streak is an AND across every plant: one thirsty pot zeroes it. That
   * reads as encouragement on a shelf of five and as a permanent scolding in a
   * garden of three hundred, where something is always a day late. This is the
   * number that stays useful at that size — you can be 96% on track and see
   * it, instead of seeing a zero that never moves.
   */
  onTrackPct: number;
  /** How many tracked plantings are past their window right now. */
  behindCount: number;
  /** How many plantings have a schedule to be judged against at all. */
  trackedCount: number;
}

export interface StreakInput {
  plants: Plant[];
  logsByPlant: Record<number, CareLog[]>;
  speciesById: Record<number, Species>;
  now?: Date;
}

function startOfDay(ms: number): number {
  const d = new Date(ms);
  d.setHours(0, 0, 0, 0);
  return d.getTime();
}

// acquired_on is a date-only string (YYYY-MM-DD). `new Date('2026-07-10')`
// parses as UTC midnight, which lands on the previous day in any timezone
// behind UTC — so parse the components as a LOCAL date instead.
function dayFromDateOnly(s: string): number {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(s);
  if (m) return new Date(+m[1], +m[2] - 1, +m[3]).getTime();
  return startOfDay(new Date(s).getTime());
}

/**
 * A household "care streak": consecutive days in which every care task that
 * had come due was logged on time (within its window + a grace buffer). Days
 * where nothing was due don't break it — you can't miss what isn't due — so
 * the streak fits real plant cadence instead of demanding daily action.
 *
 * Pure and dependency-free (no react-native / expo imports) so it's unit-testable.
 */
export function computeStreak(input: StreakInput): StreakResult {
  const { plants, logsByPlant, speciesById, now = new Date() } = input;
  const today = startOfDay(now.getTime());

  // Per plant: its scheduled intervals, sorted log-day timestamps per care
  // type, and the day it entered the household.
  interface Tracked {
    start: number;
    intervals: { careType: CareType; maxDays: number }[];
    logDaysByType: Record<string, number[]>;
  }
  const tracked: Tracked[] = [];
  let earliest = today;

  for (const plant of plants) {
    const species = speciesById[plant.species_id];
    if (!species?.care_schedules?.length) continue;

    const logs = logsByPlant[plant.id] ?? [];
    const logDaysByType: Record<string, number[]> = {};
    let firstLog = Infinity;
    for (const log of logs) {
      const d = startOfDay(new Date(log.logged_at).getTime());
      (logDaysByType[log.action] ??= []).push(d);
      if (d < firstLog) firstLog = d;
    }
    for (const arr of Object.values(logDaysByType)) arr.sort((a, b) => a - b);

    const acquired = plant.acquired_on
      ? dayFromDateOnly(plant.acquired_on)
      : (firstLog !== Infinity ? firstLog : today);
    const start = Math.min(acquired, firstLog === Infinity ? acquired : firstLog);

    const intervals = species.care_schedules
      .filter((s) => SCHEDULED.includes(s.care_type))
      .map((s) => ({ careType: s.care_type, maxDays: s.interval_days_max }));
    if (!intervals.length) continue;

    tracked.push({ start, intervals, logDaysByType });
    if (start < earliest) earliest = start;
  }

  if (!tracked.length) {
    return { current: 0, best: 0, onTrackPct: 100, behindCount: 0, trackedCount: 0 };
  }

  /** Is this planting past the far end of any of its care windows on day d? */
  const isBehindOn = (t: typeof tracked[number], d: number): boolean => {
    for (const iv of t.intervals) {
      const days = t.logDaysByType[iv.careType] ?? [];
      // newest log of this type on or before day d
      let last = -1;
      for (let i = days.length - 1; i >= 0; i--) {
        if (days[i] <= d) { last = days[i]; break; }
      }
      const anchor = last === -1 ? t.start : last;
      if (d - anchor > (iv.maxDays + GRACE_DAYS) * DAY) return true;
    }
    return false;
  };

  // Walk each day from the oldest plant's start (capped at a year) to today,
  // marking whether the household was in good standing.
  //
  // Stepping with `new Date().setDate(+1)` rather than adding 86,400,000ms:
  // a fixed millisecond day drifts an hour off local midnight the moment the
  // walk crosses a daylight-saving boundary, and the old code then compared
  // `d === today` for an exact match that could never land — silently
  // reporting a zero streak to anyone whose history spanned a time change.
  const rangeStart = Math.max(earliest, today - 365 * DAY);
  let best = 0, run = 0;

  const cursor = new Date(rangeStart);
  while (cursor.getTime() <= today) {
    const d = cursor.getTime();
    let inScope = false;
    let behind = false;
    for (const t of tracked) {
      if (d < t.start) continue;
      inScope = true;
      if (isBehindOn(t, d)) { behind = true; break; }
    }
    if (inScope && !behind) {
      run += 1;
      if (run > best) best = run;
    } else {
      run = 0;
    }
    cursor.setDate(cursor.getDate() + 1);
  }
  // The loop ends on the first day past today, so `run` is today's streak.
  // Assigning it here rather than inside the loop removes the exact-equality
  // test that the DST drift used to defeat.
  const current = run;

  const inScopeToday = tracked.filter((t) => t.start <= today);
  const behindCount = inScopeToday.filter((t) => isBehindOn(t, today)).length;
  const trackedCount = inScopeToday.length;
  const onTrackPct = trackedCount === 0
    ? 100
    : Math.round(((trackedCount - behindCount) / trackedCount) * 100);

  return { current, best, onTrackPct, behindCount, trackedCount };
}

// ── Badges ────────────────────────────────────────────────────────────────────

export interface Badge {
  id: string;
  name: string;
  emoji: string;
  description: string;
  earned: boolean;
}

interface BadgeDef extends Omit<Badge, 'earned'> {
  test: (m: Metrics) => boolean;
}

interface Metrics {
  plantCount: number;
  totalCareActions: number;
  distinctSpecies: number;
  bestStreak: number;
}

// Small, tasteful set spanning first-time / streak / count / variety.
const BADGE_DEFS: BadgeDef[] = [
  { id: 'first_sprout', name: 'First Sprout', emoji: '🌱',
    description: 'Logged your first care action.',
    test: (m) => m.totalCareActions >= 1 },
  { id: 'plant_parent', name: 'Plant Parent', emoji: '🪴',
    description: 'Added 5 plants to your garden.',
    test: (m) => m.plantCount >= 5 },
  { id: 'green_thumb', name: 'Green Thumb', emoji: '🌿',
    description: 'Kept a 7-day care streak.',
    test: (m) => m.bestStreak >= 7 },
  { id: 'botanist', name: 'Botanist', emoji: '📚',
    description: 'Growing 5 different species.',
    test: (m) => m.distinctSpecies >= 5 },
  { id: 'consistent_carer', name: 'Consistent Carer', emoji: '📅',
    description: 'Kept a 30-day care streak.',
    test: (m) => m.bestStreak >= 30 },
  { id: 'century_club', name: 'Century Club', emoji: '💯',
    description: 'Logged 100 care actions.',
    test: (m) => m.totalCareActions >= 100 },
];

export function computeMetrics(
  plants: Plant[],
  logsByPlant: Record<number, CareLog[]>,
  bestStreak: number,
): Metrics {
  let totalCareActions = 0;
  for (const plant of plants) totalCareActions += (logsByPlant[plant.id]?.length ?? 0);
  return {
    plantCount: plants.length,
    totalCareActions,
    distinctSpecies: new Set(plants.map((p) => p.species_id)).size,
    bestStreak,
  };
}

export function computeBadges(metrics: Metrics): Badge[] {
  return BADGE_DEFS.map(({ test, ...b }) => ({ ...b, earned: test(metrics) }));
}
