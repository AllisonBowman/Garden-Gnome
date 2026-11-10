// A new plant is dated by the phone, not the server: the server's clock runs
// on UTC, so the day it would stamp is tomorrow on a California evening and
// yesterday on a Tokyo morning, and the first check counts from that day.
jest.mock('react-native', () => ({ Platform: { OS: 'ios' } }));

const posted: { url: string; body: any }[] = [];
jest.mock('./client', () => ({
  apiClient: async () => ({
    post: async (url: string, body: unknown) => {
      posted.push({ url, body });
      return { data: url === '/plants/bulk' ? { created: 0, plants: [] } : { id: 1 } };
    },
  }),
}));

import { createPlant, createPlantsBulk } from './plants';
import { localDateString } from './serverDate';

beforeEach(() => { posted.length = 0; });

test('a plant added today is sent with today’s date on this phone', async () => {
  await createPlant({ species_id: 7, nickname: 'Ferny' });
  expect(posted[0].url).toBe('/plants/');
  expect(posted[0].body).toEqual({ species_id: 7, nickname: 'Ferny', acquired_on: localDateString() });
});

test('a date the caretaker gave is kept as given', async () => {
  await createPlant({ species_id: 7, acquired_on: '2025-04-01' });
  expect(posted[0].body.acquired_on).toBe('2025-04-01');
});

test('every plant in a walked garden is dated the same way', async () => {
  await createPlantsBulk([{ species_id: 1 }, { species_id: 2, acquired_on: '2025-04-01' }]);
  expect(posted[0].url).toBe('/plants/bulk');
  expect(posted[0].body.plants.map((p: { acquired_on: string }) => p.acquired_on))
    .toEqual([localDateString(), '2025-04-01']);
});
