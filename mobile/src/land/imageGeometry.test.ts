import {
  boxToPixelRect, clampToImage, containsLatLng, latLngToPixel, pixelRectToBox, pixelToLatLng,
} from './imageGeometry';
import { Box } from '../types/site';

// The National Arboretum block the server snaps to (grid.py).
const bounds: Box = { west: -76.971, south: 38.91, east: -76.965, north: 38.915 };
const W = 600;
const H = 500;

test('corners map to the bounds, north up', () => {
  expect(pixelToLatLng(bounds, W, H, 0, 0)).toEqual({ lat: 38.915, lng: -76.971 });
  const se = pixelToLatLng(bounds, W, H, W, H);
  expect(se.lat).toBeCloseTo(38.91, 9);
  expect(se.lng).toBeCloseTo(-76.965, 9);
});

test('pixel to place and back is the identity', () => {
  for (const [x, y] of [[0, 0], [123.5, 77], [W, H], [300, 250]]) {
    const ll = pixelToLatLng(bounds, W, H, x, y);
    const p = latLngToPixel(bounds, W, H, ll.lat, ll.lng);
    expect(p.x).toBeCloseTo(x, 6);
    expect(p.y).toBeCloseTo(y, 6);
  }
});

test('the arboretum landmark lands inside the image', () => {
  const p = latLngToPixel(bounds, W, H, 38.9123, -76.9681);
  expect(p.x).toBeCloseTo(290, 6);
  expect(p.y).toBeCloseTo(270, 6);
  expect(containsLatLng(bounds, 38.9123, -76.9681)).toBe(true);
  expect(containsLatLng(bounds, 30.2669, -97.7729)).toBe(false);
});

test('a box becomes a pixel rectangle and back', () => {
  const box: Box = { west: -76.97, south: 38.911, east: -76.968, north: 38.913 };
  const r = boxToPixelRect(bounds, W, H, box);
  expect(r.x).toBeCloseTo(100, 6);
  expect(r.y).toBeCloseTo(200, 6);
  expect(r.w).toBeCloseTo(200, 6);
  expect(r.h).toBeCloseTo(200, 6);
  const back = pixelRectToBox(bounds, W, H, r);
  expect(back.west).toBeCloseTo(box.west, 9);
  expect(back.east).toBeCloseTo(box.east, 9);
  expect(back.south).toBeCloseTo(box.south, 9);
  expect(back.north).toBeCloseTo(box.north, 9);
});

test('a rectangle dragged up and left still gives a proper box', () => {
  const b = pixelRectToBox(bounds, W, H, { x: 300, y: 300, w: -100, h: -100 });
  expect(b.west).toBeLessThan(b.east);
  expect(b.south).toBeLessThan(b.north);
  expect(boxToPixelRect(bounds, W, H, b).x).toBeCloseTo(200, 6);
});

test('empty bounds are refused rather than dividing by zero', () => {
  expect(() => pixelToLatLng({ ...bounds, east: bounds.west }, W, H, 1, 1)).toThrow(RangeError);
});

test('points are kept on the image', () => {
  expect(clampToImage(W, H, { x: -5, y: 900 })).toEqual({ x: 0, y: H });
});
