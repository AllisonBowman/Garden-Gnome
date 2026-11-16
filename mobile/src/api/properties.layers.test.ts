// The map layers route (map and visuals spec section 4.1) against a simulated
// server, through the real client: the path it asks, and that a 404 (an older
// server, or the feature off) reads as null so the map shows the aerial image
// alone, while any other failure stays an error.
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
import { SITE_QUERY_KEYS, fetchMapLayersOrOff } from './properties';
import { MapLayers } from '../types/site';

type Reply = { status: number; data?: unknown };
let reply: (config: InternalAxiosRequestConfig) => Reply;
const seen: string[] = [];

beforeAll(() => {
  axios.defaults.adapter = async (config: InternalAxiosRequestConfig) => {
    const path = (config.url ?? '').replace(config.baseURL ?? '', '').replace(DEFAULT_BASE_URL, '');
    seen.push(`${(config.method ?? 'get').toUpperCase()} ${path}`);
    const r = reply(config);
    const response = {
      data: r.data, status: r.status, statusText: String(r.status), headers: {}, config,
    } as AxiosResponse;
    if (r.status >= 400) throw new AxiosError(`status ${r.status}`, undefined, config, undefined, response);
    return response;
  };
});

beforeEach(() => { seen.length = 0; });

const body: MapLayers = {
  property_id: 4,
  bounds: { west: -77.01, south: 38.9, east: -77.0, north: 38.91 },
  layers: [],
};

test('asks GET /properties/{id}/layers and returns the body', async () => {
  reply = () => ({ status: 200, data: body });
  await expect(fetchMapLayersOrOff(4)).resolves.toEqual(body);
  expect(seen).toEqual(['GET /properties/4/layers']);
});

test('a 404 (an older server, or the feature off) reads as null', async () => {
  reply = () => ({ status: 404, data: { detail: 'Not Found' } });
  await expect(fetchMapLayersOrOff(4)).resolves.toBeNull();
});

test('any other failure is still an error', async () => {
  reply = () => ({ status: 500 });
  await expect(fetchMapLayersOrOff(4)).rejects.toBeInstanceOf(AxiosError);
});

test('the query key sits under the property, beside imagery and zones', () => {
  expect(SITE_QUERY_KEYS.mapLayers(4)).toEqual(['properties', 4, 'mapLayers']);
});
