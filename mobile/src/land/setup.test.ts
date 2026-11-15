import {
  LOT_CONTENT_LABELS, createBody, editPatch, inUnitedStates, lotContentChoices, metresBetween, nudge,
  pinSourceFor, readingLines, stillReading, toggleLotContent,
} from './setup';
import { LOT_CONTENTS } from '../types/site';

const arboretum = { lat: 38.9123, lng: -76.9681 };

test('every lot contents value has a plain label, in the server order', () => {
  expect(lotContentChoices().map((c) => c.value)).toEqual([...LOT_CONTENTS]);
  for (const v of LOT_CONTENTS) expect(LOT_CONTENT_LABELS[v]).toMatch(/^[A-Z][a-z ]+$/);
});

test('chips toggle and keep their order', () => {
  expect(toggleLotContent(['lawn'], 'shrubs')).toEqual(['shrubs', 'lawn']);
  expect(toggleLotContent(['shrubs', 'lawn'], 'shrubs')).toEqual(['lawn']);
});

test('the country name decides United States coverage; the outline only without one', () => {
  expect(inUnitedStates({ country: 'United States', ...arboretum })).toBe(true);
  expect(inUnitedStates({ country: 'Canada', lat: 45.4, lng: -75.7 })).toBe(false);
  expect(inUnitedStates({ country: '', lat: 30.2669, lng: -97.7729 })).toBe(true);
  expect(inUnitedStates({ country: null, lat: 51.5, lng: -0.12 })).toBe(false);
  expect(inUnitedStates({ country: 'Puerto Rico', lat: 18.4, lng: -66.1 })).toBe(true);
});

test('a nudge moves the pin about five metres', () => {
  for (const d of ['north', 'south', 'east', 'west'] as const) {
    expect(metresBetween(arboretum, nudge(arboretum, d))).toBeCloseTo(5, 1);
  }
  expect(nudge(arboretum, 'north').lat).toBeGreaterThan(arboretum.lat);
  expect(nudge(arboretum, 'west').lng).toBeLessThan(arboretum.lng);
});

test('a device position left where it was stays a device location', () => {
  expect(pinSourceFor('device', false)).toBe('device_location');
  expect(pinSourceFor('device', true)).toBe('owner_pin');
  expect(pinSourceFor('typed', false)).toBe('owner_pin');
});

test('the create body carries only the pin, its source and the chips', () => {
  const body = createBody(arboretum, 'owner_pin', ['lawn']);
  expect(body).toEqual({ pin_lat: 38.9123, pin_lng: -76.9681, pin_source: 'owner_pin', lot_contents: ['lawn'] });
  expect(Object.keys(createBody(arboretum, 'owner_pin', []))).toEqual(['pin_lat', 'pin_lng', 'pin_source']);
  const text = JSON.stringify(body);
  for (const k of ['address', 'city', 'region', 'country']) expect(text).not.toContain(k);
});

test('going back over a property sends only what changed', () => {
  const before = { pin: arboretum, lotContents: ['lawn' as const] };
  expect(editPatch(before, { pin: { ...arboretum }, lotContents: ['lawn'] })).toEqual({});
  const moved = nudge(arboretum, 'east', 20);
  expect(editPatch(before, { pin: moved, lotContents: ['lawn'] })).toEqual({ pin_lat: moved.lat, pin_lng: moved.lng });
  expect(editPatch(before, { pin: arboretum, lotContents: [] })).toEqual({ lot_contents: [] });
});

test('the reading screen says what each step is doing', () => {
  const lines = readingLines({ fast: 'ready', background: 'building' });
  expect(lines.map((l) => [l.key, l.state, l.done])).toEqual([
    ['fast', 'Done', true], ['background', 'Reading now', false],
  ]);
  expect(readingLines({ fast: 'failed', background: 'pending' })[0].state).toMatch(/try again/);
  expect(stillReading({ fast: 'ready', background: 'building' })).toBe(true);
  expect(stillReading({ fast: 'ready', background: 'partial' })).toBe(false);
  expect(stillReading(undefined)).toBe(true);
});
