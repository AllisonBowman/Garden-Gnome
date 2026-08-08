import { computeReminderPlan } from './plan';
import { computeCareTasks } from '../care/schedule';
import { CareLog, Plant, Species } from '../types';

// Plan 1.3: repotting left the interval model. Every source gives condition
// signs plus a season, never a due date — firing on day 365 regardless of
// root condition prompts over-potting and root rot. The reminder is now a
// February check-up carrying NC State's four pot-bound signs, cleared by any
// repot-family log (repotted / top-dressed / checked-fine) that calendar year.

function species(): Species {
  return {
    id: 100, common_name: 'Fern', scientific_name: 'Testus',
    light_need: 'bright_indirect', humidity_pct_min: 40, humidity_pct_max: 60,
    temp_f_min: 60, temp_f_max: 85, soil_type: 'loam', toxic_to_pets: false,
    care_notes: '',
    care_schedules: [
      { id: 1, species_id: 100, care_type: 'repot' as const, interval_days_min: 365, interval_days_max: 730, notes: '' },
    ],
  } as Species;
}

const PLANT = {
  id: 1, plant_uuid: 'p', nickname: 'Ferny', species_id: 100,
  environment_id: 5, location: '', maturity_stage: 'mature', intake_notes: '',
} as Plant;

function repotLog(loggedAt: string, outcome?: CareLog['outcome']): CareLog {
  return {
    id: 1, plant_id: 1, action: 'repot', outcome, notes: '', logged_at: loggedAt,
  };
}

function plan(now: Date, logs: CareLog[] = []) {
  return computeReminderPlan({
    plants: [PLANT],
    logsByPlant: { 1: logs },
    speciesById: { 100: species() },
    prefs: { repot: true },
    now,
  });
}

describe('the repot reminder is a February inspection, not an anniversary', () => {
  it('does not fire in July, even when the old interval says long overdue', () => {
    // Last repotted years ago — day-365 logic would have fired repeatedly.
    const batches = plan(
      new Date('2026-07-05T08:00:00'), [repotLog('2023-05-01T09:00:00')]);
    expect(batches).toHaveLength(0);
  });

  it('appears when February enters the horizon, carrying the four signs', () => {
    const batches = plan(
      new Date('2027-01-25T08:00:00'), [repotLog('2025-05-01T09:00:00')]);
    expect(batches).toHaveLength(1);
    expect(batches[0].date.getMonth()).toBe(1); // February
    expect(batches[0].date.getDate()).toBe(1);
    expect(batches[0].title).toBe("🪴 Ferny's spring check-up");
    for (const sign of [
      'roots pushing out of the pot',
      'Crown or roots showing at the surface',
      'Wilting again soon after you water',
      'growth stalled',
    ]) {
      expect(batches[0].body).toContain(sign);
    }
    expect(batches[0].body).toContain('top-dress with fresh mix');
  });

  it('fires mid-February for a plant not yet inspected this year', () => {
    const batches = plan(
      new Date('2026-02-10T08:00:00'), [repotLog('2025-03-15T09:00:00')]);
    expect(batches).toHaveLength(1);
    expect(batches[0].date.getMonth()).toBe(1);
  });

  it('stays quiet once any repot-family log exists this calendar year', () => {
    for (const outcome of ['repotted', 'top_dressed', 'checked_fine'] as const) {
      const batches = plan(
        new Date('2026-02-10T08:00:00'),
        [repotLog('2026-01-20T09:00:00', outcome)]);
      expect(batches).toHaveLength(0);
    }
  });
});

describe('the to-do list agrees with the inspection calendar', () => {
  function tasks(now: Date, logs: CareLog[] = []) {
    return computeCareTasks({
      plants: [PLANT],
      logsByPlant: { 1: logs },
      speciesById: { 100: species() },
      now,
    });
  }

  it('shows no repot task outside February', () => {
    expect(tasks(new Date('2026-07-15T14:00:00'))).toHaveLength(0);
  });

  it('shows a due — never overdue — inspection through February', () => {
    const [task] = tasks(
      new Date('2026-02-27T14:00:00'), [repotLog('2024-04-01T09:00:00')]);
    expect(task.careType).toBe('repot');
    expect(task.status).toBe('due');
  });

  it('clears for the year once the inspection is logged', () => {
    expect(tasks(
      new Date('2026-02-27T14:00:00'),
      [repotLog('2026-02-05T09:00:00', 'checked_fine')],
    )).toHaveLength(0);
  });
});
