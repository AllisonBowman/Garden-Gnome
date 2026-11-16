import {
  LABEL_STYLE, brightness, mapInk, pinPoint, placeLabels, viewRect, wrapWords, yardFocus, zoneRects,
} from './mapLayout';
import { ALMANAC, OBSERVATORY } from '../theme/tokens';
import { Imagery, Zone } from '../types/site';

// A 1000 x 800 pixel image over a 0.01 x 0.008 degree block.
const imagery: Imagery = {
  tile_key: 'blk1_1_1', image_path: '/imagery/tiles/blk1_1_1.jpg', width: 1000, height: 800,
  bounds: { west: -77.01, south: 38.9, east: -77.0, north: 38.908 },
  source: { name: 'Aerial survey' },
  pin: { lat: 38.904, lng: -77.005 },
  default_footprint: { west: -77.006, south: 38.903, east: -77.004, north: 38.905 },
};

const zone = (over: Partial<Zone>): Zone => ({
  id: 1, growing_area_id: 1, property_id: 1, name: 'Front bed', vegetation_type: 'garden_bed',
  is_whole_lot: false, box: null, boundary_source: 'owner', plant_count: 0, values: [], ...over,
});

const identity = { toView: (p: { x: number; y: number }) => p };

describe('zoneRects', () => {
  test('a drawn box becomes image pixels', () => {
    const [r] = zoneRects(imagery, [zone({
      id: 5, box: { west: -77.009, south: 38.906, east: -77.008, north: 38.907 },
    })]);
    expect(r.id).toBe(5);
    expect(r.rect.x).toBeCloseTo(100);
    expect(r.rect.y).toBeCloseTo(100);
    expect(r.rect.w).toBeCloseTo(100);
    expect(r.rect.h).toBeCloseTo(100);
  });

  test('the whole lot with no box uses the approximate yard; other zones with no box are left out', () => {
    const rects = zoneRects(imagery, [
      zone({ id: 1, is_whole_lot: true, boundary_source: 'default' }),
      zone({ id: 2, box: null }),
    ]);
    expect(rects.map((r) => r.id)).toEqual([1]);
    expect(rects[0].rect.x).toBeCloseTo(400);
    expect(rects[0].rect.w).toBeCloseTo(200);
  });

  test('no approximate yard and no boxes: nothing to draw', () => {
    expect(zoneRects({ ...imagery, default_footprint: null }, [zone({ is_whole_lot: true })])).toEqual([]);
  });

  test('broken bounds place nothing rather than throwing', () => {
    const bad = { ...imagery, bounds: { west: 1, south: 1, east: 1, north: 1 } };
    expect(zoneRects(bad, [zone({ box: imagery.default_footprint })])).toEqual([]);
  });
});

describe('yardFocus', () => {
  test('centred on the approximate yard, a quarter of the image across', () => {
    const f = yardFocus(imagery)!;
    expect(f.x).toBeCloseTo(500);
    expect(f.y).toBeCloseTo(400);
    expect(f.span).toBe(250);
  });

  test('on the pin when there is no approximate yard', () => {
    const f = yardFocus({ ...imagery, default_footprint: null, pin: { lat: 38.907, lng: -77.009 } })!;
    expect(f.x).toBeCloseTo(100);
    expect(f.y).toBeCloseTo(100);
  });

  test('neither: the whole image shows', () => {
    expect(yardFocus({ ...imagery, default_footprint: null, pin: null })).toBeUndefined();
  });
});

test('viewRect turns an image rectangle into a view box through the transform', () => {
  const ctx = { toView: (p: { x: number; y: number }) => ({ x: p.x * 2 + 10, y: p.y * 2 - 5 }) };
  expect(viewRect({ x: 1, y: 2, w: 3, h: 4 }, ctx)).toEqual({ left: 12, top: -1, width: 6, height: 8 });
});

describe('pinPoint', () => {
  test('the pin in view pixels', () => {
    const p = pinPoint(imagery, identity, { width: 1000, height: 800 })!;
    expect(p.x).toBeCloseTo(500);
    expect(p.y).toBeCloseTo(400);
  });
  test('null with no pin, or when the pin is off the view', () => {
    expect(pinPoint({ ...imagery, pin: null }, identity, { width: 1000, height: 800 })).toBeNull();
    expect(pinPoint(imagery, identity, { width: 100, height: 100 })).toBeNull();
  });
});

