import { MapLayers } from '../types/site';

// The land map card on Home and Your land (map and visuals spec section 4.4):
// which form it takes from the state of its three queries, the one-line
// messages for what did not load, and how often to ask again for layers the
// server is still drawing. Pure: no React Native imports.

/** How long Home and Your land keep the aerial image's address before
 *  asking again. The route is rate limited (it can fetch a cold image), and
 *  the picture changes only when the pin moves. */
export const IMAGERY_STALE_MS = 30 * 60 * 1000;

/** How often to ask again while a layer is still being prepared. */
export const LAYERS_POLL_MS = 60 * 1000;

export const MAP_LOADING_LINE = 'Loading the map.';
export const MAP_FAILED_LINE = 'The map could not be loaded. Everything else about your land is below.';
export const ZONES_FAILED_LINE = 'Your zones could not be loaded, so they are not outlined on the map.';
export const LAYERS_FAILED_LINE = 'The sun, trees and water layers could not be loaded, so the map shows the photograph alone.';

export interface LandMapInput {
  imagery: { hasData: boolean; isLoading: boolean; isError: boolean };
  zones: { hasData: boolean; isError: boolean };
  /** `hasData` is true for a null answer too (an older server: Aerial only). */
  layers: { hasData: boolean; isError: boolean };
}

export interface LandMapState {
  /** `map`: draw it. `loading`/`failed`: one line instead of the map. */
  kind: 'map' | 'loading' | 'failed';
  /** The line to show instead of the map, or null. */
  line: string | null;
  /** Lines under the map about the parts that did not load. */
  notes: string[];
}

/**
 * What the map card shows. A map that will not load is one line and never
 * stops the rest of the screen; zones or layers that fail leave the
 * photograph with a line saying what is missing. A layers route that
 * answers 404 is not a failure (fetchMapLayersOrOff gives null): the
 * Aerial chip alone is offered and nothing is said.
 */
export function landMapState(q: LandMapInput): LandMapState {
  if (!q.imagery.hasData) {
    if (q.imagery.isError) return { kind: 'failed', line: MAP_FAILED_LINE, notes: [] };
    return { kind: 'loading', line: MAP_LOADING_LINE, notes: [] };
  }
  const notes: string[] = [];
  if (q.zones.isError && !q.zones.hasData) notes.push(ZONES_FAILED_LINE);
  if (q.layers.isError && !q.layers.hasData) notes.push(LAYERS_FAILED_LINE);
  return { kind: 'map', line: null, notes };
}

/** Ask again every minute while any layer is still being prepared. */
export function layersRefetchEvery(layers: MapLayers | null | undefined): number | false {
  return (layers?.layers ?? []).some((l) => l.status === 'not_ready') ? LAYERS_POLL_MS : false;
}
