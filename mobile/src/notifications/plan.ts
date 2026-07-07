import { CareLog, CareType, Plant, Species } from '../types';

// Care types that can have reminders (matches the quick-log actions on
// PlantDetailScreen; 'clean'/'other' have no species schedules).
export const REMINDER_CARE_TYPES: CareType[] = [
  'water', 'fertilize', 'mist', 'prune', 'repot', 'rotate',
];

export const CARE_VERBS: Record<string, string> = {
  water: 'water', fertilize: 'fertilize', mist: 'mist',
  prune: 'prune', repot: 'repot', rotate: 'rotate',
};

export type ReminderPrefs = Partial<Record<CareType, boolean>>;

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
      due.setHours(deliveryHour, 0, 0, 0);
      const slot = due <= nextSlot ? nextSlot : due;
      if (slot > horizonEnd) continue;

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
