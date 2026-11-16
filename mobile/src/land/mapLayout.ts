import { Box, Imagery, Zone } from '../types/site';
import { Point, boxToPixelRect, latLngToPixel } from './imageGeometry';
import { Size } from './viewTransform';

// Where things go on the land map: each zone's box in image pixels, where the
// map starts (the yard), a box in view pixels, the pin, and where each zone's
// label sits (wrapped only at spaces, inside its box or just outside it, kept
// inside the view and off the pin; a label with no room is left off, since
// the map's spoken description names every zone anyway). Shared by the zone
// map and LandMap. Pure: no React Native imports.

/** A box on the image, in image pixels (x right, y down). */
export interface ImageRect { x: number; y: number; w: number; h: number }

/** A box in view pixels, ready to be a style. */
export interface ViewBox { left: number; top: number; width: number; height: number }

export interface ZoneRect { id: number; zone: Zone; rect: ImageRect }

type ImageFrame = Pick<Imagery, 'bounds' | 'width' | 'height'> & { default_footprint?: Box | null };

/** Something that turns image pixels into view pixels (TopDownImage's
 *  overlay context, or a transform). */
export interface ToView { toView: (p: Point) => Point }

/**
 * Each zone that has a box, as an image rectangle. The whole-lot zone with no
 * box of its own uses the approximate yard (`default_footprint`). Zones with
 * no box are left out (they are still listed by name elsewhere).
 */
export function zoneRects(imagery: ImageFrame, zones: Zone[]): ZoneRect[] {
  return zones.flatMap((z) => {
    const box = z.box ?? (z.is_whole_lot ? imagery.default_footprint ?? null : null);
    if (!box) return [];
    try {
      return [{ id: z.id, zone: z, rect: boxToPixelRect(imagery.bounds, imagery.width, imagery.height, box) }];
    } catch {
      // Broken image bounds: nothing can be placed.
      return [];
    }
  });
}

/** How much of the image's width the map starts on: about 125 metres. */
export const YARD_SPAN_SHARE = 0.25;

/** Start the map on the yard: centred on the approximate yard (or else the
 *  pin), showing about a quarter of the image across. Undefined when the
 *  image has neither, so the whole image shows. */
export function yardFocus(
  imagery: ImageFrame & { pin?: { lat: number; lng: number } | null },
): { x: number; y: number; span: number } | undefined {
  const span = Math.round(imagery.width * YARD_SPAN_SHARE);
  try {
    if (imagery.default_footprint) {
      const r = boxToPixelRect(imagery.bounds, imagery.width, imagery.height, imagery.default_footprint);
      return { x: r.x + r.w / 2, y: r.y + r.h / 2, span };
    }
    if (imagery.pin) {
      const p = latLngToPixel(imagery.bounds, imagery.width, imagery.height, imagery.pin.lat, imagery.pin.lng);
      return { x: p.x, y: p.y, span };
    }
  } catch {
    // Broken image bounds: show the whole image.
  }
  return undefined;
}

/** An image rectangle in view pixels. */
export function viewRect(rect: ImageRect, ctx: ToView): ViewBox {
  const a = ctx.toView({ x: rect.x, y: rect.y });
  const b = ctx.toView({ x: rect.x + rect.w, y: rect.y + rect.h });
  return { left: a.x, top: a.y, width: b.x - a.x, height: b.y - a.y };
}

/** The pin in view pixels, or null when the image has no pin or it lies
 *  outside the view. */
export function pinPoint(
  imagery: Pick<Imagery, 'bounds' | 'width' | 'height' | 'pin'>, ctx: ToView, view: Size,
): Point | null {
  if (!imagery.pin) return null;
  let p: Point;
  try {
    p = latLngToPixel(imagery.bounds, imagery.width, imagery.height, imagery.pin.lat, imagery.pin.lng);
  } catch {
    return null;
  }
  const v = ctx.toView(p);
  if (v.x < 0 || v.y < 0 || v.x > view.width || v.y > view.height) return null;
  return v;
}

