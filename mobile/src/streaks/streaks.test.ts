import { computeStreak, GRACE_DAYS } from './streaks';
import { CareLog, Plant, Species } from '../types';

const DAY = 86_400_000;

function species(maxDays = 10): Species {
  return {
    id: 100, common_name: 'Fern', scientific_name: 'Testus',
    light_need: 'bright_indirect', humidity_pct_min: 40, humidity_pct_max: 60,
    temp_f_min: 60, temp_f_max: 85, soil_type: 'loam', toxic_to_pets: false,
    care_notes: '',
    care_schedules: [{
      id: 1, species_id: 100, care_type: 'water',
      interval_days_min: 7, interval_days_max: maxDays, notes: '',
    }],
  } as Species;
}

function plant(id: number, acquired: string): Plant {
  return {
    id, plant_uuid: `p${id}`, nickname: `Plant ${id}`, species_id: 100,
    environment_id: 1, location: '', maturity_stage: 'mature',
    intake_notes: '', acquired_on: acquired,
  } as Plant;
}

function wateredOn(plantId: number, iso: string): CareLog {
  return {
    id: plantId * 1000, plant_id: plantId, action: 'water',
    notes: '', logged_at: iso,
  } as CareLog;
}

const speciesById = { 100: species() };

describe('computeStreak', () => {
  it('counts consecutive days where nothing was left behind', () => {
    const now = new Date('2026-07-15T12:00:00');
    const result = computeStreak({
      plants: [plant(1, '2026-07-10')],
      logsByPlant: { 1: [wateredOn(1, '2026-07-14T09:00:00')] },
      speciesById,
      now,
    });
    expect(result.current).toBeGreaterThan(0);
    expect(result.behindCount).toBe(0);
    expect(result.onTrackPct).toBe(100);
  });

  it('zeroes the streak when a plant is past its window plus grace', () => {
    const now = new Date('2026-07-31T12:00:00');
    // Acquired 30 days back, never watered: well past 10 + GRACE_DAYS.
    const result = computeStreak({
      plants: [plant(1, '2026-07-01')],
      logsByPlant: { 1: [] },
      speciesById,
      now,
    });
    expect(result.current).toBe(0);
    expect(result.behindCount).toBe(1);
    expect(result.onTrackPct).toBe(0);
  });

  // The number that has to keep working at garden scale. The streak is an AND
  // across every planting, so one late tomato zeroes it — which is fine advice
  // for five pots and useless for three hundred.
  it('reports a proportion so a large garden can still see where it stands', () => {
    const now = new Date('2026-07-31T12:00:00');
    const plants = [];
    const logsByPlant: Record<number, CareLog[]> = {};
    // 9 watered yesterday, 1 not watered for a month.
    for (let i = 1; i <= 9; i++) {
      plants.push(plant(i, '2026-07-01'));
      logsByPlant[i] = [wateredOn(i, '2026-07-30T09:00:00')];
    }
    plants.push(plant(10, '2026-07-01'));
    logsByPlant[10] = [];

    const result = computeStreak({ plants, logsByPlant, speciesById, now });

    expect(result.trackedCount).toBe(10);
    expect(result.behindCount).toBe(1);
    expect(result.onTrackPct).toBe(90);
    // The strict streak still says zero — one plant IS behind. The proportion
    // is what stops that reading as "you have failed entirely".
    expect(result.current).toBe(0);
  });

  it('treats a household with no schedules as fully on track, not as failing', () => {
    const result = computeStreak({
      plants: [], logsByPlant: {}, speciesById, now: new Date('2026-07-15T12:00:00'),
    });
    expect(result.onTrackPct).toBe(100);
    expect(result.trackedCount).toBe(0);
  });

  // Regression: the walk used to advance by a fixed 86,400,000ms and then test
  // `d === today` for an exact match. Crossing a daylight-saving boundary
  // shifts the cursor an hour off local midnight, the equality never lands,
  // and `current` silently returned 0 no matter how well-tended the garden
  // was. Any history spanning a time change hit this.
  it('survives a daylight-saving boundary in the walked range', () => {
    // US DST ends 2026-11-01; walk a range that straddles it.
    const now = new Date('2026-11-10T12:00:00');
    const logs: CareLog[] = [];
    // Water every 5 days from mid-October through today, so the plant is
    // never behind and the streak should be unbroken across the boundary.
    for (let d = new Date('2026-10-15T09:00:00'); d <= now; d.setDate(d.getDate() + 5)) {
      logs.push(wateredOn(1, new Date(d).toISOString()));
    }

    const result = computeStreak({
      plants: [plant(1, '2026-10-15')],
      logsByPlant: { 1: logs },
      speciesById,
      now,
    });

    expect(result.behindCount).toBe(0);
    expect(result.current).toBeGreaterThan(0);
  });

  it('is forgiving until grace days are used up', () => {
    const now = new Date('2026-07-31T12:00:00');
    // Watered exactly maxDays + GRACE_DAYS ago — the last day still in credit.
    const lastWater = new Date(now.getTime() - (10 + GRACE_DAYS) * DAY);
    const result = computeStreak({
      plants: [plant(1, '2026-07-01')],
      logsByPlant: { 1: [wateredOn(1, lastWater.toISOString())] },
      speciesById,
      now,
    });
    expect(result.behindCount).toBe(0);
  });
});
