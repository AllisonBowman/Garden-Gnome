import { CareLog, CareType, Plant, Species } from '../types';
import {
  REMINDER_CARE_TYPES, REPOT_INSPECTION_MONTH, isInSeason,
} from '../notifications/plan';
import { GRACE_DAYS } from '../streaks/streaks';
import { parseServerDate } from '../api/serverDate';

// One "next due" per plant × scheduled care-type, surfaced for the calendar and
// the Plants to-do list. This is the same anchor math the reminder planner uses
// (plan.ts) — most-recent log of that care type, else the acquisition date,
// else now; due `interval_days_min` days later — but WITHOUT the planner's two
// UI-hostile behaviours: it never floors an overdue date into a delivery slot
// (the to-do list needs to say *how* overdue), and it never gates on the user's
// notification preferences (a plant is due whether or not reminders are on).
//
// Pure and dependency-free (no react-native / expo imports) so it stays unit
// testable and safe to import from any screen.

const DAY_MS = 86_400_000;

export type CareTaskStatus = 'overdue' | 'due' | 'upcoming';

export interface CareTask {
  plantId: number;
  nickname: string;
  growingAreaId?: number;
  careType: CareType;
  /** When this plant next enters its care window (anchor + interval_min). */
  dueDate: Date;
  /** Far end of the care window (anchor + interval_max) — "water by" date. */
  windowEndDate: Date;
  /** Most recent log of this care type, or null when there's no history. */
  lastCareDate: Date | null;
  /** Whole calendar days from today to the START of the care window. */
  daysUntilDue: number;
  /** Days past the END of the window; negative means still inside it. */
  daysPastWindow: number;
  /** Whole days since this care was last done, or null with no history.
   *  Computed here rather than in the label so the label stays pure and the
   *  injected clock is honoured. */
  daysSinceLastCare: number | null;
  status: CareTaskStatus;
}

/** Midnight (local) of the given date — status compares whole calendar days,
 *  so an item due "today" reads as due all day, not overdue by mid-afternoon. */
export function startOfDay(d: Date): Date {
  const s = new Date(d);
  s.setHours(0, 0, 0, 0);
  return s;
}

/** Stable per-calendar-day key for grouping tasks (calendar cells, batches). */
export function dayKey(d: Date): string {
  return `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`;
}

interface CareTasksInput {
  plants: Plant[];
  logsByPlant: Record<number, CareLog[]>;
  speciesById: Record<number, Species>;
  now?: Date;
}

/**
 * Compute the next-due care task for every plant × scheduled care-type.
 * Sorted soonest-due first. Species without loaded `care_schedules` contribute
 * nothing (plant lists embed species without schedules — callers must fetch
 * species details, exactly as reminders.ts does).
 */
export function computeCareTasks(input: CareTasksInput): CareTask[] {
  const { plants, logsByPlant, speciesById, now = new Date() } = input;
  const todayMs = startOfDay(now).getTime();
  const tasks: CareTask[] = [];

  for (const plant of plants) {
    const species = speciesById[plant.species_id];
    if (!species?.care_schedules) continue;
    const logs = logsByPlant[plant.id] ?? [];

    for (const schedule of species.care_schedules) {
      const careType = schedule.care_type;
      if (!REMINDER_CARE_TYPES.includes(careType)) continue;
      // Out-of-season care isn't a task. Feeding in December isn't "overdue" —
      // it's something the plant shouldn't have at all until the light returns.
      if (!isInSeason(careType, now)) continue;

      let anchorMs = 0;
      for (const log of logs) {
        if (log.action !== careType) continue;
        const t = new Date(log.logged_at).getTime();
        if (t > anchorMs) anchorMs = t;
      }
      const lastCareDate = anchorMs ? new Date(anchorMs) : null;
      if (!anchorMs) {
        // acquired_on is a date-only string: the caretaker's day, not UTC's.
        anchorMs = parseServerDate(plant.acquired_on)?.getTime() ?? now.getTime();
      }

      // Repotting is a February inspection, not an interval (plan 1.3). The
      // task exists only during the inspection month, only when no
      // repot-family log has been made this calendar year, and it is never
      // overdue — March simply closes the window until next spring.
      if (careType === 'repot') {
        if (now.getMonth() + 1 !== REPOT_INSPECTION_MONTH) continue;
        if (lastCareDate
          && lastCareDate.getFullYear() === now.getFullYear()) continue;
        const dueDate = new Date(
          now.getFullYear(), REPOT_INSPECTION_MONTH - 1, 1);
        const windowEndDate = new Date(
          now.getFullYear(), REPOT_INSPECTION_MONTH, 1);
        tasks.push({
          plantId: plant.id,
          nickname: plant.nickname,
          growingAreaId: plant.growing_area_id,
          careType,
          dueDate,
          windowEndDate,
          lastCareDate,
          daysUntilDue: Math.round(
            (startOfDay(dueDate).getTime() - todayMs) / DAY_MS),
          daysPastWindow: Math.round(
            (todayMs - startOfDay(windowEndDate).getTime()) / DAY_MS),
          daysSinceLastCare: lastCareDate
            ? Math.round(
              (todayMs - startOfDay(lastCareDate).getTime()) / DAY_MS)
            : null,
          status: 'due',
        });
        continue;
      }

      // The species record gives a WINDOW, not a deadline: "every 7–10 days"
      // means anywhere in that span is right. Day 10 of a 7–10 window is the
      // plant behaving exactly as documented, so calling it overdue is simply
      // wrong — and it pushed people to water early, which is the direction
      // that kills plants. `dueDate` opens the window; nothing is late until
      // the window has closed and the same grace the streak allows has passed.
      const dueDate = new Date(anchorMs + schedule.interval_days_min * DAY_MS);
      const windowEndDate = new Date(anchorMs + schedule.interval_days_max * DAY_MS);
      const daysUntilDue = Math.round(
        (startOfDay(dueDate).getTime() - todayMs) / DAY_MS,
      );
      const daysPastWindow = Math.round(
        (todayMs - startOfDay(windowEndDate).getTime()) / DAY_MS,
      );
      const status: CareTaskStatus =
        daysPastWindow > GRACE_DAYS ? 'overdue'
          : daysUntilDue <= 0 ? 'due'
            : 'upcoming';

      tasks.push({
        plantId: plant.id,
        nickname: plant.nickname,
        growingAreaId: plant.growing_area_id,
        careType,
        dueDate,
        windowEndDate,
        lastCareDate,
        daysUntilDue,
        daysPastWindow,
        daysSinceLastCare: lastCareDate
          ? Math.round((todayMs - startOfDay(lastCareDate).getTime()) / DAY_MS)
          : null,
        status,
      });
    }
  }

  return tasks.sort((a, b) => a.dueDate.getTime() - b.dueDate.getTime());
}

