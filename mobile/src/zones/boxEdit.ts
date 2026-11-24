// Stretching and adjusting a zone's box on the top-down image, in image
// pixels (x to the right, y down). Converting to and from degrees is
// land/imageGeometry.ts's job. Pure.

import { t } from '../i18n';

export interface Point { x: number; y: number }
export interface Rect { x: number; y: number; w: number; h: number }

export type Handle = 'nw' | 'ne' | 'sw' | 'se';

export const HANDLES: Handle[] = ['nw', 'ne', 'sw', 'se'];

export const HANDLE_NAMES: Record<Handle, string> = {
  nw: t('zones.handles.nw'), ne: t('zones.handles.ne'), sw: t('zones.handles.sw'), se: t('zones.handles.se'),
};

/** The smallest box the tool keeps, in image pixels. A tap that barely
 *  moves is not a box. */
export const MIN_BOX_PX = 8;

function clamp(v: number, lo: number, hi: number): number {
  return Math.max(lo, Math.min(hi, v));
}

/** The box between two corners, in either order, kept inside the image. */
export function rectFromCorners(a: Point, b: Point, width: number, height: number): Rect {
  const x0 = clamp(Math.min(a.x, b.x), 0, width);
  const x1 = clamp(Math.max(a.x, b.x), 0, width);
  const y0 = clamp(Math.min(a.y, b.y), 0, height);
  const y1 = clamp(Math.max(a.y, b.y), 0, height);
  return { x: x0, y: y0, w: x1 - x0, h: y1 - y0 };
}

export function isUsableRect(r: Rect | null | undefined, min = MIN_BOX_PX): r is Rect {
  return !!r && r.w >= min && r.h >= min;
}

export function handlePoint(r: Rect, h: Handle): Point {
  return {
    x: h === 'nw' || h === 'sw' ? r.x : r.x + r.w,
    y: h === 'nw' || h === 'ne' ? r.y : r.y + r.h,
  };
}

function opposite(h: Handle): Handle {
  return ({ nw: 'se', se: 'nw', ne: 'sw', sw: 'ne' } as const)[h];
}

/** Drag one corner handle to `p`; the opposite corner stays put. The box
 *  never shrinks below `min` and never leaves the image. */
export function moveHandle(
  r: Rect, h: Handle, p: Point, width: number, height: number, min = MIN_BOX_PX,
): Rect {
  const fixed = handlePoint(r, opposite(h));
  const west = h === 'nw' || h === 'sw';
  const north = h === 'nw' || h === 'ne';
  let x = clamp(p.x, 0, width);
  let y = clamp(p.y, 0, height);
  x = west ? Math.min(x, fixed.x - min) : Math.max(x, fixed.x + min);
  y = north ? Math.min(y, fixed.y - min) : Math.max(y, fixed.y + min);
  return rectFromCorners(fixed, { x, y }, width, height);
}

/** Move the whole box by (dx, dy), stopping at the image's edges. */
export function moveRect(r: Rect, dx: number, dy: number, width: number, height: number): Rect {
  return {
    x: clamp(r.x + dx, 0, Math.max(0, width - r.w)),
    y: clamp(r.y + dy, 0, Math.max(0, height - r.h)),
    w: r.w,
    h: r.h,
  };
}

/** Which handle, if any, is within `radius` pixels of `p`. */
export function hitHandle(r: Rect, p: Point, radius: number): Handle | null {
  let best: Handle | null = null;
  let bestD = radius;
  for (const h of HANDLES) {
    const q = handlePoint(r, h);
    const d = Math.hypot(q.x - p.x, q.y - p.y);
    if (d <= bestD) { best = h; bestD = d; }
  }
  return best;
}

export function contains(r: Rect, p: Point): boolean {
  return p.x >= r.x && p.x <= r.x + r.w && p.y >= r.y && p.y <= r.y + r.h;
}

/** The zone a tap lands on: the smallest box holding the point, so a bed
 *  drawn inside a bigger area can still be picked. */
export function hitZone<T extends { id: number; rect: Rect }>(zones: T[], p: Point): T | null {
  let best: T | null = null;
  for (const z of zones) {
    if (!contains(z.rect, p)) continue;
    if (!best || z.rect.w * z.rect.h < best.rect.w * best.rect.h) best = z;
  }
  return best;
}

/** Grow or shrink a box about its centre by `factor`, inside the image: the
 *  buttons that adjust a box without dragging. */
export function scaleRect(r: Rect, factor: number, width: number, height: number, min = MIN_BOX_PX): Rect {
  const cx = r.x + r.w / 2;
  const cy = r.y + r.h / 2;
  const w = clamp(r.w * factor, min, width);
  const h = clamp(r.h * factor, min, height);
  return moveRect({ x: cx - w / 2, y: cy - h / 2, w, h }, 0, 0, width, height);
}
