import { computeReminderPlan, ReminderBatch, WeatherSignal } from './plan';
import { CareLog, Plant, Species } from '../types';

const ENV_ID = 5;
const NOW = new Date('2026-07-01T08:00:00'); // before the 9am delivery slot

function species(): Species {
  return {
    id: 100, common_name: 'Fern', scientific_name: 'Testus',
    light_need: 'bright_indirect', humidity_pct_min: 40, humidity_pct_max: 60,
    temp_f_min: 60, temp_f_max: 85, soil_type: 'loam', toxic_to_pets: false,
    care_notes: '',
    care_schedules: [
      { id: 1, species_id: 100, care_type: 'water', interval_days_min: 7, interval_days_max: 10, notes: '' },
      { id: 2, species_id: 100, care_type: 'fertilize', interval_days_min: 14, interval_days_max: 21, notes: '' },
    ],
  } as Species;
}

function plant(): Plant {
  return {
    id: 1, plant_uuid: 'p', nickname: 'Ferny', species_id: 100,
    environment_id: ENV_ID, location: '', maturity_stage: 'mature', intake_notes: '',
  } as Plant;
}

// A watering log 1 day before NOW → next water due 7 days after that (well
// beyond the delivery slot, so shifts are visible and not floored).
const logs: Record<number, CareLog[]> = {
  1: [
    { id: 1, plant_id: 1, action: 'water', notes: '', logged_at: '2026-06-30T12:00:00Z' },
    { id: 2, plant_id: 1, action: 'fertilize', notes: '', logged_at: '2026-06-30T12:00:00Z' },
  ],
};

function run(weatherByEnv?: Record<number, WeatherSignal>): ReminderBatch[] {
  return computeReminderPlan({
    plants: [plant()],
    logsByPlant: logs,
    speciesById: { 100: species() },
    prefs: { water: true, fertilize: true },
    now: NOW,
    weatherByEnv,
  });
}

function dateFor(batches: ReminderBatch[], careType: string): number {
  const b = batches.find((x) => x.items.some((i) => i.careType === careType));
  if (!b) throw new Error(`no ${careType} batch`);
  return b.date.getTime();
}

const DAY = 86_400_000;

test('no weather map leaves the schedule unchanged', () => {
  const base = run();
  const withEmpty = run({});
  expect(dateFor(withEmpty, 'water')).toBe(dateFor(base, 'water'));
});

test('rain signal pushes the watering reminder later (+2 days)', () => {
  const base = dateFor(run(), 'water');
  const shifted = dateFor(run({ [ENV_ID]: { waterShiftDays: 2 } }), 'water');
  expect(shifted - base).toBe(2 * DAY);
});

test('heat signal pulls the watering reminder sooner (-1 day)', () => {
  const base = dateFor(run(), 'water');
  const shifted = dateFor(run({ [ENV_ID]: { waterShiftDays: -1 } }), 'water');
  expect(shifted - base).toBe(-1 * DAY);
});

test('the shift is clamped to ±2 days', () => {
  const base = dateFor(run(), 'water');
  const shifted = dateFor(run({ [ENV_ID]: { waterShiftDays: 9 } }), 'water');
  expect(shifted - base).toBe(2 * DAY);
});

test('only watering is shifted — fertilize is untouched', () => {
  const base = dateFor(run(), 'fertilize');
  const shifted = dateFor(run({ [ENV_ID]: { waterShiftDays: 2 } }), 'fertilize');
  expect(shifted).toBe(base);
});

test('a plant whose environment has no signal is unchanged', () => {
  const base = dateFor(run(), 'water');
  const shifted = dateFor(run({ 999: { waterShiftDays: 2 } }), 'water');
  expect(shifted).toBe(base);
});