// ── Plants with no check schedule ────────────────────────────────────────────
// Most of the catalog has no care schedule on record yet: the claims carry a
// watering regime but no interval, and an interval nobody published is one
// the app will not invent. A plant of such a species gets no to-do, no
// calendar entry and no reminder — and the screens say so, rather than let
// silence (or "all caught up") read as "nothing needed".

/** Whether the species has a check schedule the app can keep: any interval
 *  for a care type that becomes a to-do or a reminder. */
export function hasCheckSchedule(species: Species): boolean {
  return (species.care_schedules ?? [])
    .some((s) => REMINDER_CARE_TYPES.includes(s.care_type));
}

export interface UnscheduledPlant {
  plantId: number;
  nickname: string;
  growingAreaId?: number;
}

/** The plants whose species was read and has no check schedule. A species
 *  that failed to load is not one with no schedule, so it is not listed. */
export function unscheduledPlants(input: CareTasksInput): UnscheduledPlant[] {
  const out: UnscheduledPlant[] = [];
  for (const plant of input.plants) {
    const species = input.speciesById[plant.species_id];
    if (!species || hasCheckSchedule(species)) continue;
    out.push({
      plantId: plant.id, nickname: plant.nickname, growingAreaId: plant.growing_area_id,
    });
  }
  return out;
}

/** On a plant's own page: why nothing is scheduled for it, and where to look
 *  instead. */
export const NO_SCHEDULE_LINE =
  'No check schedule on record for this species yet; its care guide below has '
  + 'what its sources say. There are no reminders for it until there is one.';

/** Under a to-do list or a calendar: which plants it leaves out, and why. */
export function unscheduledLine(plants: UnscheduledPlant[]): string | null {
  if (plants.length === 0) return null;
  if (plants.length === 1) {
    return `No check schedule on record for ${plants[0].nickname}’s species yet, so `
      + 'nothing is scheduled for it. Its care guide has what its sources say.';
  }
  return `${plants.length} plants have no check schedule on record for their species `
    + 'yet, so nothing is scheduled for them. Each one’s care guide has what its '
    + 'sources say.';
}

/** Whether the to-do card may say "All caught up": only when there are
 *  checks to be caught up on and no plant was left out of them. A plant
 *  nobody scheduled isn't caught up, it's unscheduled; one whose log
 *  couldn't be read isn't known to be. */
export function allCaughtUp(taskCount: number, leftOutCount: number): boolean {
  return taskCount > 0 && leftOutCount === 0;
}

/** Plants left out because their care log couldn't be read just now. */
export function unreadLine(count: number): string | null {
  if (count <= 0) return null;
  return count === 1
    ? 'Couldn’t read 1 plant’s care log just now, so it’s left out here.'
    : `Couldn’t read ${count} plants’ care logs just now, so they’re left out here.`;
}

/**
 * Human phrasing of a task's timing.
 *
 * Care is a window, so the honest thing to say is how long it has been — not
 * how late you are. Even past the window the copy stays elapsed time ("Last
 * done 12 days ago"): the `overdue` status still exists for sorting and the
 * warning colour, but a number counting up from "you failed" pushed people to
 * pour water on damp soil, which is the wrong direction to nag in.
 */
export function careTaskDueLabel(task: CareTask): string {
  if (task.status === 'overdue' || task.status === 'due') {
    const since = task.daysSinceLastCare;
    if (since === null) return 'Worth a check';
    return since === 1 ? 'Last done 1 day ago' : `Last done ${since} days ago`;
  }
  const n = task.daysUntilDue;
  if (n === 1) return 'Check tomorrow';
  return `Check in ${n} days`;
}
