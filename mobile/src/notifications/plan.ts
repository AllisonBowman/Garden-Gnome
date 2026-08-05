import { CareLog, CareType, Plant, Species } from '../types';

// Care types that can have reminders (matches the quick-log actions on
// PlantDetailScreen; 'clean'/'other' have no species schedules).
//
// 'mist' is deliberately absent. Misting doesn't do what people think: the
// humidity it adds lasts only until the water evaporates, which Penn State
// Extension puts at a matter of minutes, so even daily misting changes nothing
// about ambient humidity. Minnesota Extension adds that it "increases the
// likelihood of foliar leaf spot diseases," and Clemson tells begonia growers
// outright that misting is not recommended. A notification is an instruction to
// act, so a misting reminder is the app asking someone to do something useless
// at best and harmful at worst. Leaf-wiping ('clean') is separately endorsed
// and stays.
export const REMINDER_CARE_TYPES: CareType[] = [
  'water', 'fertilize', 'prune', 'repot', 'rotate',
];

// Months (1-12) in which a care type should be prompted at all. Absent means
// all year.
//
// Feeding is gated to the growing season because every extension source agrees
// on this and several are emphatic: NC State says "do not fertilize from
// November to February," and Maryland warns that feeding then "could harm some
// plants." Growth slows with the light, so the fertiliser isn't taken up — it
// accumulates as salts. A December reminder was the app telling people to do
// the one thing the literature says not to.
export const CARE_SEASON_MONTHS: Partial<Record<CareType, number[]>> = {
  fertilize: [3, 4, 5, 6, 7, 8, 9, 10],
};

/** Whether this care type should be prompted at all in the given month. */
export function isInSeason(careType: CareType, date: Date): boolean {
  const months = CARE_SEASON_MONTHS[careType];
  return !months || months.includes(date.getMonth() + 1);
}

export const CARE_VERBS: Record<string, string> = {
  water: 'water', fertilize: 'fertilize',
  prune: 'prune', repot: 'repot', rotate: 'rotate',
};

export type ReminderPrefs = Partial<Record<CareType, boolean>>;

export interface WeatherSignal {
  /**
   * Whole-day shift applied to WATERING due-dates only: negative brings the
   * reminder sooner (heat dries the plant out faster), positive pushes it
   * later (rain will water an unsheltered plant). Bounded to ±2 days by the
   * planner so weather can nudge, never upend, the schedule.
   */
  waterShiftDays: number;
}

/** Max days weather may move a watering reminder in either direction. */
export const MAX_WEATHER_SHIFT_DAYS = 2;

export interface ReminderItem {
  plantId: number;
  nickname: string;
  careType: CareType;
}

export interface ReminderBatch {
  date: Date;
  title: string;
  body: string;
  items: ReminderItem[];
}

interface PlanInput {
  plants: Plant[];
  logsByPlant: Record<number, CareLog[]>;
  speciesById: Record<number, Species>;
  prefs: ReminderPrefs;
  now?: Date;
  /** Days ahead to schedule (default 30 — stays well under iOS's 64 pending-notification cap since batches are one per day). */
  horizonDays?: number;
  /** Local hour of day to deliver reminders (default 9am). */
  deliveryHour?: number;
  /**
   * Optional per-environment weather nudge, keyed by environment id. Populated
   * only when the user opts in (Settings → weather adjustments). Absent = no
   * weather influence, so the schedule is identical to the weather-free plan.
   */
  weatherByEnv?: Record<number, WeatherSignal>;
}

/**
 * Compute one notification per calendar day, batching every plant/care-type
 * due that day. A plant×care-type becomes due `interval_days_min` days after
 * the most recent care log of that type — falling back to the acquisition
 * date, then to "now", when there's no history — so reminders track real
 * care history, not a fixed cadence from install.
 * Pure and dependency-free: no react-native or expo imports.
 */