describe('wrapWords', () => {
  test('one line when it fits, else even lines broken at spaces', () => {
    expect(wrapWords('Front bed', 20, 2)).toEqual(['Front bed']);
    expect(wrapWords('Garden bed', 7, 2)).toEqual(['Garden', 'bed']);
    expect(wrapWords('Herbs by the back door', 14, 2)).toEqual(['Herbs by the', 'back door']);
  });
  test('never inside a word: a word longer than a line, or too many lines, is null', () => {
    expect(wrapWords('Garden bed', 5, 2)).toBeNull();
    expect(wrapWords('one two three four five', 5, 2)).toBeNull();
    expect(wrapWords('   ', 10, 2)).toBeNull();
  });
});

describe('placeLabels', () => {
  const view = { width: 300, height: 200 };
  const charPx = LABEL_STYLE.fontSize * LABEL_STYLE.charWidth;
  const within = (l: { left: number; top: number; width: number; lines: number }) => {
    expect(l.left).toBeGreaterThanOrEqual(0);
    expect(l.top).toBeGreaterThanOrEqual(0);
    expect(l.left + l.width).toBeLessThanOrEqual(view.width);
    expect(l.top + l.lines * LABEL_STYLE.lineHeight).toBeLessThanOrEqual(view.height);
  };
  const noBrokenWords = (text: string, rows: string[]) => {
    expect(rows.join(' ')).toBe(text);
    const words = new Set(text.split(' '));
    for (const r of rows) for (const w of r.split(' ')) expect(words.has(w)).toBe(true);
  };

  test('a label sits inside the top-left of its box', () => {
    const [l] = placeLabels([{ id: 1, text: 'Front bed', box: { left: 20, top: 30, width: 150, height: 60 } }], view);
    expect(l).toMatchObject({ id: 1, text: 'Front bed', rows: ['Front bed'], left: 23, top: 33, lines: 1, placement: 'inside' });
    expect(l.width).toBe(Math.ceil('Front bed'.length * charPx));
  });

  test('a box partly off the view keeps its label inside the view', () => {
    const [l] = placeLabels([{ id: 1, text: 'Back lawn', box: { left: -50, top: -40, width: 200, height: 100 } }], view);
    expect(l.left).toBe(LABEL_STYLE.padding);
    expect(l.top).toBe(LABEL_STYLE.padding);
  });

  test('a long name wraps to at most two lines within the box width, at spaces', () => {
    const text = 'Approximate yard (typical lot size)';
    const [l] = placeLabels([{ id: 1, text, box: { left: 0, top: 0, width: 140, height: 100 } }], view);
    expect(l.lines).toBe(2);
    expect(l.placement).toBe('inside');
    expect(l.width).toBeLessThanOrEqual(140 - 2 * LABEL_STYLE.padding);
    noBrokenWords(text, l.rows);
  });

  test('"Garden bed" in a small box is never broken inside a word: it goes just below the box', () => {
    const box = { left: 100, top: 60, width: 36, height: 30 };
    const [l] = placeLabels([{ id: 1, text: 'Garden bed', box }], view, { pin: { x: 118, y: 75 } });
    expect(l.placement).toBe('below');
    expect(l.rows).toEqual(['Garden bed']);
    expect(l.top).toBe(box.top + box.height + LABEL_STYLE.padding);
    within(l);
  });

  test('above the box when there is no room below', () => {
    const box = { left: 100, top: 150, width: 36, height: 45 };
    const [l] = placeLabels([{ id: 1, text: 'Garden bed', box }], view);
    expect(l.placement).toBe('above');
    expect(l.top + LABEL_STYLE.lineHeight).toBeLessThanOrEqual(box.top);
    within(l);
  });

  test('an outside label near the right edge is pulled back inside the view', () => {
    const [l] = placeLabels([{ id: 1, text: 'Vegetable garden', box: { left: 280, top: 20, width: 20, height: 20 } }], view);
    expect(l.placement).toBe('below');
    within(l);
  });

  test('the label keeps off the pin when another place fits', () => {
    const box = { left: 20, top: 20, width: 150, height: 80 };
    const [l] = placeLabels([{ id: 1, text: 'Front bed', box }], view, { pin: { x: 30, y: 28 } });
    // The top left would cover the pin; the bottom left inside the box does not.
    expect(l.placement).toBe('inside');
    expect(l.top).toBe(box.top + box.height - LABEL_STYLE.padding - LABEL_STYLE.lineHeight);
  });

  test('a small box with the pin in it puts its label outside, not over the pin', () => {
    const box = { left: 100, top: 60, width: 80, height: 18 };
    const pin = { x: 110, y: 69 };
    const [l] = placeLabels([{ id: 1, text: 'Herbs', box }], view, { pin });
    expect(l.placement).toBe('below');
    const pinBox = { left: pin.x - LABEL_STYLE.pinClearance, top: pin.y - LABEL_STYLE.pinClearance };
    expect(l.top).toBeGreaterThanOrEqual(pinBox.top + 2 * LABEL_STYLE.pinClearance);
  });

  test('covering the pin is allowed when nothing else fits', () => {
    const box = { left: 0, top: 0, width: 300, height: 200 };
    const [l] = placeLabels([{ id: 1, text: 'Whole lot', box }], { width: 300, height: 200 }, { pin: { x: 150, y: 100 } });
    expect(l.placement).toBe('inside');
  });

  test('a label that fits nowhere is left off', () => {
    // A thin strip the full height of the view: no room inside, below or above.
    expect(placeLabels([{ id: 1, text: 'Herbs', box: { left: 0, top: 0, width: 12, height: 200 } }], view)).toEqual([]);
    // A word too long for any line.
    expect(placeLabels([{ id: 1, text: 'A'.repeat(40), box: { left: 0, top: 0, width: 50, height: 50 } }], view)).toEqual([]);
  });

  test('a box off the view, or a blank name, has no label', () => {
    expect(placeLabels([
      { id: 1, text: 'Away', box: { left: 400, top: 10, width: 50, height: 50 } },
      { id: 2, text: '   ', box: { left: 10, top: 10, width: 100, height: 50 } },
    ], view)).toEqual([]);
  });

  test('a label that would cover one already placed moves, or is left off', () => {
    const labels = placeLabels([
      { id: 1, text: 'Front bed', box: { left: 10, top: 10, width: 100, height: 40 } },
      { id: 2, text: 'Approximate yard', box: { left: 5, top: 8, width: 250, height: 150 } },
      { id: 3, text: 'Herbs', box: { left: 150, top: 120, width: 100, height: 40 } },
    ], view);
    expect(labels.map((l) => l.id)).toEqual([1, 2, 3]);
    const yard = labels.find((l) => l.id === 2)!;
    // Its top left is taken by Front bed, so it sits at its bottom left.
    expect(yard.top).toBe(8 + 150 - LABEL_STYLE.padding - LABEL_STYLE.lineHeight);
    // Three labels for boxes that fill the view: top left, bottom left, then
    // no place is left, so the third is left off.
    const full = { left: 0, top: 0, width: 300, height: 200 };
    const crowded = placeLabels([
      { id: 1, text: 'Front bed', box: full },
      { id: 2, text: 'Back bed', box: full },
      { id: 3, text: 'Side bed', box: full },
    ], view);
    expect(crowded.map((l) => l.id)).toEqual([1, 2]);
  });

  test('every label at phone width: inside the view, words whole, at most two lines', () => {
    const phone = { width: 313, height: 235 };
    const names = ['Garden bed', 'Front bed', 'Vegetable garden by the shed', 'Herbs', 'Approximate yard'];
    const items = names.map((text, i) => ({
      id: i + 1, text, box: { left: 20 + i * 55, top: 30 + (i % 2) * 90, width: 30 + i * 5, height: 25 },
    }));
    const placed = placeLabels(items, phone, { pin: { x: 150, y: 110 } });
    for (const l of placed) {
      expect(l.lines).toBeLessThanOrEqual(2);
      noBrokenWords(l.text, l.rows);
      expect(l.left + l.width).toBeLessThanOrEqual(phone.width);
      expect(l.top + l.lines * LABEL_STYLE.lineHeight).toBeLessThanOrEqual(phone.height);
    }
  });
});

describe('mapInk', () => {
  test('the lighter theme colour draws, the darker is the halo, in both themes', () => {
    expect(mapInk(ALMANAC)).toEqual({ line: ALMANAC.card, halo: ALMANAC.ink });
    expect(mapInk(OBSERVATORY)).toEqual({ line: OBSERVATORY.ink, halo: OBSERVATORY.card });
  });
  test('a colour that is not hex falls back to card on ink', () => {
    expect(mapInk({ card: 'white', ink: '#000000' })).toEqual({ line: 'white', halo: '#000000' });
    expect(brightness('#FFFFFF')).toBeCloseTo(1);
    expect(brightness('rgba(0,0,0,1)')).toBeNull();
  });
});
