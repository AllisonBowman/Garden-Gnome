// The property routes against a simulated server, through the real client:
// that each call asks the route the spec names, and that "feature off" (a 404
// on GET /properties or GET /vitals) is told apart from a real failure.
jest.mock('react-native', () => ({ Platform: { OS: 'ios' } }));
jest.mock('expo-secure-store', () => {
  const values = new Map<string, string>([['pa_access_token', 'tok']]);
  return {
    getItemAsync: jest.fn(async (key: string) => values.get(key) ?? null),
    setItemAsync: jest.fn(async (key: string, value: string) => { values.set(key, value); }),
    deleteItemAsync: jest.fn(async (key: string) => { values.delete(key); }),
  };
});

import axios, { AxiosError, AxiosResponse, InternalAxiosRequestConfig } from 'axios';
import { DEFAULT_BASE_URL } from './client';
import {
  SITE_QUERY_KEYS, createProperty, deleteOverride, fetchPropertiesOrOff, fetchProperty,
  fetchVitals, fetchVitalsOrOff, isFeatureOff, lngLatToPixel, pixelToLngLat, pixelsToBox,
  putSeasonEvent, refreshHome, fetchBlockImagery,
} from './properties';

type Reply = { status: number; data?: unknown };
let reply: (config: InternalAxiosRequestConfig) => Reply;
const seen: Array<{ method: string; path: string; params?: unknown; data?: unknown }> = [];

beforeAll(() => {
  axios.defaults.adapter = async (config: InternalAxiosRequestConfig) => {
    const path = (config.url ?? '').replace(config.baseURL ?? '', '').replace(DEFAULT_BASE_URL, '');
    seen.push({
      method: (config.method ?? 'get').toUpperCase(), path, params: config.params,
      data: config.data ? JSON.parse(String(config.data)) : undefined,
    });
    const r = reply(config);
    const response = {
      data: r.data, status: r.status, statusText: String(r.status), headers: {}, config,
    } as AxiosResponse;
    if (r.status >= 400) {
      throw new AxiosError(`status ${r.status}`, undefined, config, undefined, response);
    }
    return response;
  };
});

beforeEach(() => {
  seen.length = 0;
  reply = () => ({ status: 200, data: {} });
});

test('a 404 on the list or the vitals means the feature is off, and reads as null', async () => {
  reply = () => ({ status: 404, data: { detail: 'Not Found' } });
  await expect(fetchPropertiesOrOff()).resolves.toBeNull();
  await expect(fetchVitalsOrOff()).resolves.toBeNull();
  await expect(fetchVitalsOrOff(3)).resolves.toBeNull();
  expect(seen.map((s) => `${s.method} ${s.path}`)).toEqual(['GET /properties', 'GET /vitals', 'GET /vitals']);
  expect(seen[2].params).toEqual({ property_id: 3 });
});

test('a 404 on one property is a real error, not the feature being off', async () => {
  reply = () => ({ status: 404, data: { detail: 'Property not found' } });
  const err = await fetchProperty(9).catch((e) => e);
  expect(isFeatureOff(err)).toBe(false);
});

test('a server error or no answer on the probes is still an error', async () => {
  reply = () => ({ status: 500 });
  await expect(fetchVitalsOrOff()).rejects.toBeInstanceOf(AxiosError);
  expect(isFeatureOff(new Error('network'))).toBe(false);
});

test('isFeatureOff reads the path however the URL is written', () => {
  const err = (url: string, method = 'get') => new AxiosError('x', undefined,
    { url, method, headers: {} } as InternalAxiosRequestConfig, undefined,
    { status: 404 } as AxiosResponse);
  expect(isFeatureOff(err('/properties/'))).toBe(true);
  expect(isFeatureOff(err('https://api.example.invalid/vitals?property_id=2'))).toBe(true);
  expect(isFeatureOff(err('/properties', 'post'))).toBe(false);
  expect(isFeatureOff(err('/properties/2/site-profile'))).toBe(false);
});

test('writes go to the routes the spec names, with the bodies it names', async () => {
  reply = () => ({ status: 201, data: { id: 1 } });
  await createProperty({ pin_lat: 38.9123, pin_lng: -76.9681, pin_source: 'owner_pin', lot_contents: ['lawn'] });
  await deleteOverride(1, 'sun', 4);
  await putSeasonEvent(1, 'first frost/2026', { state: 'happened', observed_on: '2026-11-10' });
  await fetchBlockImagery(30.2669, -97.7729);
  expect(seen.map((s) => `${s.method} ${s.path}`)).toEqual([
    'POST /properties',
    'DELETE /properties/1/overrides/sun',
    'PUT /properties/1/seasonal-plan/events/first%20frost%2F2026',
    'GET /imagery/block',
  ]);
  expect(seen[0].data).toEqual({ pin_lat: 38.9123, pin_lng: -76.9681, pin_source: 'owner_pin', lot_contents: ['lawn'] });
  expect(seen[1].params).toEqual({ zone_id: 4 });
  expect(seen[2].data).toEqual({ state: 'happened', observed_on: '2026-11-10' });
  expect(seen[3].params).toEqual({ lat: 30.2669, lng: -97.7729 });
});

test('vitals without a property sends no property id', async () => {
  await fetchVitals();
  expect(seen[0].params).toBeUndefined();
});

test('refreshHome marks vitals, properties and growing areas stale', async () => {
  const keys: unknown[] = [];
  await refreshHome({ invalidateQueries: async (f) => { keys.push(f.queryKey); } });
  expect(keys).toEqual([['vitals'], ['properties'], ['growingAreas'], ['growingArea']]);
  // A property's own keys sit under ['properties'], so they go too.
  expect(SITE_QUERY_KEYS.siteProfile(2).slice(0, 1)).toEqual(['properties']);
  expect(SITE_QUERY_KEYS.seasonalPlan(2).slice(0, 1)).toEqual(['properties']);
});

test('image pixels and degrees convert both ways with the bounds', () => {
  const img = { width: 512, height: 256, bounds: { west: -77, east: -76.99, south: 38.91, north: 38.915 } };
  expect(lngLatToPixel(img, -77, 38.915)).toEqual({ x: 0, y: 0 });
  const mid = pixelToLngLat(img, 256, 128);
  expect(mid.lng).toBeCloseTo(-76.995, 9);
  expect(mid.lat).toBeCloseTo(38.9125, 9);
  const back = lngLatToPixel(img, mid.lng, mid.lat);
  expect(back.x).toBeCloseTo(256, 6);
  expect(back.y).toBeCloseTo(128, 6);
  const box = pixelsToBox(img, { x: 512, y: 256 }, { x: 0, y: 0 });
  expect(box.west).toBeCloseTo(-77, 9);
  expect(box.east).toBeCloseTo(-76.99, 9);
  expect(box.south).toBeCloseTo(38.91, 9);
  expect(box.north).toBeCloseTo(38.915, 9);
});
