import { mergeThisWeek, moreCareLine, weekCounts } from './week';
import { CareTask } from '../care/schedule';
import { SeasonTask, VitalsWeekItem } from '../types/site';

const task = (key: string, state: SeasonTask['state'] = 'open'): SeasonTask => ({
  task_key: key, text: `Do ${key}`, low_impact_note: null,
  reason: `Because ${key}`, sources: [{ name: 'Xerces Society' }],
  applies_to: { kind: 'lot', ids: [] }, state,
});
const item = (key: string, state?: SeasonTask['state'], event = 'ev'): VitalsWeekItem =>
  ({ event_key: event, task: task(key, state) });

const care = (id: number, status: CareTask['status'], daysUntilDue: number, nickname = `P${id}`): CareTask => ({
  plantId: id, nickname, careType: 'water', dueDate: new Date(), windowEndDate: new Date(),
  lastCareDate: null, daysUntilDue, daysPastWindow: 0, daysSinceLastCare: null, status,
});

test('open seasonal tasks come first, then due plant care, then settled tasks', () => {
  const week = mergeThisWeek(
    [item('a', 'done'), item('b'), item('c', 'not_needed'), item('d')],
    [care(1, 'due', 0), care(2, 'overdue', -3)],
  );
  expect(week.items.map((i) => i.key)).toEqual([
    'season:b', 'season:d', 'care:2:water', 'care:1:water', 'season:a', 'season:c',
  ]);
});

test('upcoming plant checks are not this week', () => {
  const week = mergeThisWeek([], [care(1, 'upcoming', 4), care(2, 'due', 0)]);
  expect(week.items.map((i) => i.key)).toEqual(['care:2:water']);
});

test('a task the server lists twice shows once', () => {
  expect(mergeThisWeek([item('a'), item('a', 'open', 'other')], []).items).toHaveLength(1);
});

test('every seasonal row keeps its reason and sources and its event', () => {
  const [row] = mergeThisWeek([item('a', 'open', 'first_frost-2026')], []).items;
  expect(row).toMatchObject({
    kind: 'season', reason: 'Because a', sources: [{ name: 'Xerces Society' }],
    eventKey: 'first_frost-2026', state: 'open',
  });
});

test('a long care backlog is cut and counted, never hidden', () => {
  const tasks = Array.from({ length: 9 }, (_, i) => care(i + 1, 'overdue', -i));
  const week = mergeThisWeek([], tasks, 6);
  expect(week.items).toHaveLength(6);
  expect(week.moreCare).toBe(3);
  expect(moreCareLine(3)).toBe('3 more plant checks are due. Plants has the full list.');
  expect(moreCareLine(0)).toBeNull();
  expect(weekCounts(week)).toEqual({ openSeason: 0, careDue: 9 });
});

test('care rows read as a check, with how long it has been', () => {
  const [row] = mergeThisWeek([], [care(1, 'due', 0, 'Ferny')]).items;
  expect(row).toMatchObject({ kind: 'care', text: '💧 Check Ferny', detail: 'Worth a check', plantId: 1 });
});
