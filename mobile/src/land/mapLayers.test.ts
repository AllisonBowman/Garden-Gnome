import {
  chosenChip, layerPicturePath, layerReady, layerStatusLines, layerStatusText, legendA11y, legendSteps,
  mapA11yLabel, mapChips, pictureLoadKey,
} from './mapLayers';
import { Explained, MapLayer, MapLayers } from '../types/site';

const explained: Explained = {
  display: 'Hours of direct sun', confidence: 'rough_estimate', confidence_label: 'Rough estimate',
  reason: 'From the shape of the ground and tree heights.', sources: [], provenance: 'modelled',
};

const layer = (over: Partial<MapLayer>): MapLayer => ({
  kind: 'sun', title: 'Sun', status: 'ready', status_text: null,
  image_path: '/properties/1/layers/sun.png', width: 120, height: 100,
  legend: [{ color: '#1B2A49', label: 'Under 2 hours' }, { color: '#FFD966', label: '6 hours or more' }],
  explained, notes: ['Buildings are not counted.'], ...over,
});

const layers = (list: MapLayer[]): MapLayers => ({
  property_id: 1, bounds: { west: 0, south: 0, east: 1, north: 1 }, layers: list,
});

describe('mapChips', () => {
  test('Aerial first, then the server layers in its order', () => {
    const chips = mapChips(layers([
      layer({ kind: 'sun' }), layer({ kind: 'trees', title: 'Trees' }), layer({ kind: 'water', title: 'Water' }),
    ]));
    expect(chips.map((c) => [c.key, c.label, c.enabled])).toEqual([
      ['aerial', 'Aerial', true], ['sun', 'Sun', true], ['trees', 'Trees', true], ['water', 'Water', true],
    ]);
    expect(chips.every((c) => c.a11y.length > 0)).toBe(true);
  });

  test('an older server (no layers) offers Aerial only', () => {
    expect(mapChips(null).map((c) => c.key)).toEqual(['aerial']);
    expect(mapChips(undefined).map((c) => c.key)).toEqual(['aerial']);
    expect(mapChips(layers([])).map((c) => c.key)).toEqual(['aerial']);
  });

  test('a layer not ready, or ready without a picture, cannot be switched on', () => {
    const chips = mapChips(layers([
      layer({ kind: 'sun', status: 'not_ready', image_path: null, status_text: 'The map is still being prepared.' }),
      layer({ kind: 'trees', title: 'Trees', status: 'ready', image_path: null }),
      layer({ kind: 'water', title: 'Water', status: 'unavailable', image_path: null, status_text: 'The ground data here is too coarse.' }),
    ]));
    expect(chips.map((c) => c.enabled)).toEqual([true, false, false, false]);
    expect(chips[1].a11y).toBe('Sun layer, not available yet. The map is still being prepared.');
  });

  test('unknown kinds and repeats are left out; a missing title falls back', () => {
    const chips = mapChips(layers([
      layer({ kind: 'sun', title: '' }), layer({ kind: 'sun' }), layer({ kind: 'roofs' as never }),
    ]));
    expect(chips.map((c) => [c.key, c.label])).toEqual([['aerial', 'Aerial'], ['sun', 'Sun']]);
  });
});

test('chosenChip falls back to Aerial when the wanted layer cannot be shown', () => {
  const chips = mapChips(layers([layer({ kind: 'sun' }), layer({ kind: 'trees', title: 'Trees', status: 'not_ready', image_path: null })]));
  expect(chosenChip(chips, 'sun').key).toBe('sun');
  expect(chosenChip(chips, 'trees').key).toBe('aerial');
  expect(chosenChip(chips, 'water').key).toBe('aerial');
  expect(chosenChip(chips, null).key).toBe('aerial');
});

describe('status words', () => {
  test('the server sentence first, then a stand-in by status', () => {
    expect(layerStatusText(layer({}))).toBeNull();
    expect(layerStatusText(layer({ status: 'not_ready', image_path: null, status_text: '  Still preparing. ' }))).toBe('Still preparing.');
    expect(layerStatusText(layer({ status: 'not_ready', image_path: null }))).toBe(
      'The sun map is still being prepared. Check back in a few minutes.');
    expect(layerStatusText(layer({ kind: 'water', title: 'Water', status: 'unavailable', image_path: null }))).toBe(
      'The water map is not available for this place.');
  });

  test('one line per layer that is not ready', () => {
    const chips = mapChips(layers([
      layer({ kind: 'sun' }),
      layer({ kind: 'water', title: 'Water', status: 'unavailable', image_path: null, status_text: 'Outside the United States.' }),
    ]));
    expect(layerStatusLines(chips)).toEqual(['Water: Outside the United States.']);
  });

  test('layerReady needs a size too', () => {
    expect(layerReady(layer({ width: 0 }))).toBe(false);
    expect(layerReady(null)).toBe(false);
  });
});

