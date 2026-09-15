import { apiClient } from './client';
import {
  GrowingArea, GrowingAreaType, Shelter, TempExposure, SunExposure, Weather,
  GrowingSurface, GrowingGoal,
} from '../types';

export interface GrowingAreaClimate {
  shelter?: Shelter;
  temp_exposure?: TempExposure;
  sun_exposure?: SunExposure;
}

/** The real estate: what there is to plant into, and what it is for.
 *
 * Every field is optional and none is defaulted on the way out. Sending 0 for
 * a dimension nobody measured would land in the catalog matcher as a real
 * measurement; leaving it off is what keeps it `unknown`. */
export interface GrowingAreaRealEstate {
  surface?: GrowingSurface;
  area_sqft?: number;
  headroom_in?: number;
  soil_depth_in?: number;
  goals?: GrowingGoal[];
}

export async function fetchGrowingAreas(): Promise<GrowingArea[]> {
  const client = await apiClient();
  const { data } = await client.get<GrowingArea[]>('/growing-areas/');
  return data;
}

export async function fetchGrowingArea(id: number): Promise<GrowingArea> {
  const client = await apiClient();
  const { data } = await client.get<GrowingArea>(`/growing-areas/${id}`);
  return data;
}

export interface GrowingAreaWeatherResponse {
  available: boolean;
  detail: string;
  weather: Weather | null;
}

export async function fetchGrowingAreaWeather(id: number): Promise<GrowingAreaWeatherResponse> {
  const client = await apiClient();
  const { data } = await client.get<GrowingAreaWeatherResponse>(`/growing-areas/${id}/weather`);
  return data;
}

export async function createGrowingArea(payload: {
  name: string;
  type: GrowingAreaType;
  city?: string;
  region?: string;
  country?: string;
  lat?: number;
  lng?: number;
} & GrowingAreaClimate & GrowingAreaRealEstate): Promise<GrowingArea> {
  const client = await apiClient();
  const { data } = await client.post<GrowingArea>('/growing-areas/', payload);
  return data;
}

export async function updateGrowingArea(
  id: number,
  patch: Partial<{
    name: string;
    type: GrowingAreaType;
    city: string;
    region: string;
    country: string;
    lat: number;
    lng: number;
  } & GrowingAreaClimate & GrowingAreaRealEstate>,
): Promise<GrowingArea> {
  const client = await apiClient();
  const { data } = await client.patch<GrowingArea>(`/growing-areas/${id}`, patch);
  return data;
}

// --- Fit: does this species belong in this area? -------------------------

/** One axis's verdict, and the sentence a person reads for it.
 *
 * `sentence` already carries the genus-borrowed label when the value behind
 * it was inherited (ADR 0002), so render it as-is — never rebuild it here. */
export interface FitFinding {
  axis: 'indoor_outdoor' | 'sun' | 'soil' | 'footprint' | 'upkeep' | 'goal';
  verdict: 'fits' | 'misfits' | 'unknown';
  sentence: string;
  borrowed: boolean;
}

/** A species put forward for an area. `fits` holds only confirmed axes —
 *  never the unknown ones, because "no idea how big it gets" is not a reason
 *  to plant something. `score` is their count. */
export interface Candidate {
  species_id: number;
  common_name: string;
  scientific_name: string;
  score: number;
  fits: FitFinding[];
}

/** A plant already standing here, and what specifically doesn't suit it. */
export interface PlantMisfit {
  plant_id: number;
  nickname: string;
  species_id: number;
  common_name: string;
  misfits: FitFinding[];
}

export async function fetchCandidates(
  id: number, limit = 20,
): Promise<Candidate[]> {
  const client = await apiClient();
  const { data } = await client.get<Candidate[]>(
    `/growing-areas/${id}/candidates`, { params: { limit } });
  return data;
}

export async function fetchMisfits(id: number): Promise<PlantMisfit[]> {
  const client = await apiClient();
  const { data } = await client.get<PlantMisfit[]>(`/growing-areas/${id}/misfits`);
  return data;
}
