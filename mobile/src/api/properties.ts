import axios from 'axios';
import { apiClient, getBaseUrl } from './client';
import { getAccessToken } from '../auth/tokenStorage';
import {
  Box, Imagery, MapLayers, OverridePut, Property, PropertyCreate, PropertyPatch,
  RefreshAccepted, SeasonEvent, SeasonEventPut, SeasonalPlan, SiteField,
  SiteProfile, Vitals, Zone, ZoneCreate, ZonePatch,
} from '../types/site';

// One typed call per route of the property, site profile, zone, imagery,
// seasonal plan and vitals contract (build spec section 4). Every call goes
// through the shared client, so the token, the single-flight refresh and the
// timeout are the same as everywhere else, and failures reach screens as the
// same axios errors (api/errorMessage.ts reads them).
//
// The routes are dark-launched: while a server's flag is off they answer
// 404. `isFeatureOff` tells that apart from a real failure, and the `…OrOff`
// calls turn it into `null` so a screen can fall back to what the app did
// before (Home's no-property form) instead of showing an error.

// ── "This server has the feature switched off" ───────────────────────────────

/** The two reads whose 404 means "feature off", not "not found". Any other
 *  404 (a property id that isn't yours, a deleted zone) is a real error. */
const FEATURE_PROBES = ['/properties', '/vitals'];

function pathOnly(url: string | undefined): string {
  if (!url) return '';
  // Absolute or relative, with or without a query string or a trailing slash.
  const noQuery = url.split('?')[0];
  const path = noQuery.replace(/^[a-z]+:\/\/[^/]+/i, '');
  return path.length > 1 ? path.replace(/\/$/, '') : path;
}

/**
 * Whether a failed request means this server has the new routes switched off:
 * a 404 answer to GET /properties or GET /vitals. Everything else, including
 * a dropped connection and a 404 on one property, is a real error.
 */
export function isFeatureOff(err: unknown): boolean {
  if (!axios.isAxiosError(err) || err.response?.status !== 404) return false;
  const method = (err.config?.method ?? 'get').toLowerCase();
  if (method !== 'get') return false;
  return FEATURE_PROBES.includes(pathOnly(err.config?.url));
}

/** Run a feature probe: `null` when the feature is off, the error otherwise. */
async function orOff<T>(load: () => Promise<T>): Promise<T | null> {
  try {
    return await load();
  } catch (err) {
    if (isFeatureOff(err)) return null;
    throw err;
  }
}

// ── Query keys ───────────────────────────────────────────────────────────────

/** Query keys for everything here, so a screen that changes a property can
 *  invalidate what Home and the other screens are showing. */
export const SITE_QUERY_KEYS = {
  properties: ['properties'] as const,
  property: (id: number) => ['properties', id] as const,
  siteProfile: (id: number) => ['properties', id, 'siteProfile'] as const,
  zones: (id: number) => ['properties', id, 'zones'] as const,
  imagery: (id: number) => ['properties', id, 'imagery'] as const,
  seasonalPlan: (id: number) => ['properties', id, 'seasonalPlan'] as const,
  mapLayers: (id: number) => ['properties', id, 'mapLayers'] as const,
  vitals: ['vitals'] as const,
};

/** The one part of a QueryClient `refreshHome` needs, so a test can pass its own. */
interface InvalidatingCache {
  invalidateQueries(filters: { queryKey: readonly unknown[] }): Promise<void>;
}

/**
 * After any change to a property, its zones, its corrections or its plan:
 * mark everything Home reads as stale, so Home (and any screen under it on
 * the stack) shows the change when it is next on screen. Zones are growing
 * areas, so the growing-area lists go too.
 */
export async function refreshHome(queryClient: InvalidatingCache): Promise<void> {
  await Promise.all([
    queryClient.invalidateQueries({ queryKey: SITE_QUERY_KEYS.vitals }),
    queryClient.invalidateQueries({ queryKey: SITE_QUERY_KEYS.properties }),
    queryClient.invalidateQueries({ queryKey: ['growingAreas'] }),
    queryClient.invalidateQueries({ queryKey: ['growingArea'] }),
  ]);
}

// ── Properties ───────────────────────────────────────────────────────────────

export async function fetchProperties(): Promise<Property[]> {
  const client = await apiClient();
  const { data } = await client.get<Property[]>('/properties');
  return data;
}

/** The person's properties, or `null` when this server has the feature off. */
export function fetchPropertiesOrOff(): Promise<Property[] | null> {
  return orOff(fetchProperties);
}

