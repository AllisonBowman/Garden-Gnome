import { computeReminderPlan, isInSeason, REMINDER_CARE_TYPES } from './plan';
import { computeCareTasks } from '../care/schedule';
import { CareLog, Plant, Species } from '../types';

// The app used to prompt two things the horticultural literature says not to
// do: misting on a schedule (which raises humidity for minutes and invites
// foliar disease) and feeding through the winter (which Maryland Extension
// says "could harm some plants", because growth has slowed and the fertiliser
// accumulates as salts instead). These lock both doors.

function species(schedules: Species['care_schedules']): Species {
  return {
    id: 100, common_name: 'Fern', scientific_name: 'Testus',
    light_need: 'bright_indirect', humidity_pct_min: 40, humidity_pct_max: 60,
    temp_f_min: 60, temp_f_max: 85, soil_type: 'loam', toxic_to_pets: false,
    care_notes: '', care_schedules: schedules,
  } as Species;
}

const PLANT = {
  id: 1, plant_uuid: 'p', nickname: 'Ferny', species_id: 100,
  environment_id: 5, location: '', maturity_stage: 'mature', intake_notes: '',
} as Plant;

const FEED_AND_WATER = [
  { id: 1, species_id: 100, care_type: 'water' as const, interval_days_min: 7, interval_days_max: 10, notes: '' },
  { id: 2, species_id: 100, care_type: 'fertilize' as const, interval_days_min: 30, interval_days_max: 60, notes: '' },
];

// Logged long ago, so both care types are due whenever we look.
const LOGS: Record<number, CareLog[]> = {
  1: [
    { id: 1, plant_id: 1, action: 'water', notes: '', logged_at: '2025-01-01T09:00:00' },
    { id: 2, plant_id: 1, action: 'fertilize', notes: '', logged_at: '2025-01-01T09:00:00' },
  ],
};

function plannedTypes(now: Date): string[] {
  const batches = computeReminderPlan({
    plants: [PLANT],
    logsByPlant: LOGS,
    speciesById: { 100: species(FEED_AND_WATER) },
    prefs: { water: true, fertilize: true },
    now,
  });
  return batches.flatMap((b) => b.items.map((i) => i.careType));
}

describe('misting is not a thing the app asks anyone to do', () => {
  it('is not a care type that can carry a reminder', () => {
    expect(REMINDER_CARE_TYPES).not.toContain('mist');
  });

  it('produces no reminder even when a species carries a mist schedule', () => {
    const withMist = [
      { id: 3, species_id: 100, care_type: 'mist' as const, interval_days_min: 2, interval_days_max: 3, notes: '' },
    ];
    const batches = computeReminderPlan({
      plants: [PLANT],
      logsByPlant: LOGS,
      speciesById: { 100: species(withMist) },
      prefs: { mist: true } as never,
      now: new Date('2026-07-15T08:00:00'),
    });
    expect(batches).toEqual([]);
  });

  it('produces no to-do either', () => {
    const withMist = [
      { id: 3, species_id: 100, care_type: 'mist' as const, interval_days_min: 2, interval_days_max: 3, notes: '' },
    ];
    const tasks = computeCareTasks({
      plants: [PLANT],
      logsByPlant: LOGS,
      speciesById: { 100: species(withMist) },
      now: new Date('2026-07-15T08:00:00'),
    });
    expect(tasks).toEqual([]);
  });
});

describe('feeding stops for the winter', () => {
  it('knows which months are in season', () => {
    expect(isInSeason('fertilize', new Date('2026-07-15T12:00:00'))).toBe(true);
    expect(isInSeason('fertilize', new Date('2026-03-01T12:00:00'))).toBe(true);
    expect(isInSeason('fertilize', new Date('2026-10-31T12:00:00'))).toBe(true);
    expect(isInSeason('fertilize', new Date('2026-12-15T12:00:00'))).toBe(false);
    expect(isInSeason('fertilize', new Date('2026-01-15T12:00:00'))).toBe(false);
    expect(isInSeason('fertilize', new Date('2026-02-28T12:00:00'))).toBe(false);
  });

  it('leaves watering alone all year', () => {
    expect(isInSeason('water', new Date('2026-12-15T12:00:00'))).toBe(true);
  });

  it('schedules feeding in July', () => {
    expect(plannedTypes(new Date('2026-07-15T08:00:00'))).toContain('fertilize');
  });

  it('schedules no feeding in December, but still waters', () => {
    const types = plannedTypes(new Date('2026-12-15T08:00:00'));
    expect(types).not.toContain('fertilize');
    expect(types).toContain('water');
  });

  it('drops a feeding reminder that would land out of season', () => {
    // Late October, feeding due 30 days out — that lands in November.
    const logs: Record<number, CareLog[]> = {
      1: [{ id: 1, plant_id: 1, action: 'fertilize', notes: '', logged_at: '2026-10-25T09:00:00' }],
    };
    const batches = computeReminderPlan({
      plants: [PLANT],
      logsByPlant: logs,
      speciesById: { 100: species(FEED_AND_WATER) },
      prefs: { fertilize: true },
      now: new Date('2026-10-26T08:00:00'),
    });
    expect(batches.flatMap((b) => b.items)).toEqual([]);
  });

  it('shows no winter feeding to-do', () => {
    const tasks = computeCareTasks({
      plants: [PLANT],
      logsByPlant: LOGS,
      speciesById: { 100: species(FEED_AND_WATER) },
      now: new Date('2026-12-15T08:00:00'),
    });
    expect(tasks.map((t) => t.careType)).toEqual(['water']);
  });
});
