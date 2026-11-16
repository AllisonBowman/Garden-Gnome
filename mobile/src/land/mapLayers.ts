import { LegendStep, MapLayer, MapLayerKind, MapLayers } from '../types/site';

// The land map's layer chips and the words around them (map and visuals spec
// sections 1 and 4.2): Aerial first (nothing drawn over the photograph),
// then the server's layers in the order it sends them. Only a layer the
// server has ready can be switched on; the others say why in a sentence.
// The legend's colours are the server's own, so the picture and its legend
// cannot disagree. Pure: no React Native imports.

export type MapChipKey = 'aerial' | MapLayerKind;

export interface MapChip {
  key: MapChipKey;
  label: string;
  /** Whether it can be switched on now. Aerial always can. */
  enabled: boolean;
  /** The layer behind the chip (null for Aerial). */
  layer: MapLayer | null;
  /** What a screen reader hears for the chip. */
  a11y: string;
}

export const AERIAL_LABEL = 'Aerial';

const KNOWN_KINDS: MapLayerKind[] = ['sun', 'trees', 'water'];

const FALLBACK_TITLES: Record<MapLayerKind, string> = { sun: 'Sun', trees: 'Trees', water: 'Water' };

/** Whether a layer can be drawn now: ready, with a picture to load. */
export function layerReady(layer: MapLayer | null | undefined): boolean {
  return !!layer && layer.status === 'ready' && !!layer.image_path && layer.width > 0 && layer.height > 0;
}

function titleOf(layer: MapLayer): string {
  return layer.title?.trim() || FALLBACK_TITLES[layer.kind] || layer.kind;
}

/**
 * The status sentence for a layer that is not ready, or null for one that
 * is. The server's own words come first; these stand in if it sends none.
 */
export function layerStatusText(layer: MapLayer): string | null {
  if (layerReady(layer)) return null;
  const own = layer.status_text?.trim();
  if (own) return own;
  if (layer.status === 'unavailable') return `The ${titleOf(layer).toLowerCase()} map is not available for this place.`;
  return `The ${titleOf(layer).toLowerCase()} map is still being prepared. Check back in a few minutes.`;
}

/**
 * The chips, Aerial first. With no layers (an older server, or the route
 * answered 404) only Aerial is offered. Kinds this app does not know and
 * repeats are left out.
 */
export function mapChips(layers: MapLayers | null | undefined): MapChip[] {
  const chips: MapChip[] = [{
    key: 'aerial', label: AERIAL_LABEL, enabled: true, layer: null,
    a11y: 'Aerial. The photograph alone, with nothing drawn over it.',
  }];
  const seen = new Set<MapLayerKind>();
  for (const layer of layers?.layers ?? []) {
    if (!KNOWN_KINDS.includes(layer.kind) || seen.has(layer.kind)) continue;
    seen.add(layer.kind);
    const label = titleOf(layer);
    const enabled = layerReady(layer);
    chips.push({
      key: layer.kind, label, enabled, layer,
      a11y: enabled ? `${label} layer. Draws ${label.toLowerCase()} over the photograph.`
        : `${label} layer, not available yet. ${layerStatusText(layer)}`,
    });
  }
  return chips;
}

/** The chip to show as chosen: the one asked for when it can be switched on,
 *  else Aerial (a layer that stopped being ready falls back by itself). */
export function chosenChip(chips: MapChip[], wanted: MapChipKey | null | undefined): MapChip {
  return chips.find((c) => c.key === wanted && c.enabled) ?? chips[0];
}

/** One line per layer that cannot be switched on yet, for under the chips. */
export function layerStatusLines(chips: MapChip[]): string[] {
  return chips.filter((c) => !c.enabled && c.layer).map((c) => `${c.label}: ${layerStatusText(c.layer!)}`);
}

/**
 * Where to load a ready layer's picture from: the server's path with the
 * aerial image's tile key added. The server's path is the same for every
 * block, so after the pin moves to another block this gives a new address
 * (and a new HTTP cache entry) instead of the old block's picture. The
 * server ignores the added query. Null when the layer is not ready.
 */
export function layerPicturePath(
  layer: MapLayer | null | undefined, imagery: { tile_key?: string | null },
): string | null {
  if (!layerReady(layer)) return null;
  const path = layer!.image_path!;
  const tile = imagery.tile_key?.trim();
  if (!tile) return path;
  return `${path}${path.includes('?') ? '&' : '?'}tile=${encodeURIComponent(tile)}`;
}

/**
 * What a picture's load is keyed on: its address and the answer it came
 * with (a query's dataUpdatedAt). A new answer, such as after a pull to
 * refresh, loads the picture again, so one that failed once can come back.
 */
export function pictureLoadKey(path: string | null | undefined, version?: string | number | null): string | null {
  if (!path) return null;
  return `${path}|${version ?? ''}`;
}

const HEX = /^#([0-9a-f]{6}|[0-9a-f]{8})$/i;

/** The legend to draw: the server's steps with a usable colour and label. */
export function legendSteps(layer: MapLayer | null | undefined): LegendStep[] {
  return (layer?.legend ?? [])
    .filter((s) => typeof s.color === 'string' && HEX.test(s.color.trim()) && !!s.label?.trim())
    .map((s) => ({ color: s.color.trim(), label: s.label.trim() }));
}

/** One sentence for a screen reader about the legend. */
export function legendA11y(layer: MapLayer): string {
  const steps = legendSteps(layer);
  if (steps.length === 0) return `${titleOf(layer)} legend: no colours were given.`;
  return `${titleOf(layer)} legend, ${steps.length} ${steps.length === 1 ? 'colour' : 'colours'}: ${steps.map((s) => s.label).join(', ')}.`;
}

/**
 * The map as one sentence for a screen reader: what the picture is, which
 * zones are outlined, the pin, and the layer drawn on top with its range.
 */
export function mapA11yLabel(opts: {
  sourceName?: string | null;
  zoneNames: string[];
  hasPin: boolean;
  layer?: MapLayer | null;
}): string {
  const parts: string[] = [];
  const source = opts.sourceName?.trim();
  parts.push(source ? `Top-down aerial image of your land, from ${source.replace(/[.\s]+$/, '')}.`
    : 'Top-down aerial image of your land.');
  const names = opts.zoneNames.map((n) => n.trim()).filter(Boolean);
  if (names.length === 1) parts.push(`One zone outlined: ${names[0]}.`);
  else if (names.length > 1) parts.push(`${names.length} zones outlined: ${names.join(', ')}.`);
  if (opts.hasPin) parts.push('Your pin is marked.');
  const layer = opts.layer && layerReady(opts.layer) ? opts.layer : null;
  if (layer) {
    const steps = legendSteps(layer);
    const range = steps.length >= 2 ? ` Colours run from ${steps[0].label} to ${steps[steps.length - 1].label}.`
      : steps.length === 1 ? ` Coloured areas show ${steps[0].label}.` : '';
    parts.push(`Showing the ${titleOf(layer)} layer.${range} The legend below lists every colour.`);
  }
  return parts.join(' ');
}
