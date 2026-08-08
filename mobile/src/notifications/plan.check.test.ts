import { computeReminderPlan } from './plan';
import { CareLog, Plant, Species } from '../types';

// Plan 1.5: the watering verb is *check*. The interval is a prior on when a
// check will probably come back positive — the notification asks for the
// finger test and makes watering conditional on what it finds. "Time to
// water" was the sentence that made people pour on damp soil.

function species(schedules: Species['care_schedules']): Species {
  return {
    id: 100, common_name: 'Fern', scientific_name: 'Testus',
    light_need: 'bright_indirect', humidity_pct_min: 40, humidity_pct_max: 60,
    temp_f_min: 60, temp_f_max: 85, soil_type: 'loam', toxic_to_pets: false,
    care_notes: '', care_schedules: schedules,
  } as Species;
}

function plant(id: number, nickname: string): Plant {
  return {
    id, plant_uuid: `p${id}`, nickname, species_id: 100,
    environment_id: 5, location: '', maturity_stage: 'mature', intake_notes: '',
  } as Plant;
}

const WATER = [
  { id: 1, species_id: 100, care_type: 'water' as const, interval_days_min: 7, interval_days_max: 10, notes: '' },
];
const FEED = [
  { id: 2, species_id: 100, care_type: 'fertilize' as const, interval_days_min: 30, interval_days_max: 60, notes: '' },
];

const NOW = new Date('2026-07-05T08:00:00');

function log(plantId: number, action: CareLog['action'], loggedAt: string): CareLog {
  return { id: 1, plant_id: plantId, action, notes: '', logged_at: loggedAt };
}

describe('the water reminder asks for a check, not a pour', () => {
  it('gives the finger test with elapsed time, watering only conditionally', () => {
    const batches = computeReminderPlan({
      plants: [plant(1, 'Ferny')],
      logsByPlant: { 1: [log(1, 'water', '2026-07-01T09:00:00')] },
      speciesById: { 100: species(WATER) },
      prefs: { water: true },
      now: NOW,
    });
    expect(batches).toHaveLength(1);
    // watered Jul 1, due Jul 8 (min 7) at the 9am slot → 7 days elapsed
    expect(batches[0].body).toBe(
      "Check Ferny — it's been 7 days. Push a finger 2 inches in; "
      + "water thoroughly only if it's dry down there.");
    expect(batches[0].body).not.toMatch(/time to water/i);
    expect(batches[0].items[0].daysSinceCare).toBe(7);
  });

  it('uses the check verb in a batched day', () => {
    const batches = computeReminderPlan({
      plants: [plant(1, 'Ferny'), plant(2, 'Mossy')],
      logsByPlant: {
        1: [log(1, 'water', '2026-07-01T09:00:00')],
        2: [log(2, 'water', '2026-07-01T09:00:00')],
      },
      speciesById: { 100: species(WATER) },
      prefs: { water: true },
      now: NOW,
    });
    expect(batches).toHaveLength(1);
    expect(batches[0].body).toContain('Ferny — check');
    expect(batches[0].body).toContain('Mossy — check');
    expect(batches[0].body).not.toMatch(/water/i);
  });

  it('leaves non-water reminders on their plain imperative', () => {
    const batches = computeReminderPlan({
      plants: [plant(1, 'Ferny')],
      logsByPlant: { 1: [log(1, 'fertilize', '2026-06-01T09:00:00')] },
      speciesById: { 100: species(FEED) },
      prefs: { fertilize: true },
      now: NOW,
    });
    expect(batches).toHaveLength(1);
    expect(batches[0].body).toBe('Time to fertilize Ferny.');
  });
});
