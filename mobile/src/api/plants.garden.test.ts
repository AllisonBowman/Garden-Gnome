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

import {
  GardenLoadAbandoned, forgetGardenLoad, gardenChanged, loadGardenCareData, logCare,
  readablePlants,
} from './plants';
import { dropSessionData } from './sessionData';

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

// --- a session that ends takes its load with it -------------------------------
// One phone, two accounts: A signs out while A's garden is still loading
// (a large garden, a server waking up) and B signs in. B must not join A's
// load, and nothing still waiting on A's load may act on A's garden.

function slowPlantList(): { release: (plants: unknown) => void } {
  let release!: (plants: unknown) => void;
  const pending = new Promise((resolve) => { release = resolve; });
  handler = (url) => (url === '/plants/' ? pending : healthy(url));
  return { release };
}

test('after a session ends, the next ask starts its own load instead of joining the last one', async () => {
  const a = slowPlantList();
  const accountA = loadGardenCareData();

  forgetGardenLoad(); // A signs out
  handler = (url) => (url === '/plants/'
    ? Promise.resolve([{ id: 9, species_id: 10, nickname: 'B’s basil' }])
    : healthy(url));
  const accountB = loadGardenCareData();

  expect(accountB).not.toBe(accountA);
  expect((await accountB).plants.map((p) => p.nickname)).toEqual(['B’s basil']);
  a.release(PLANTS);
  await expect(accountA).rejects.toBeInstanceOf(GardenLoadAbandoned);
});

test('whoever was still waiting on the ended session’s load gets nothing to act on', async () => {
  const a = slowPlantList();
  const waiting = loadGardenCareData(); // say, a reminder reschedule
  forgetGardenLoad();
  a.release(PLANTS);
  await expect(waiting).rejects.toBeInstanceOf(GardenLoadAbandoned);
});

test('a load that finished before the session ended was already let go', async () => {
  await loadGardenCareData();
  forgetGardenLoad();
  await expect(loadGardenCareData()).resolves.toMatchObject({ unreadPlantIds: [] });
  expect(calls.filter((x) => x === '/plants/')).toHaveLength(2);
});

test('ending a session clears the query cache and the garden load together', async () => {
  const { QueryClient } = jest.requireActual('@tanstack/query-core');
  const queryClient = new QueryClient();
  queryClient.setQueryData(['plants'], PLANTS);
  const a = slowPlantList();
  const accountA = loadGardenCareData();

  dropSessionData(queryClient);

  expect(queryClient.getQueryData(['plants'])).toBeUndefined();
  handler = healthy;
  const next = loadGardenCareData();
  expect(next).not.toBe(accountA);
  a.release(PLANTS);
  await expect(accountA).rejects.toBeInstanceOf(GardenLoadAbandoned);
  await next;
});

test('only an unreadable plant list fails the load', async () => {
  handler = (url) => (url === '/plants/' ? Promise.reject(new Error('offline')) : healthy(url));
  await expect(loadGardenCareData()).rejects.toThrow('offline');
});
