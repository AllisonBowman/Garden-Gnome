import { CARE_PRESENTATION, careActionLabel } from './labels';
import { CareType } from '../types';

// The app schedules checks, never actions (CONTEXT.md). A to-do row that read
// "Fertilize Ferny" was the calendar telling someone the plant was hungry —
// something no calendar can know. Every row asks for a look instead.

const TYPES = Object.keys(CARE_PRESENTATION) as CareType[];

test('every row asks for a check, never opens on the chore', () => {
  for (const type of TYPES) {
    const row = CARE_PRESENTATION[type].check('Ferny');
    expect(row).toMatch(/^(Check|See if|Look)\b/);
    expect(row).not.toMatch(/^(Water|Fertili[sz]e|Feed|Mist|Prune|Repot|Rotate|Clean)\b/);
    expect(row).toContain('Ferny');
  }
});

test('the calendar label is the icon and the check', () => {
  expect(careActionLabel('water', 'Ferny')).toBe('💧 Check Ferny');
  expect(careActionLabel('fertilize', 'Ferny')).toBe('🌿 See if Ferny wants feeding');
  expect(careActionLabel('repot', 'Ferny')).toBe('🪴 Look at Ferny’s roots');
});

test('a confirmation still says what was logged', () => {
  expect(CARE_PRESENTATION.fertilize.done).toBe('Fertilized');
  expect(CARE_PRESENTATION.water.done).toBe('Watered');
});
