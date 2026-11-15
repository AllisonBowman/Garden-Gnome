import { Box } from '../types/site';

// Converting between a top-down image's pixels and latitude and longitude,
// using the image's `bounds` (Imagery.bounds). The image is north up, and a
// block this small (about 500 metres across) is treated as linear in degrees,
// the same way the server cut it. Pixel (0, 0) is the north-west corner.
// Pure: no React Native imports, so ZoneMap, PropertySetup and tests share it.

export interface Point { x: number; y: number }
export interface LatLng { lat: number; lng: number }
export interface PixelRect { x: number; y: number; w: number; h: number }

function spans(bounds: Box): { lngSpan: number; latSpan: number } {
  const lngSpan = bounds.east - bounds.west;
  const latSpan = bounds.north - bounds.south;
  if (!(lngSpan > 0) || !(latSpan > 0)) {
    throw new RangeError('Image bounds must have east > west and north > south.');
  }
  return { lngSpan, latSpan };
}

/** The place under an image pixel. */
export function pixelToLatLng(
  bounds: Box, width: number, height: number, x: number, y: number,
): LatLng {
  const { lngSpan, latSpan } = spans(bounds);
  return {
    lat: bounds.north - (y / height) * latSpan,
    lng: bounds.west + (x / width) * lngSpan,
  };
}

/** The image pixel over a place. Places outside the bounds give pixels
 *  outside the image (negative, or past the width or height). */
export function latLngToPixel(
  bounds: Box, width: number, height: number, lat: number, lng: number,
): Point {
  const { lngSpan, latSpan } = spans(bounds);
  return {
    x: ((lng - bounds.west) / lngSpan) * width,
    y: ((bounds.north - lat) / latSpan) * height,
  };
}

/** A box in degrees as a pixel rectangle: top-left corner, width, height. */
export function boxToPixelRect(
  bounds: Box, width: number, height: number, box: Box,
): PixelRect {
  const nw = latLngToPixel(bounds, width, height, box.north, box.west);
  const se = latLngToPixel(bounds, width, height, box.south, box.east);
  const x = Math.min(nw.x, se.x);
  const y = Math.min(nw.y, se.y);
  return { x, y, w: Math.abs(se.x - nw.x), h: Math.abs(se.y - nw.y) };
}

/** A pixel rectangle as a box in degrees. A negative width or height (a
 *  rectangle dragged up or left) is normalised. */
export function pixelRectToBox(
  bounds: Box, width: number, height: number, rect: PixelRect,
): Box {
  const a = pixelToLatLng(bounds, width, height, rect.x, rect.y);
  const b = pixelToLatLng(bounds, width, height, rect.x + rect.w, rect.y + rect.h);
  return {
    west: Math.min(a.lng, b.lng),
    east: Math.max(a.lng, b.lng),
    south: Math.min(a.lat, b.lat),
    north: Math.max(a.lat, b.lat),
  };
}

/** Whether a place lies inside the bounds (edges included). */
export function containsLatLng(bounds: Box, lat: number, lng: number): boolean {
  return lat >= bounds.south && lat <= bounds.north && lng >= bounds.west && lng <= bounds.east;
}

/** Keep an image point on the image. */
export function clampToImage(width: number, height: number, p: Point): Point {
  return { x: Math.min(Math.max(p.x, 0), width), y: Math.min(Math.max(p.y, 0), height) };
}
