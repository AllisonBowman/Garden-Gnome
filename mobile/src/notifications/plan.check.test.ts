import { computeReminderPlan, waterCheck } from './plan';
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
    growing_area_id: 5, location: '', maturity_stage: 'mature', intake_notes: '',
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
      "Check Ferny — it's been 7 days. Feel the soil before you water.");
    expect(batches[0].body).not.toMatch(/time to water/i);
    expect(batches[0].items[0].daysSinceCare).toBe(7);
  });

  // The old copy told every species to push a finger 2 inches in. No catalog
  // record supplied that number, and for a plant kept evenly moist it is the
  // wrong test. The check now says only what the species' own record says.
  it('never gives a depth the species record did not', () => {
    const batches = computeReminderPlan({
      plants: [plant(1, 'Ferny')],
      logsByPlant: { 1: [log(1, 'water', '2026-07-01T09:00:00')] },
      speciesById: { 100: species(WATER) },
      prefs: { water: true },
      now: NOW,
    });
    expect(batches[0].body).not.toMatch(/inch|finger/i);
  });

  it('uses the species check depth when the record has one', () => {
    const batches = computeReminderPlan({
      plants: [plant(1, 'Ferny')],
      logsByPlant: { 1: [log(1, 'water', '2026-07-01T09:00:00')] },
      speciesById: { 100: { ...species(WATER), water_check_depth_cm: 3 } },
      prefs: { water: true },
      now: NOW,
    });
    expect(batches[0].body).toBe(
      "Check Ferny — it's been 7 days. Feel the soil 3 cm down; water only if it's dry there.");
  });

  it('a keep-moist species is checked at the surface, in its sources’ words', () => {
    expect(waterCheck({ waterRegime: 'keep_moist', checkDepthCm: 2 })).toBe(
      'Its sources say keep the medium evenly moist; water if the surface feels dry.');
    expect(waterCheck({ waterRegime: 'dry_thoroughly_between' })).toBe(
      'Its sources say let the medium dry thoroughly between waterings; '
      + 'feel the soil before you water.');
    expect(waterCheck({})).toBe('Feel the soil before you water.');
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

  it('asks for a look when a feeding window opens, never "time to fertilize"', () => {
    const batches = computeReminderPlan({
      plants: [plant(1, 'Ferny')],
      logsByPlant: { 1: [log(1, 'fertilize', '2026-06-01T09:00:00')] },
      speciesById: { 100: species(FEED) },
      prefs: { fertilize: true },
      now: NOW,
    });
    expect(batches).toHaveLength(1);
    expect(batches[0].title).toBe('🪴 Time to look at Ferny');
    expect(batches[0].body).toBe(
      'Ferny has reached its feeding window. Have a look and decide whether it needs it.');
  });

  it('no reminder title or body is a chore', () => {
    const batches = computeReminderPlan({
      plants: [plant(1, 'Ferny'), plant(2, 'Mossy')],
      logsByPlant: {
        1: [log(1, 'fertilize', '2026-06-01T09:00:00'), log(1, 'water', '2026-07-01T09:00:00')],
        2: [log(2, 'water', '2026-07-01T09:00:00')],
      },
      speciesById: { 100: species([...WATER, ...FEED]) },
      prefs: { water: true, fertilize: true },
      now: NOW,
    });
    for (const b of batches) {
      expect(`${b.title} ${b.body}`)
        .not.toMatch(/needs? (some )?care|time to (water|fertili[sz]e|prune|rotate|repot)/i);
    }
    expect(batches.some((b) => /plants could use a look today/.test(b.title))).toBe(true);
  });
});

// The server dates a new plant 'YYYY-MM-DD'. Read as UTC midnight, that is
// the evening before anywhere behind UTC (this suite runs in New York), and
// the first check fired on day 6 of a 7-day schedule, saying "it's been 7
// days".
describe('a new plant’s first check counts from the day it was added here', () => {
  it('reads the date-only acquired_on as a local date', () => {
    const batches = computeReminderPlan({
      plants: [{ ...plant(1, 'Ferny'), acquired_on: '2026-07-05' }],
      logsByPlant: {},
      speciesById: { 100: species(WATER) },
      prefs: { water: true },
      now: NOW, // Jul 5, 8am
    });
    expect(batches).toHaveLength(1);
    const { date } = batches[0];
    expect([date.getMonth(), date.getDate(), date.getHours()]).toEqual([6, 12, 9]);
    expect(batches[0].items[0].daysSinceCare).toBe(7);
  });
});
