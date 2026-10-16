// The garden load is shared by the to-do list, the streaks and the reminder
// planner. These pin the two things that make sharing safe: callers who ask
// while a load is running get that load, and a write makes the next ask start
// over rather than join a load that began before it.
jest.mock('react-native', () => ({ Platform: { OS: 'ios' } }));

type Handler = (url: string) => Promise<unknown>;
let handler: Handler;
const calls: string[] = [];

jest.mock('./client', () => ({
  apiClient: async () => ({
    get: async (url: string) => {
      calls.push(url);
      return { data: await handler(url) };
    },
    post: async (url: string) => {
      calls.push(`POST ${url}`);
      return { data: { id: 1 } };
    },
  }),
}));

import { gardenChanged, loadGardenCareData, logCare, readablePlants } from './plants';

const PLANTS = [
  { id: 1, species_id: 10, nickname: 'Ferny' },
  { id: 2, species_id: 20, nickname: 'Sage' },
  { id: 3, species_id: 10, nickname: 'Fronds' },
];

function healthy(url: string): Promise<unknown> {
  if (url === '/plants/') return Promise.resolve(PLANTS);
  if (url.startsWith('/plants/')) return Promise.resolve([]);
  if (url.startsWith('/species/')) {
    return Promise.resolve({ id: Number(url.split('/')[2]), care_schedules: [] });
  }
  return Promise.reject(new Error(`unexpected ${url}`));
}

beforeEach(() => {
  calls.length = 0;
  handler = healthy;
  gardenChanged(); // no load from an earlier test is joined
});

test('one load: each plant’s log and each species once', async () => {
  const data = await loadGardenCareData();
  expect(calls.filter((c) => c === '/plants/')).toHaveLength(1);
  expect(calls.filter((c) => /^\/plants\/\d+\/logs$/.test(c))).toHaveLength(3);
  expect(calls.filter((c) => c.startsWith('/species/')).sort()).toEqual(['/species/10', '/species/20']);
  expect(data.unreadPlantIds).toEqual([]);
});

test('callers who ask while a load runs share it — no second fan-out', async () => {
  const [a, b, c] = await Promise.all([
    loadGardenCareData(), loadGardenCareData(), loadGardenCareData(),
  ]);
  expect(a).toBe(b);
  expect(b).toBe(c);
  expect(calls.filter((x) => x === '/plants/')).toHaveLength(1);
});

test('a write makes the next ask load fresh instead of joining the old load', async () => {
  const before = loadGardenCareData();
  await logCare(1, 'water');
  const after = loadGardenCareData();
  expect(after).not.toBe(before);
  await Promise.all([before, after]);
  expect(calls.filter((x) => x === '/plants/')).toHaveLength(2);
});

test('a finished load is not reused: the next ask reads the server again', async () => {
  await loadGardenCareData();
  await loadGardenCareData();
  expect(calls.filter((x) => x === '/plants/')).toHaveLength(2);
});

test('one unreadable log or species leaves those plants out, not the whole garden', async () => {
  handler = (url) => {
    if (url === '/plants/2/logs') return Promise.reject(new Error('timeout'));
    if (url === '/species/10') return Promise.reject(new Error('404'));
    return healthy(url);
  };
  const data = await loadGardenCareData();
  // Plant 2's log failed; plants 1 and 3 share the species that failed.
  expect(data.unreadPlantIds).toEqual([1, 2, 3]);
  expect(readablePlants(data)).toEqual([]);
});

test('only an unreadable plant list fails the load', async () => {
  handler = (url) => (url === '/plants/' ? Promise.reject(new Error('offline')) : healthy(url));
  await expect(loadGardenCareData()).rejects.toThrow('offline');
});
