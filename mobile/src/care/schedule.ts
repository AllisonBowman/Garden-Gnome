import { CareLog, CareType, Plant, Species } from '../types';
import { REMINDER_CARE_TYPES } from '../notifications/plan';

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
  environmentId?: number;
  careType: CareType;
  /** When this plant next enters its care window (anchor + interval_min). */
  dueDate: Date;
  /** Far end of the care window (anchor + interval_max) — "water by" date. */
  windowEndDate: Date;
  /** Most recent log of this care type, or null when there's no history. */
  lastCareDate: Date | null;
  /** Whole calendar days from today to the due date; negative = overdue. */
  daysUntilDue: number;
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

      let anchorMs = 0;
      for (const log of logs) {
        if (log.action !== careType) continue;
        const t = new Date(log.logged_at).getTime();
        if (t > anchorMs) anchorMs = t;
      }
      const lastCareDate = anchorMs ? new Date(anchorMs) : null;
      if (!anchorMs) {
        anchorMs = plant.acquired_on
          ? new Date(plant.acquired_on).getTime()
          : now.getTime();
      }

      const dueDate = new Date(anchorMs + schedule.interval_days_min * DAY_MS);
      const windowEndDate = new Date(anchorMs + schedule.interval_days_max * DAY_MS);
      const daysUntilDue = Math.round(
        (startOfDay(dueDate).getTime() - todayMs) / DAY_MS,
      );
      const status: CareTaskStatus =
        daysUntilDue < 0 ? 'overdue' : daysUntilDue === 0 ? 'due' : 'upcoming';

      tasks.push({
        plantId: plant.id,
        nickname: plant.nickname,
        environmentId: plant.environment_id,
        careType,
        dueDate,
        windowEndDate,
        lastCareDate,
        daysUntilDue,
        status,
      });
    }
  }

  return tasks.sort((a, b) => a.dueDate.getTime() - b.dueDate.getTime());
}

/** Human phrasing of a task's timing: "3 days overdue", "Due today", … */
export function careTaskDueLabel(task: CareTask): string {
  const n = task.daysUntilDue;
  if (n < 0) return n === -1 ? '1 day overdue' : `${-n} days overdue`;
  if (n === 0) return 'Due today';
  if (n === 1) return 'Due tomorrow';
  return `Due in ${n} days`;
}