// ── Labels ───────────────────────────────────────────────────────────────────

export interface LabelStyle {
  /** Font size in view pixels. */
  fontSize: number;
  /** Line height in view pixels. */
  lineHeight: number;
  /** Average character width as a share of the font size (a safe estimate,
   *  since the text is measured only after it is drawn). */
  charWidth: number;
  /** Space between the box edge (or the view edge) and the label. */
  padding: number;
  /** The most lines a label may wrap to. */
  maxLines: number;
  /** The widest a label placed outside its box may be, in view pixels. */
  outsideWidth: number;
  /** How far around the pin a label keeps clear of, in view pixels. */
  pinClearance: number;
}

export const LABEL_STYLE: LabelStyle = {
  fontSize: 11.5, lineHeight: 14, charWidth: 0.58, padding: 3, maxLines: 2,
  outsideWidth: 150, pinClearance: 9,
};

export type LabelPlacement = 'inside' | 'below' | 'above';

export interface PlacedLabel {
  id: number;
  text: string;
  /** The text as it is drawn, one entry per line; wrapped only at spaces. */
  rows: string[];
  left: number;
  top: number;
  /** The label's estimated width (its longest row). */
  width: number;
  /** How many lines (rows.length). */
  lines: number;
  /** Inside the box, or just outside it below or above. */
  placement: LabelPlacement;
}

function overlaps(a: ViewBox, b: ViewBox): boolean {
  return a.left < b.left + b.width && b.left < a.left + a.width
    && a.top < b.top + b.height && b.top < a.top + a.height;
}

/**
 * Words wrapped into at most `maxLines` lines of at most `perLine`
 * characters, broken only at spaces, with lines as even as they can be. Null
 * when a single word is longer than a line or the words need more lines.
 */
export function wrapWords(text: string, perLine: number, maxLines: number): string[] | null {
  const words = text.trim().split(/\s+/).filter(Boolean);
  if (words.length === 0 || perLine < 1 || maxLines < 1) return null;
  const longest = Math.max(...words.map((w) => w.length));
  if (longest > perLine) return null;
  const greedy = (limit: number): string[] => {
    const rows: string[] = [];
    let row = '';
    for (const w of words) {
      if (!row) row = w;
      else if (row.length + 1 + w.length <= limit) row += ` ${w}`;
      else { rows.push(row); row = w; }
    }
    if (row) rows.push(row);
    return rows;
  };
  // The narrowest width, from the longest word up, that still fits in the
  // fewest lines this width allows: even lines rather than a long one and a
  // stub.
  const fewest = greedy(perLine).length;
  if (fewest > maxLines) return null;
  for (let limit = longest; limit <= perLine; limit++) {
    const rows = greedy(limit);
    if (rows.length <= fewest) return rows;
  }
  return greedy(perLine);
}

/**
 * Where each zone's label goes. Never broken inside a word, at most
 * `maxLines` lines, always inside the view. In order of preference:
 *
 *   1. inside the visible part of the box, at its top left (or its bottom
 *      left, when the top left would cover the pin);
 *   2. just below the box, when the name does not fit inside;
 *   3. just above it, when there is no room below.
 *
 * A placement that covers the pin is used only when no other one fits. A
 * label is left off when its box is off screen, when it fits nowhere, or
 * when every place would cover a label already placed (earlier items win, so
 * pass drawn zones before the approximate yard). The map's spoken
 * description names every zone anyway.
 */
