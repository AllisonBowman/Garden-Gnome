import { Point } from './imageGeometry';

// The pan and pinch zoom of TopDownImage, as pure maths. A view point is
// `image point * scale + offset`, where scale is view pixels per image pixel.
// The image starts fitted inside the view and centred; zoom never goes below
// that fit, and the image is never panned off the view.

export interface ViewTransform { scale: number; tx: number; ty: number }
export interface Size { width: number; height: number }

/** How far in a pinch can zoom, as a multiple of the fitted scale. */
export const MAX_ZOOM = 6;

/** The fitted transform: the whole image visible, centred. */
export function fitTransform(view: Size, image: Size): ViewTransform {
  if (view.width <= 0 || view.height <= 0 || image.width <= 0 || image.height <= 0) {
    return { scale: 1, tx: 0, ty: 0 };
  }
  const scale = Math.min(view.width / image.width, view.height / image.height);
  return {
    scale,
    tx: (view.width - image.width * scale) / 2,
    ty: (view.height - image.height * scale) / 2,
  };
}

/**
 * A starting view centred on one image point, zoomed so about `span` image
 * pixels fit across the shorter side of the view. Used by the zone map so
 * the yard, not the whole 500 metre block, fills the screen at first.
 */
export function focusTransform(
  view: Size, image: Size, focus: { x: number; y: number; span: number },
): ViewTransform {
  const fit = fitTransform(view, image);
  if (view.width <= 0 || view.height <= 0 || focus.span <= 0) return fit;
  const scale = Math.min(view.width, view.height) / focus.span;
  return clampTransform({
    scale,
    tx: view.width / 2 - focus.x * scale,
    ty: view.height / 2 - focus.y * scale,
  }, view, image);
}

export function toView(t: ViewTransform, p: Point): Point {
  return { x: p.x * t.scale + t.tx, y: p.y * t.scale + t.ty };
}

export function toImage(t: ViewTransform, p: Point): Point {
  return { x: (p.x - t.tx) / t.scale, y: (p.y - t.ty) / t.scale };
}

function clampAxis(offset: number, content: number, view: number): number {
  if (content <= view) return (view - content) / 2;
  return Math.min(0, Math.max(view - content, offset));
}

/** Keep zoom between the fit and MAX_ZOOM, and the image covering the view
 *  (or centred along a side where it is smaller than the view). */
export function clampTransform(t: ViewTransform, view: Size, image: Size): ViewTransform {
  const fit = fitTransform(view, image).scale;
  const scale = Math.min(Math.max(t.scale, fit), fit * MAX_ZOOM);
  return {
    scale,
    tx: clampAxis(t.tx, image.width * scale, view.width),
    ty: clampAxis(t.ty, image.height * scale, view.height),
  };
}

/** One finger moved by (dx, dy) since the gesture began at `start`. */
export function panBy(start: ViewTransform, dx: number, dy: number, view: Size, image: Size): ViewTransform {
  return clampTransform({ scale: start.scale, tx: start.tx + dx, ty: start.ty + dy }, view, image);
}

/**
 * Two fingers: the image point that was under the first focal point stays
 * under the current one, and the scale grows with the distance between the
 * fingers.
 */
export function pinch(
  start: ViewTransform, startFocal: Point, startDistance: number,
  focal: Point, distance: number, view: Size, image: Size,
): ViewTransform {
  if (startDistance <= 0) return start;
  const anchor = toImage(start, startFocal);
  const scale = start.scale * (distance / startDistance);
  const fit = fitTransform(view, image).scale;
  const s = Math.min(Math.max(scale, fit), fit * MAX_ZOOM);
  return clampTransform({ scale: s, tx: focal.x - anchor.x * s, ty: focal.y - anchor.y * s }, view, image);
}

/** Distance and midpoint of two touches. */
export function touchPair(a: Point, b: Point): { distance: number; focal: Point } {
  return {
    distance: Math.hypot(a.x - b.x, a.y - b.y),
    focal: { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 },
  };
}

/** A touch that moved less than this many view pixels counts as a tap. */
export const TAP_SLOP = 8;

export function isTap(dx: number, dy: number, durationMs: number): boolean {
  return Math.hypot(dx, dy) < TAP_SLOP && durationMs < 500;
}
