import { HOME_TASKS, isoWeek, pickHomeTasks, taskAnswer, taskButtons } from './homeTasks';
import type { WeekItem } from './week';

const season = (k: string, state: 'open' | 'done' = 'open'): WeekItem => ({
  kind: 'season', key: `season:${k}`, text: `Do ${k}`, lowImpactNote: null, reason: 'r', sources: [],
  eventKey: 'first_frost', state,
});
const care = (id: number, careType: 'water' | 'fertilize' | 'repot'): WeekItem => ({
  kind: 'care', key: `care:${id}:${careType}`, text: `💧 Check P${id}`, detail: 'Due today', plantId: id, careType, overdue: false,
});

test('at most three open tasks, skipped ones left out, the rest counted', () => {
  const items = [season('a'), season('b', 'done'), care(1, 'water'), season('c'), care(2, 'fertilize'), care(3, 'repot')];
  const r = pickHomeTasks(items, new Set(['season:c']));
  expect(HOME_TASKS).toBe(3);
  expect(r.shown.map((i) => i.key)).toEqual(['season:a', 'care:1:water', 'care:2:fertilize']);
  expect(r.more).toBe(1);
});

test('Done and Skip never claim a chore that was not done', () => {
  const task = ['mark_done', 'mark_not_needed'];
  expect(taskAnswer(season('a'), 'done', task)).toEqual({ kind: 'season', state: 'done' });
  expect(taskAnswer(season('a'), 'skip', task)).toEqual({ kind: 'season', state: 'not_needed' });
  // A frost event offers no "done": covering the plants must not mark the frost done.
  const frost = ['mark_happened', 'mark_not_needed'];
  expect(taskAnswer(season('a'), 'done', frost)).toEqual({ kind: 'hide' });
  expect(taskAnswer(season('a'), 'skip', frost)).toEqual({ kind: 'season', state: 'not_needed' });
  // An event Home does not know is never answered.
  expect(taskAnswer(season('a'), 'done', null)).toEqual({ kind: 'hide' });
  expect(taskAnswer(care(1, 'water'), 'done')).toEqual({ kind: 'log', outcome: 'watered' });
  expect(taskAnswer(care(1, 'water'), 'skip')).toEqual({ kind: 'log', outcome: 'checked_not_needed' });
  expect(taskAnswer(care(1, 'repot'), 'done')).toEqual({ kind: 'log', outcome: 'checked_fine' });
  expect(taskAnswer(care(1, 'fertilize'), 'skip')).toEqual({ kind: 'hide' });
});

test('a water check’s buttons say its own endings', () => {
  expect(taskButtons(care(1, 'water'))).toMatchObject({ done: 'Watered', skip: 'Still damp', doneA11y: 'Watered: Check P1' });
  expect(taskButtons(season('a'))).toMatchObject({ done: 'Done', skip: 'Skip', skipA11y: 'Skip: Do a' });
});

test('a skip lasts for the ISO week', () => {
  expect(isoWeek(new Date(2026, 10, 24))).toBe('2026-W48');
  expect(isoWeek(new Date(2027, 0, 1))).toBe('2026-W53');
});
