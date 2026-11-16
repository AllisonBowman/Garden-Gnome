import {
  LAYERS_FAILED_LINE, LAYERS_POLL_MS, MAP_FAILED_LINE, MAP_LOADING_LINE, ZONES_FAILED_LINE,
  landMapState, layersRefetchEvery,
} from './landMap';
import { MapLayer, MapLayers } from '../types/site';

const ok = { hasData: true, isLoading: false, isError: false };

test('everything loaded draws the map with nothing more to say', () => {
  expect(landMapState({ imagery: ok, zones: ok, layers: ok })).toEqual({ kind: 'map', line: null, notes: [] });
});

test('while the aerial image is on its way, one line', () => {
  expect(landMapState({
    imagery: { hasData: false, isLoading: true, isError: false }, zones: ok, layers: ok,
  })).toEqual({ kind: 'loading', line: MAP_LOADING_LINE, notes: [] });
});

test('an aerial image that fails is one line, whatever else loaded', () => {
  const s = landMapState({
    imagery: { hasData: false, isLoading: false, isError: true },
    zones: { hasData: false, isError: true }, layers: { hasData: false, isError: true },
  });
  expect(s).toEqual({ kind: 'failed', line: MAP_FAILED_LINE, notes: [] });
});

test('a refresh that fails after a first load keeps the map', () => {
  expect(landMapState({
    imagery: { hasData: true, isLoading: false, isError: true }, zones: ok, layers: ok,
  }).kind).toBe('map');
});

test('zones or layers that fail leave the photograph with a line each', () => {
  const s = landMapState({
    imagery: ok, zones: { hasData: false, isError: true }, layers: { hasData: false, isError: true },
  });
  expect(s.kind).toBe('map');
  expect(s.notes).toEqual([ZONES_FAILED_LINE, LAYERS_FAILED_LINE]);
});

test('the lines are plain: no em dashes', () => {
  for (const l of [MAP_LOADING_LINE, MAP_FAILED_LINE, ZONES_FAILED_LINE, LAYERS_FAILED_LINE]) {
    expect(l).not.toContain('—');
  }
});

const layer = (kind: MapLayer['kind'], status: MapLayer['status']): MapLayer => ({
  kind, title: kind, status, status_text: null, image_path: status === 'ready' ? `/x/${kind}.png` : null,
  width: 10, height: 10, legend: [], notes: [],
  explained: {
    display: '', confidence: 'rough_estimate', confidence_label: 'Rough estimate',
    reason: '', sources: [], provenance: 'modelled',
  },
});
const layers = (...ls: MapLayer[]): MapLayers => ({
  property_id: 1, bounds: { west: 0, south: 0, east: 1, north: 1 }, layers: ls,
});

test('layers are asked for again only while one is still being prepared', () => {
  expect(layersRefetchEvery(undefined)).toBe(false);
  expect(layersRefetchEvery(null)).toBe(false);
  expect(layersRefetchEvery(layers(layer('sun', 'ready'), layer('water', 'unavailable')))).toBe(false);
  expect(layersRefetchEvery(layers(layer('sun', 'ready'), layer('trees', 'not_ready')))).toBe(LAYERS_POLL_MS);
});
