import { computeReminderPlan, MAX_PENDING_NOTIFICATIONS } from './plan';
import { SEASONAL_RESERVE } from '../season/alerts';
import { CareLog, Plant, Species } from '../types';
import { SeasonAlert } from '../types/site';

// Seasonal alerts are an input to the one planner (decision D21): planned in
// the same pass as care reminders, so the cancel-and-replace in reminders.ts
// rebuilds them every time rather than wiping them.

const SPECIES = {
  id: 100, common_name: 'Fern', scientific_name: 'Testus',
  light_need: 'bright_indirect', humidity_pct_min: 40, humidity_pct_max: 60,
  temp_f_min: 60, temp_f_max: 85, soil_type: 'loam', toxic_to_pets: false, care_notes: '',
  care_schedules: [
    { id: 1, species_id: 100, care_type: 'water', interval_days_min: 1, interval_days_max: 2, notes: '' },
    { id: 2, species_id: 100, care_type: 'fertilize', interval_days_min: 30, interval_days_max: 60, notes: '' },
  ],
} as Species;

function plant(id: number, area: number): Plant {
  return {
    id, plant_uuid: `p${id}`, nickname: `Plant ${id}`, species_id: 100,
    growing_area_id: area, location: '', maturity_stage: 'mature', intake_notes: '',
  } as Plant;
}

const OLD_LOGS = (id: number): CareLog[] => [
  { id, plant_id: id, action: 'fertilize', notes: '', logged_at: '2026-01-01T09:00:00' },
  { id: id + 1000, plant_id: id, action: 'water', notes: '', logged_at: '2026-01-01T09:00:00' },
];

const NOW = new Date(2026, 9, 10, 10, 0); // 10 October 2026

function alertAt(key: string, d: Date): SeasonAlert {
  return {
    alert_key: key, event_key: 'first_frost_2026', title: 'Frost possible Tuesday night',
    body: 'Bring tender pots in before dark.', fire_at: d.toISOString(),
    built_from_forecast_at: new Date(2026, 9, 10, 9, 0).toISOString(),
  };
}

describe('seasonal alerts in the one planner', () => {
  it('schedules seasonal alerts with every care type off', () => {
    const batches = computeReminderPlan({
      plants: [plant(1, 5)], logsByPlant: { 1: OLD_LOGS(1) }, speciesById: { 100: SPECIES },
      prefs: {}, now: NOW,
      seasonal: { alerts: [alertAt('a1', new Date(2026, 9, 13, 15, 0))] },
    });
    expect(batches).toHaveLength(1);
    expect(batches[0]).toMatchObject({ kind: 'seasonal', identifier: 'a1', items: [] });
    expect(batches[0].body).toMatch(/Forecast as of 9 am on Saturday 10 October\.$/);
  });

  it('plans care and seasonal batches together, in time order', () => {
    const batches = computeReminderPlan({
      plants: [plant(1, 5)], logsByPlant: { 1: OLD_LOGS(1) }, speciesById: { 100: SPECIES },
      prefs: { water: true }, now: NOW, horizonDays: 5,
      seasonal: { alerts: [alertAt('a1', new Date(2026, 9, 13, 15, 0))] },
    });
    expect(batches.some((b) => b.kind === 'seasonal')).toBe(true);
    expect(batches.some((b) => b.kind === undefined)).toBe(true);
    const times = batches.map((b) => b.date.getTime());
    expect([...times].sort((a, b) => a - b)).toEqual(times);
  });

  it('is unchanged without a seasonal input', () => {
    const base = { plants: [plant(1, 5)], logsByPlant: { 1: OLD_LOGS(1) }, speciesById: { 100: SPECIES }, prefs: { water: true }, now: NOW };
    expect(computeReminderPlan({ ...base, seasonal: null })).toEqual(computeReminderPlan(base));
  });

  it('keeps the total under the iOS limit of 64, with the seasonal share reserved', () => {
    // A long horizon and many daily batches would overrun the budget alone.
    const alerts = [11, 13, 15].map((d, i) => alertAt(`a${i}`, new Date(2026, 9, d, 15, 0)));
    const batches = computeReminderPlan({
      plants: [plant(1, 5)], logsByPlant: { 1: [] }, speciesById: { 100: { ...SPECIES, care_schedules: [SPECIES.care_schedules![0]] } as Species },
      prefs: { water: true }, now: NOW, horizonDays: 200,
      seasonal: { alerts },
    });
    expect(batches.length).toBeLessThanOrEqual(MAX_PENDING_NOTIFICATIONS);
    expect(MAX_PENDING_NOTIFICATIONS).toBeLessThan(64);
    expect(batches.filter((b) => b.kind === 'seasonal')).toHaveLength(3);
    expect(SEASONAL_RESERVE).toBeLessThan(MAX_PENDING_NOTIFICATIONS);
  });
});

describe('fall hardening stops feeding checks for outdoor plants', () => {
  const input = (from: Date | null) => ({
    plants: [plant(1, 5), plant(2, 9)],
    logsByPlant: { 1: OLD_LOGS(1), 2: OLD_LOGS(2) },
    speciesById: { 100: SPECIES },
    prefs: { fertilize: true },
    now: NOW,
    outdoorFeedingStop: from ? { growingAreaIds: [5], from } : null,
  });
  const fedPlants = (batches: ReturnType<typeof computeReminderPlan>) =>
    batches.flatMap((b) => b.items.filter((i) => i.careType === 'fertilize').map((i) => i.plantId));

  it('gives a plant in a zone no feeding check once hardening has begun', () => {
    expect(fedPlants(computeReminderPlan(input(new Date(2026, 9, 1))))).toEqual([2]);
  });

  it('still feeds both before hardening begins', () => {
    expect(fedPlants(computeReminderPlan(input(new Date(2026, 11, 1)))).sort()).toEqual([1, 2]);
    expect(fedPlants(computeReminderPlan(input(null))).sort()).toEqual([1, 2]);
  });
});
