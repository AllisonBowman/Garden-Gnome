import { AxiosError, AxiosResponse, InternalAxiosRequestConfig } from 'axios';
import { BULK_LIMIT, chunk, saveFailureAlert, saveInChunks } from './bulkSave';

declare const require: (id: string) => any;
declare const __dirname: string;
const fs = require('fs');
const path = require('path');
const readSrc = (rel: string): string => fs.readFileSync(path.join(__dirname, rel), 'utf8');

const range = (n: number) => Array.from({ length: n }, (_, i) => i);

// --- the limit is the server's ------------------------------------------------

test('the batch limit is the one PlantBulkCreate enforces', () => {
  const schemas = readSrc('../../../garden-gnome/app/models/schemas.py');
  const block = schemas.slice(schemas.indexOf('class PlantBulkCreate'));
  const match = block.match(/plants: list\[PlantCreate\] = Field\(min_length=1, max_length=(\d+)\)/);
  expect(match).not.toBeNull();
  expect(Number(match![1])).toBe(BULK_LIMIT);
});

// --- chunking -------------------------------------------------------------------

test('a list is cut into batches no bigger than the limit, in order', () => {
  expect(chunk(range(5), 2)).toEqual([[0, 1], [2, 3], [4]]);
  expect(chunk(range(400), BULK_LIMIT).map((b) => b.length)).toEqual([200, 200]);
  expect(chunk(range(401), BULK_LIMIT).map((b) => b.length)).toEqual([200, 200, 1]);
  expect(chunk([], 3)).toEqual([]);
});

test('a nonsense batch size is refused rather than looping forever', () => {
  expect(() => chunk(range(3), 0)).toThrow();
  expect(() => chunk(range(3), 1.5)).toThrow();
});

// --- saving -------------------------------------------------------------------

test('a garden under the limit goes in one call, exactly as before', async () => {
  const calls: number[][] = [];
  const res = await saveInChunks(range(12), async (b) => { calls.push(b); });
  expect(calls).toEqual([range(12)]);
  expect(res).toEqual({ saved: range(12), unsaved: [], error: null });
});

test('a garden over the limit is saved in batches the server takes', async () => {
  const sizes: number[] = [];
  const res = await saveInChunks(range(450), async (b) => {
    if (b.length > BULK_LIMIT) throw new Error('422 too_long');
    sizes.push(b.length);
  });
  expect(sizes).toEqual([200, 200, 50]);
  expect(res.saved).toHaveLength(450);
  expect(res.unsaved).toEqual([]);
  expect(res.error).toBeNull();
});

test('a failed batch stops the run: what landed is saved, the rest stays', async () => {
  const offline = new Error('Network Error');
  let call = 0;
  const res = await saveInChunks(range(450), async () => {
    call += 1;
    if (call === 2) throw offline;
  });
  expect(call).toBe(2);
  expect(res.saved).toEqual(range(200));
  expect(res.unsaved).toEqual(range(450).slice(200));
  expect(res.error).toBe(offline);
});

test('a first batch that fails saves nothing and keeps everything', async () => {
  const res = await saveInChunks(range(3), async () => { throw new Error('503'); });
  expect(res.saved).toEqual([]);
  expect(res.unsaved).toEqual(range(3));
});

// --- what the caretaker is told ---------------------------------------------------

const config = { headers: {} } as InternalAxiosRequestConfig;
const answered = (status: number, data: unknown = {}) => new AxiosError(
  `Request failed with status code ${status}`, 'ERR_BAD_RESPONSE', config, null,
  { status, data, statusText: '', headers: {}, config } as AxiosResponse,
);
const unreachable = () => new AxiosError('Network Error', AxiosError.ERR_NETWORK, config);

test('a refusal never shows the server’s field names, and doesn’t promise a retry will work', () => {
  // POST /plants/bulk's own words for a stale species and a removed area.
  for (const err of [
    answered(400, { detail: 'species_id does not exist' }),
    answered(404, { detail: 'Growing area not found' }),
  ]) {
    const { title, body } = saveFailureAlert(err, 0, 3);
    expect(title).toBe('Nothing was saved');
    expect(body).not.toMatch(/species_id|not found|does not exist/i);
    expect(body).toMatch(/may have changed since you started/);
    expect(body).not.toMatch(/Try again in a moment/);
    expect(body).toMatch(/Your list is still here\./);
  }
});

test('no signal says so, and that the list is waiting', () => {
  expect(saveFailureAlert(unreachable(), 0, 4)).toEqual({
    title: 'Nothing was saved',
    body: 'PlantAdvocate couldn’t reach the server. Your list is still here. Try again in a moment.',
  });
});

test('a server that is busy or waking up is worth trying again', () => {
  expect(saveFailureAlert(answered(502), 0, 4).body)
    .toBe('The server couldn’t take them just now. Your list is still here. Try again in a moment.');
});

test('a 503’s own detail is the one server sentence shown, as a sentence', () => {
  const { body } = saveFailureAlert(answered(503, { detail: 'Saving is resting for a moment' }), 0, 2);
  expect(body).toBe('Saving is resting for a moment. Your list is still here. Try again in a moment.');
});

test('a signed-out session doesn’t claim the list is still here', () => {
  const { body } = saveFailureAlert(answered(401, { detail: 'Not authenticated' }), 0, 5);
  expect(body).not.toMatch(/still here|Not authenticated/);
  expect(body).toMatch(/signed out/);
});

test('a partial save counts what landed and agrees in number with what didn’t', () => {
  expect(saveFailureAlert(unreachable(), 200, 1)).toEqual({
    title: 'Saved 200 of 201',
    body: 'PlantAdvocate couldn’t reach the server. The other 1 is still here. Try again in a moment.',
  });
  expect(saveFailureAlert(unreachable(), 200, 50).body).toMatch(/The other 50 are still here\./);
});

test('a failure that isn’t the network isn’t blamed on it', () => {
  const { body } = saveFailureAlert(new TypeError('x is undefined'), 0, 1);
  expect(body).not.toMatch(/reach the server/);
  expect(body).toMatch(/Something went wrong/);
});