export function placeLabels(
  items: Array<{ id: number; text: string; box: ViewBox }>,
  view: Size,
  opts: { pin?: Point | null; style?: LabelStyle } = {},
): PlacedLabel[] {
  const style = opts.style ?? LABEL_STYLE;
  const pad = style.padding;
  const charPx = style.fontSize * style.charWidth;
  const pinBox: ViewBox | null = opts.pin
    ? {
      left: opts.pin.x - style.pinClearance, top: opts.pin.y - style.pinClearance,
      width: 2 * style.pinClearance, height: 2 * style.pinClearance,
    }
    : null;
  const out: PlacedLabel[] = [];
  const taken: ViewBox[] = [];
  const perLine = (px: number) => Math.floor(px / charPx);
  const sized = (rows: string[]) => ({
    width: Math.ceil(Math.max(...rows.map((r) => r.length)) * charPx),
    height: rows.length * style.lineHeight,
  });

  for (const item of items) {
    const text = item.text.trim().replace(/\s+/g, ' ');
    if (!text) continue;
    // The visible part of the box.
    const x0 = Math.max(item.box.left, 0);
    const y0 = Math.max(item.box.top, 0);
    const x1 = Math.min(item.box.left + item.box.width, view.width);
    const y1 = Math.min(item.box.top + item.box.height, view.height);
    if (x1 <= x0 || y1 <= y0) continue;

    const candidates: Array<{ rows: string[]; box: ViewBox; placement: LabelPlacement }> = [];

    // Inside: wrapped to the visible width, as tall as the visible height.
    const inside = wrapWords(text, perLine(x1 - x0 - 2 * pad), style.maxLines);
    if (inside) {
      const { width, height } = sized(inside);
      if (height <= y1 - y0 - 2 * pad) {
        candidates.push({ rows: inside, placement: 'inside', box: { left: x0 + pad, top: y0 + pad, width, height } });
        candidates.push({ rows: inside, placement: 'inside', box: { left: x0 + pad, top: y1 - pad - height, width, height } });
      }
    }

    // Outside: as wide as the box, or up to `outsideWidth`, within the view.
    const outsideRoom = Math.min(view.width - 2 * pad, Math.max(x1 - x0, style.outsideWidth));
    const outside = wrapWords(text, perLine(outsideRoom), style.maxLines);
    if (outside) {
      const { width, height } = sized(outside);
      const left = Math.max(pad, Math.min(x0, view.width - pad - width));
      const below = item.box.top + item.box.height + pad;
      if (below + height <= view.height - pad) {
        candidates.push({ rows: outside, placement: 'below', box: { left, top: below, width, height } });
      }
      const above = item.box.top - pad - height;
      if (above >= pad) {
        candidates.push({ rows: outside, placement: 'above', box: { left, top: above, width, height } });
      }
    }

    const free = candidates.filter((c) => !taken.some((t) => overlaps(t, c.box)));
    const chosen = free.find((c) => !pinBox || !overlaps(pinBox, c.box)) ?? free[0];
    if (!chosen) continue;
    taken.push(chosen.box);
    out.push({
      id: item.id, text, rows: chosen.rows, left: chosen.box.left, top: chosen.box.top,
      width: chosen.box.width, lines: chosen.rows.length, placement: chosen.placement,
    });
  }
  return out;
}

// ── Ink on the photograph ────────────────────────────────────────────────────

/** Relative brightness of a "#RRGGBB" colour, 0 to 1, or null if not one. */
export function brightness(color: string): number | null {
  const m = /^#([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})(?:[0-9a-f]{2})?$/i.exec(color.trim());
  if (!m) return null;
  const [r, g, b] = [m[1], m[2], m[3]].map((h) => parseInt(h, 16) / 255);
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

/**
 * The colours for outlines and labels drawn over the aerial photograph, from
 * the theme's own card and ink colours: the lighter of the two for lines and
 * text, the darker for the halo that keeps them readable on light ground.
 * Both themes have one light and one dark of the pair, so this works in each.
 */
export function mapInk(palette: { card: string; ink: string }): { line: string; halo: string } {
  const c = brightness(palette.card);
  const i = brightness(palette.ink);
  if (c == null || i == null) return { line: palette.card, halo: palette.ink };
  return c >= i ? { line: palette.card, halo: palette.ink } : { line: palette.ink, halo: palette.card };
}
