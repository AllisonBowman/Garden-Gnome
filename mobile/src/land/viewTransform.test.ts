import {
  MAX_ZOOM, clampTransform, fitTransform, isTap, panBy, pinch, toImage, toView, touchPair,
} from './viewTransform';

const view = { width: 300, height: 300 };
const image = { width: 600, height: 400 };

test('the image starts fitted and centred', () => {
  const t = fitTransform(view, image);
  expect(t.scale).toBe(0.5);
  expect(t.tx).toBe(0);
  expect(t.ty).toBe(50);
});

test('toView and toImage are inverses', () => {
  const t = { scale: 1.7, tx: -40, ty: 12 };
  const p = toImage(t, toView(t, { x: 123, y: 45 }));
  expect(p.x).toBeCloseTo(123, 9);
  expect(p.y).toBeCloseTo(45, 9);
});

test('panning at the fit keeps the image where it is', () => {
  const t = fitTransform(view, image);
  expect(panBy(t, 100, 100, view, image)).toEqual(t);
});

test('panning when zoomed moves the image but never off the view', () => {
  const t = clampTransform({ scale: 1, tx: -100, ty: -50 }, view, image);
  expect(panBy(t, 30, 0, view, image).tx).toBe(-70);
  expect(panBy(t, 500, 0, view, image).tx).toBe(0);
  expect(panBy(t, -5000, 0, view, image).tx).toBe(300 - 600);
});

test('a pinch keeps the point under the fingers in place', () => {
  const t = fitTransform(view, image);
  const focal = { x: 150, y: 150 };
  const under = toImage(t, focal);
  const z = pinch(t, focal, 100, focal, 200, view, image);
  expect(z.scale).toBe(1);
  const after = toImage(z, focal);
  expect(after.x).toBeCloseTo(under.x, 9);
  expect(after.y).toBeCloseTo(under.y, 9);
});

test('zoom stays between the fit and the maximum', () => {
  const t = fitTransform(view, image);
  expect(pinch(t, { x: 0, y: 0 }, 100, { x: 0, y: 0 }, 10, view, image).scale).toBe(0.5);
  expect(pinch(t, { x: 0, y: 0 }, 1, { x: 0, y: 0 }, 1000, view, image).scale).toBe(0.5 * MAX_ZOOM);
});

test('two touches give their midpoint and distance', () => {
  expect(touchPair({ x: 0, y: 0 }, { x: 6, y: 8 })).toEqual({ distance: 10, focal: { x: 3, y: 4 } });
});

test('a short, still touch is a tap; a drag is not', () => {
  expect(isTap(2, 3, 120)).toBe(true);
  expect(isTap(20, 0, 120)).toBe(false);
  expect(isTap(0, 0, 900)).toBe(false);
});

test('an empty view does not divide by zero', () => {
  expect(fitTransform({ width: 0, height: 0 }, image)).toEqual({ scale: 1, tx: 0, ty: 0 });
});

describe('focusTransform', () => {
  const { focusTransform, toView: tv } = require('./viewTransform');
  const view = { width: 300, height: 300 };
  const image = { width: 1200, height: 1200 };

  it('centres the focus point and shows about the span across', () => {
    const t = focusTransform(view, image, { x: 600, y: 600, span: 300 });
    expect(t.scale).toBeCloseTo(1);
    const c = tv(t, { x: 600, y: 600 });
    expect(c.x).toBeCloseTo(150);
    expect(c.y).toBeCloseTo(150);
  });

  it('never pans the image off the view when the focus is near an edge', () => {
    const t = focusTransform(view, image, { x: 10, y: 1190, span: 300 });
    expect(t.tx).toBeLessThanOrEqual(0);
    expect(t.ty).toBeGreaterThanOrEqual(300 - 1200 * t.scale);
  });

  it('falls back to the fit when the span is not usable', () => {
    const t = focusTransform(view, image, { x: 600, y: 600, span: 0 });
    expect(t.scale).toBeCloseTo(0.25);
  });
});
