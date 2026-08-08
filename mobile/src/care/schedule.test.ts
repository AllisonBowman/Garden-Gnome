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
  // The window is the recommendation. A "water every 7–10 days" plant is doing
  // exactly what the catalog says on day 10, and calling that overdue pushed
  // people to water early — the direction that actually kills houseplants.
  it('does not call a plant late while it is still inside its care window', () => {
    const logs = { 1: [{ id: 1, plant_id: 1, action: 'water' as const, notes: '', logged_at: '2026-07-05T09:00:00' }] };
    const [task] = run({ logsByPlant: logs });
    // watered Jul 5; window Jul 12–15; today is Jul 15, the far end of it
    expect(task.status).toBe('due');
    expect(task.daysPastWindow).toBe(0);
    expect(careTaskDueLabel(task)).toBe('Last done 10 days ago');
  });

  it('calls a plant late only once the window has closed and the grace has passed', () => {
    // watered Jun 30 → window Jul 7–10; today Jul 15 is 5 days past, over the
    // 3-day grace the streak already allows. The STATUS is overdue (sorting,
    // warning colour) but the COPY stays elapsed time — a count-up from "you
    // failed" nagged people into watering damp soil.
    const logs = { 1: [{ id: 1, plant_id: 1, action: 'water' as const, notes: '', logged_at: '2026-06-30T09:00:00' }] };
    const [task] = run({ logsByPlant: logs });
    expect(task.status).toBe('overdue');
    expect(task.daysPastWindow).toBe(5);
    expect(careTaskDueLabel(task)).toBe('Last done 15 days ago');
  });

  it('agrees with the streak: inside the window plus grace is not behind', () => {
    // watered Jul 4 → window Jul 11–14; today Jul 15 is 1 day past, inside grace
    const logs = { 1: [{ id: 1, plant_id: 1, action: 'water' as const, notes: '', logged_at: '2026-07-04T09:00:00' }] };
    const [task] = run({ logsByPlant: logs });
    expect(task.status).not.toBe('overdue');
  });

  it('marks a plant entering its window as due', () => {
    const logs = { 1: [{ id: 1, plant_id: 1, action: 'water' as const, notes: '', logged_at: '2026-07-08T06:00:00' }] };
    const [task] = run({ logsByPlant: logs });
    // watered Jul 8, window opens Jul 15 = today, even though NOW is 2pm
    expect(task.status).toBe('due');
    expect(task.daysUntilDue).toBe(0);
    expect(careTaskDueLabel(task)).toBe('Last done 7 days ago');
  });

  it('marks a recently watered plant as upcoming', () => {
    const logs = { 1: [{ id: 1, plant_id: 1, action: 'water' as const, notes: '', logged_at: '2026-07-14T09:00:00' }] };
    const [task] = run({ logsByPlant: logs });
    // watered Jul 14, window opens Jul 21 → 6 days out
    expect(task.status).toBe('upcoming');
    expect(task.daysUntilDue).toBe(6);
    expect(careTaskDueLabel(task)).toBe('Check in 6 days');
  });

  it('falls back to acquired_on when there is no care history', () => {
    const [task] = run({ plants: [plant({ acquired_on: '2026-07-01T00:00:00' })] });
    // acquired Jul 1; window Jul 8–11; today Jul 15 is 4 days past → overdue
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
