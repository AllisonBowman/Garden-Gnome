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
const SCHEDULED: CareType[] = ['water', 'fertilize', 'mist', 'prune', 'repot', 'rotate'];

export interface StreakResult {
  /** Consecutive "good-standing" days ending today (no plant left behind). */
  current: number;
  /** Longest good-standing run in the household's history (for badges). */
  best: number;
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

  if (!tracked.length) return { current: 0, best: 0 };

  // Walk each day from the oldest plant's start (capped at a year) to today,
  // marking whether the household was in good standing.
  const rangeStart = Math.max(earliest, today - 365 * DAY);
  let current = 0, best = 0, run = 0;

  for (let d = rangeStart; d <= today; d += DAY) {
    let inScope = false;
    let behind = false;
    for (const t of tracked) {
      if (d < t.start) continue;
      inScope = true;
      for (const iv of t.intervals) {
        const days = t.logDaysByType[iv.careType] ?? [];
        // newest log of this type on or before day d
        let last = -1;
        for (let i = days.length - 1; i >= 0; i--) {
          if (days[i] <= d) { last = days[i]; break; }
        }
        const anchor = last === -1 ? t.start : last;
        if (d - anchor > (iv.maxDays + GRACE_DAYS) * DAY) { behind = true; break; }
      }
      if (behind) break;
    }
    if (inScope && !behind) {
      run += 1;
      if (run > best) best = run;
    } else {
      run = 0;
    }
    if (d === today) current = run;
  }

  return { current, best };
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