describe('legend', () => {
  test('only steps with a usable colour and label', () => {
    expect(legendSteps(layer({ legend: [
      { color: '#AABBCC', label: 'Shade' },
      { color: ' #aabbcc80 ', label: ' Part sun ' },
      { color: 'red', label: 'Bad colour' },
      { color: '#ABC', label: 'Short colour' },
      { color: '#112233', label: '' },
    ] }))).toEqual([{ color: '#AABBCC', label: 'Shade' }, { color: '#aabbcc80', label: 'Part sun' }]);
    expect(legendSteps(null)).toEqual([]);
  });

  test('a sentence for the legend', () => {
    expect(legendA11y(layer({}))).toBe('Sun legend, 2 colours: Under 2 hours, 6 hours or more.');
    expect(legendA11y(layer({ legend: [] }))).toBe('Sun legend: no colours were given.');
  });
});

describe('mapA11yLabel', () => {
  test('photograph, zones, pin and the layer range', () => {
    expect(mapA11yLabel({
      sourceName: 'National Agriculture Imagery Program.', zoneNames: ['Front bed', 'Back lawn'], hasPin: true, layer: layer({}),
    })).toBe('Top-down aerial image of your land, from National Agriculture Imagery Program. '
      + '2 zones outlined: Front bed, Back lawn. Your pin is marked. '
      + 'Showing the Sun layer. Colours run from Under 2 hours to 6 hours or more. The legend below lists every colour.');
  });

  test('no source, one zone, no pin, a layer that is not ready says nothing about it', () => {
    expect(mapA11yLabel({
      zoneNames: ['Front bed'], hasPin: false, layer: layer({ status: 'not_ready', image_path: null }),
    })).toBe('Top-down aerial image of your land. One zone outlined: Front bed.');
  });

  test('a layer with one legend step', () => {
    expect(mapA11yLabel({
      zoneNames: [], hasPin: false,
      layer: layer({ kind: 'water', title: 'Water', legend: [{ color: '#3366FF', label: 'Water collects here' }] }),
    })).toContain('Coloured areas show Water collects here.');
  });
});

describe('layerPicturePath and pictureLoadKey', () => {
  test('a pin moved to another block asks for a different address', () => {
    const sun = layer({});
    const before = layerPicturePath(sun, { tile_key: 'blk_10_20_naip' });
    const after = layerPicturePath(sun, { tile_key: 'blk_10_21_naip' });
    expect(before).toBe('/properties/1/layers/sun.png?tile=blk_10_20_naip');
    expect(after).not.toBe(before);
    expect(after!.startsWith(sun.image_path!)).toBe(true);
  });

  test('no picture for a layer that is not ready; the plain path with no tile key', () => {
    expect(layerPicturePath(layer({ status: 'not_ready', image_path: null }), { tile_key: 'blk_1_1' })).toBeNull();
    expect(layerPicturePath(null, { tile_key: 'blk_1_1' })).toBeNull();
    expect(layerPicturePath(layer({}), { tile_key: '' })).toBe('/properties/1/layers/sun.png');
    expect(layerPicturePath(layer({ image_path: '/p/sun.png?x=1' }), { tile_key: 'a b' })).toBe('/p/sun.png?x=1&tile=a%20b');
  });

  test('a new answer from the layers route changes the load key, so a failed picture is tried again', () => {
    const path = '/properties/1/layers/sun.png?tile=blk_1_1';
    expect(pictureLoadKey(path, 1000)).not.toBe(pictureLoadKey(path, 2000));
    expect(pictureLoadKey(path, 1000)).toBe(pictureLoadKey(path, 1000));
    expect(pictureLoadKey(null, 1000)).toBeNull();
    expect(pictureLoadKey(path)).toBe(`${path}|`);
  });
});
