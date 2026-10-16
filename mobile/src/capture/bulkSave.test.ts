import { BULK_LIMIT, chunk, saveInChunks } from './bulkSave';

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