export function computeReminderPlan(input: PlanInput): ReminderBatch[] {
  const {
    plants, logsByPlant, speciesById, prefs,
    now = new Date(), horizonDays = 30, deliveryHour = 9,
    weatherByEnv,
  } = input;

  // Earliest allowed delivery slot: today at deliveryHour if that's still in
  // the future, otherwise tomorrow. Overdue plants land in this slot.
  const nextSlot = new Date(now);
  nextSlot.setHours(deliveryHour, 0, 0, 0);
  if (nextSlot <= now) nextSlot.setDate(nextSlot.getDate() + 1);
  const horizonEnd = new Date(now.getTime() + horizonDays * 86_400_000);

  const byDay = new Map<string, { date: Date; items: ReminderItem[] }>();

  for (const plant of plants) {
    const species = speciesById[plant.species_id];
    if (!species?.care_schedules) continue;
    const logs = logsByPlant[plant.id] ?? [];

    for (const schedule of species.care_schedules) {
      const careType = schedule.care_type;
      if (!prefs[careType] || !REMINDER_CARE_TYPES.includes(careType)) continue;

      let anchorMs = 0;
      for (const log of logs) {
        if (log.action !== careType) continue;
        const t = new Date(log.logged_at).getTime();
        if (t > anchorMs) anchorMs = t;
      }
      if (!anchorMs) {
        anchorMs = plant.acquired_on
          ? new Date(plant.acquired_on).getTime()
          : now.getTime();
      }

      // Due when the plant enters its care window ("every 7–10 days" → day 7)
      const due = new Date(anchorMs + schedule.interval_days_min * 86_400_000);

      // Opt-in weather nudge: only watering, only for plants whose environment
      // has a signal, clamped so weather can't move a reminder more than a
      // couple of days. Advancing past `nextSlot` is floored below, so an
      // overdue-after-shift plant simply lands in the next delivery slot.
      if (careType === 'water' && weatherByEnv && plant.environment_id != null) {
        const shift = weatherByEnv[plant.environment_id]?.waterShiftDays ?? 0;
        if (shift) {
          const bounded = Math.max(-MAX_WEATHER_SHIFT_DAYS, Math.min(MAX_WEATHER_SHIFT_DAYS, shift));
          due.setDate(due.getDate() + bounded);
        }
      }

      due.setHours(deliveryHour, 0, 0, 0);
      const slot = due <= nextSlot ? nextSlot : due;
      if (slot > horizonEnd) continue;
      // Checked against the slot, not today: a feeding reminder that would land
      // in December is dropped even when it was computed in October.
      if (!isInSeason(careType, slot)) continue;

      const key = `${slot.getFullYear()}-${slot.getMonth()}-${slot.getDate()}`;
      let batch = byDay.get(key);
      if (!batch) {
        batch = { date: new Date(slot), items: [] };
        byDay.set(key, batch);
      }
      batch.items.push({ plantId: plant.id, nickname: plant.nickname, careType });
    }
  }

  return [...byDay.values()]
    .sort((a, b) => a.date.getTime() - b.date.getTime())
    .map(({ date, items }) => ({ date, items, ...composeMessage(items) }));
}

function composeMessage(items: ReminderItem[]): { title: string; body: string } {
  if (items.length === 1) {
    const [it] = items;
    return {
      title: `🪴 ${it.nickname} needs some care`,
      body: `Time to ${CARE_VERBS[it.careType] ?? it.careType} ${it.nickname}.`,
    };
  }
  const plantCount = new Set(items.map((i) => i.plantId)).size;
  const shown = items.slice(0, 6)
    .map((i) => `${i.nickname} — ${CARE_VERBS[i.careType] ?? i.careType}`);
  const more = items.length > 6 ? ` +${items.length - 6} more` : '';
  return {
    title: plantCount === 1
      ? `🪴 ${items[0].nickname} needs some care`
      : `🪴 ${plantCount} plants need care today`,
    body: shown.join(' · ') + more,
  };
}
