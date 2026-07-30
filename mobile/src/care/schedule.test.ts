import { computeCareTasks, careTaskDueLabel, CareTask } from './schedule';
import { CareLog, Plant, Species } from '../types';

const NOW = new Date('2026-07-15T14:00:00'); // mid-afternoon, local

function species(schedules: Species['care_schedules']): Species {
  return {
    id: 100, common_name: 'Fern', scientific_name: 'Testus',
    light_need: 'bright_indirect', humidity_pct_min: 40, humidity_pct_max: 60,
    temp_f_min: 60, temp_f_max: 85, soil_type: 'loam', toxic_to_pets: false,
    care_notes: '', care_schedules: schedules,
  } as Species;
}

function plant(over: Partial<Plant> = {}): Plant {
  return {
    id: 1, plant_uuid: 'p', nickname: 'Ferny', species_id: 100,
    environment_id: 5, location: '', maturity_stage: 'mature', intake_notes: '',
    ...over,
  } as Plant;
}

const waterEvery7 = [
  { id: 1, species_id: 100, care_type: 'water' as const, interval_days_min: 7, interval_days_max: 10, notes: '' },
];

function run(over: {
  plants?: Plant[];
  logsByPlant?: Record<number, CareLog[]>;
  speciesById?: Record<number, Species>;
} = {}): CareTask[] {
  return computeCareTasks({
    plants: over.plants ?? [plant()],
    logsByPlant: over.logsByPlant ?? {},
    speciesById: over.speciesById ?? { 100: species(waterEvery7) },
    now: NOW,
  });
}

describe('computeCareTasks', () => {
  it('marks a plant watered 10 days ago as overdue by the right count', () => {
    const logs = { 1: [{ id: 1, plant_id: 1, action: 'water' as const, notes: '', logged_at: '2026-07-05T09:00:00' }] };
    const [task] = run({ logsByPlant: logs });
    // watered Jul 5, due Jul 12 (min 7), today Jul 15 → 3 days overdue
    expect(task.status).toBe('overdue');
    expect(task.daysUntilDue).toBe(-3);
    expect(careTaskDueLabel(task)).toBe('3 days overdue');
  });

  it('marks a plant due exactly today as due (not overdue) all day', () => {
    const logs = { 1: [{ id: 1, plant_id: 1, action: 'water' as const, notes: '', logged_at: '2026-07-08T06:00:00' }] };
    const [task] = run({ logsByPlant: logs });
    // watered Jul 8, due Jul 15 = today, even though NOW is 2pm
    expect(task.status).toBe('due');
    expect(task.daysUntilDue).toBe(0);
    expect(careTaskDueLabel(task)).toBe('Due today');
  });

  it('marks a recently watered plant as upcoming', () => {
    const logs = { 1: [{ id: 1, plant_id: 1, action: 'water' as const, notes: '', logged_at: '2026-07-14T09:00:00' }] };
    const [task] = run({ logsByPlant: logs });
    // watered Jul 14, due Jul 21 → 6 days out
    expect(task.status).toBe('upcoming');
    expect(task.daysUntilDue).toBe(6);
    expect(careTaskDueLabel(task)).toBe('Due in 6 days');
  });

  it('falls back to acquired_on when there is no care history', () => {
    const [task] = run({ plants: [plant({ acquired_on: '2026-07-01T00:00:00' })] });
    // acquired Jul 1, due Jul 8 → overdue by 7, and no lastCareDate
    expect(task.status).toBe('overdue');
    expect(task.daysUntilDue).toBe(-7);
    expect(task.lastCareDate).toBeNull();
  });

  it('falls back to now (never immediately overdue) when there is no history and no acquired date', () => {
    const [task] = run(); // no logs, no acquired_on
    expect(task.status).toBe('upcoming');
    expect(task.daysUntilDue).toBe(7); // due 7 days from today
  });

  it('emits one task per scheduled care-type, soonest first', () => {
    const schedules = [
      { id: 1, species_id: 100, care_type: 'water' as const, interval_days_min: 7, interval_days_max: 10, notes: '' },
      { id: 2, species_id: 100, care_type: 'fertilize' as const, interval_days_min: 30, interval_days_max: 45, notes: '' },
    ];
    const tasks = run({ speciesById: { 100: species(schedules) } });
    expect(tasks.map((t) => t.careType)).toEqual(['water', 'fertilize']);
  });

  it('ignores plants whose species has no loaded schedules', () => {
    expect(run({ speciesById: { 100: species(undefined) } })).toEqual([]);
  });

  it('scopes nothing itself — every task carries its environmentId for the caller to filter', () => {
    const [task] = run();
    expect(task.environmentId).toBe(5);
  });
});