export async function fetchProperty(id: number): Promise<Property> {
  const client = await apiClient();
  const { data } = await client.get<Property>(`/properties/${id}`);
  return data;
}

export async function createProperty(body: PropertyCreate): Promise<Property> {
  const client = await apiClient();
  const { data } = await client.post<Property>('/properties', body);
  return data;
}

export async function updateProperty(id: number, patch: PropertyPatch): Promise<Property> {
  const client = await apiClient();
  const { data } = await client.patch<Property>(`/properties/${id}`, patch);
  return data;
}

export async function deleteProperty(id: number): Promise<void> {
  const client = await apiClient();
  await client.delete(`/properties/${id}`);
}

// ── Site profile and corrections ─────────────────────────────────────────────

export async function fetchSiteProfile(propertyId: number): Promise<SiteProfile> {
  const client = await apiClient();
  const { data } = await client.get<SiteProfile>(`/properties/${propertyId}/site-profile`);
  return data;
}

/** Ask the server to read the land again. It answers 202 at once. */
export async function refreshSiteProfile(propertyId: number): Promise<RefreshAccepted> {
  const client = await apiClient();
  const { data } = await client.post<RefreshAccepted>(
    `/properties/${propertyId}/site-profile/refresh`);
  return data;
}

export async function putOverride(propertyId: number, body: OverridePut): Promise<SiteProfile> {
  const client = await apiClient();
  const { data } = await client.put<SiteProfile>(`/properties/${propertyId}/overrides`, body);
  return data;
}

export async function deleteOverride(
  propertyId: number, field: SiteField, zoneId?: number,
): Promise<SiteProfile> {
  const client = await apiClient();
  const { data } = await client.delete<SiteProfile>(
    `/properties/${propertyId}/overrides/${field}`,
    zoneId == null ? undefined : { params: { zone_id: zoneId } },
  );
  return data;
}

// ── Zones ────────────────────────────────────────────────────────────────────

export async function fetchZones(propertyId: number): Promise<Zone[]> {
  const client = await apiClient();
  const { data } = await client.get<Zone[]>(`/properties/${propertyId}/zones`);
  return data;
}

export async function createZone(propertyId: number, body: ZoneCreate): Promise<Zone> {
  const client = await apiClient();
  const { data } = await client.post<Zone>(`/properties/${propertyId}/zones`, body);
  return data;
}

export async function updateZone(
  propertyId: number, zoneId: number, patch: ZonePatch,
): Promise<Zone> {
  const client = await apiClient();
  const { data } = await client.patch<Zone>(`/properties/${propertyId}/zones/${zoneId}`, patch);
  return data;
}

/** The whole-lot zone cannot be deleted, and a zone holding plants answers
 *  409: both reach the caller as the server's error. */
export async function deleteZone(propertyId: number, zoneId: number): Promise<void> {
  const client = await apiClient();
  await client.delete(`/properties/${propertyId}/zones/${zoneId}`);
}

// ── Imagery ──────────────────────────────────────────────────────────────────

/**
 * The public aerial image service can take most of a minute the first time
 * an area is asked for, so these calls wait longer than the usual 15 s. The
 * server gives up at 45 s and answers either way.
 */
export const IMAGERY_TIMEOUT_MS = 60000;

/** The top-down image around a pin, for the pin step before a property exists. */
export async function fetchBlockImagery(lat: number, lng: number): Promise<Imagery> {
  const client = await apiClient();
  const { data } = await client.get<Imagery>('/imagery/block', {
    params: { lat, lng }, timeout: IMAGERY_TIMEOUT_MS,
  });
  return data;
}

export async function fetchPropertyImagery(propertyId: number): Promise<Imagery> {
  const client = await apiClient();
  const { data } = await client.get<Imagery>(`/properties/${propertyId}/imagery`, {
    timeout: IMAGERY_TIMEOUT_MS,
  });
  return data;
}

/**
 * Where to load an Imagery's picture from: the server's `image_path` on the
 * configured server. The bytes need the sign-in token, so pass
 * `imageHeaders()` alongside it to `<Image source={{ uri, headers }} />`.
 */
export async function imageryUri(imagery: Pick<Imagery, 'image_path'>): Promise<string> {
  const base = await getBaseUrl();
  const path = imagery.image_path.startsWith('/') ? imagery.image_path : `/${imagery.image_path}`;
  return `${base}${path}`;
}

/**
 * The picture itself, as a `data:` address an `<Image>` can show with no
 * headers. It is fetched through the signed-in client, so an expired token
 * is refreshed the same way as for every other call, and it works where an
 * image element cannot send a sign-in header (the web preview).
 */
export async function fetchImageryDataUri(imagery: Pick<Imagery, 'image_path'>): Promise<string> {
  return fetchSignedDataUri(imagery.image_path);
}

/**
 * Any picture on our server (an aerial image, a map layer), as a `data:`
 * address, fetched through the signed-in client. See `fetchImageryDataUri`.
 */
export async function fetchSignedDataUri(imagePath: string): Promise<string> {
  const client = await apiClient();
  const path = imagePath.startsWith('/') ? imagePath : `/${imagePath}`;
  const { data } = await client.get<Blob>(path, { responseType: 'blob', timeout: IMAGERY_TIMEOUT_MS });
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      if (typeof reader.result === 'string' && reader.result.startsWith('data:')) resolve(reader.result);
      else reject(new Error('The picture could not be read.'));
    };
    reader.onerror = () => reject(new Error('The picture could not be read.'));
    reader.readAsDataURL(data);
  });
}

/** The sign-in header the image route needs (every route here is signed in). */
export async function imageHeaders(): Promise<Record<string, string>> {
  const token = await getAccessToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

/** Turn degrees into image pixels with the image's `bounds` (north up,
 *  linear across a block this small). */
export function lngLatToPixel(
  imagery: Pick<Imagery, 'bounds' | 'width' | 'height'>, lng: number, lat: number,
): { x: number; y: number } {
  const { bounds: b, width, height } = imagery;
  return {
    x: ((lng - b.west) / (b.east - b.west)) * width,
    y: ((b.north - lat) / (b.north - b.south)) * height,
  };
}

/** Turn image pixels back into degrees, the inverse of `lngLatToPixel`. */
export function pixelToLngLat(
  imagery: Pick<Imagery, 'bounds' | 'width' | 'height'>, x: number, y: number,
): { lng: number; lat: number } {
  const { bounds: b, width, height } = imagery;
  return {
    lng: b.west + (x / width) * (b.east - b.west),
    lat: b.north - (y / height) * (b.north - b.south),
  };
}

/** A box in degrees from two corners in image pixels, in either order. */
export function pixelsToBox(
  imagery: Pick<Imagery, 'bounds' | 'width' | 'height'>,
  a: { x: number; y: number }, c: { x: number; y: number },
): Box {
  const p = pixelToLngLat(imagery, a.x, a.y);
  const q = pixelToLngLat(imagery, c.x, c.y);
  return {
    west: Math.min(p.lng, q.lng), east: Math.max(p.lng, q.lng),
    south: Math.min(p.lat, q.lat), north: Math.max(p.lat, q.lat),
  };
}

// ── Map layers ───────────────────────────────────────────────────────────────

export async function fetchMapLayers(propertyId: number): Promise<MapLayers> {
  const client = await apiClient();
  const { data } = await client.get<MapLayers>(`/properties/${propertyId}/layers`);
  return data;
}

/**
 * The property's map layers (sun, trees, water), or `null` when this server
 * answers 404: an older server without the route, or the feature off. The
 * map then shows the aerial image only. Any other failure is an error.
 */
export async function fetchMapLayersOrOff(propertyId: number): Promise<MapLayers | null> {
  try {
    return await fetchMapLayers(propertyId);
  } catch (err) {
    if (axios.isAxiosError(err) && err.response?.status === 404) return null;
    throw err;
  }
}

// ── Seasonal plan ────────────────────────────────────────────────────────────

export async function fetchSeasonalPlan(propertyId: number): Promise<SeasonalPlan> {
  const client = await apiClient();
  const { data } = await client.get<SeasonalPlan>(`/properties/${propertyId}/seasonal-plan`);
  return data;
}

export async function putSeasonEvent(
  propertyId: number, eventKey: string, body: SeasonEventPut,
): Promise<SeasonEvent> {
  const client = await apiClient();
  const { data } = await client.put<SeasonEvent>(
    `/properties/${propertyId}/seasonal-plan/events/${encodeURIComponent(eventKey)}`, body);
  return data;
}

// ── Vitals ───────────────────────────────────────────────────────────────────

export async function fetchVitals(propertyId?: number): Promise<Vitals> {
  const client = await apiClient();
  const { data } = await client.get<Vitals>(
    '/vitals', propertyId == null ? undefined : { params: { property_id: propertyId } });
  return data;
}

/** Home's report, or `null` when this server has the feature off. */
export function fetchVitalsOrOff(propertyId?: number): Promise<Vitals | null> {
  return orOff(() => fetchVitals(propertyId));
}
