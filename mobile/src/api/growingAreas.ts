import { apiClient } from './client';
import {
  GrowingArea, GrowingAreaType, Shelter, TempExposure, SunExposure, Weather,
  GrowingSurface, GrowingGoal, EatenPart,
} from '../types';
import { leftOffCount, totalCount } from '../growingAreas/ranking';

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
  /** Whose word it is: the authorities whose pages settled a value this
   *  finding rests on, for this species itself. Empty for an unknown and
   *  for a value only the genus answered (`borrowed` says that). Absent from
   *  a server that predates it. */
  authorities?: string[];
  /** Which of the area's goals this finding answers. Edible and pollinators
   *  share the `goal` axis, so this is the only way to tell them apart.
   *  Absent from a server that predates it. */
  goal?: GrowingGoal | null;
}

export type FitAxis = FitFinding['axis'];

/** A species put forward for an area. `fits` holds only confirmed axes —
 *  never the unknown ones, because "no idea how big it gets" is not a reason
 *  to plant something. `score` is their count. */
export interface Candidate {
  species_id: number;
  common_name: string;
  scientific_name: string;
  score: number;
  fits: FitFinding[];
  /** One short caution line when the species is recorded toxic to pets or
   *  people ("Toxic to pets and people if eaten."), null otherwise. Shown as
   *  a warning on every row or card that lists the candidate, because a
   *  recommendation is exactly where a hazard must not go unsaid. Absent
   *  from a server that predates it. */
  hazard?: string | null;
  /** What is eaten (ADR 0011): the parts a source names (for a food crop
   *  whose record names none, the part the app's own crop table names),
   *  which a list that asked for something to eat is grouped by, and the
   *  one line that says them with their condition and the hazards recorded
   *  beside them. Both null when no part is named. The line is shown as
   *  sent and never cut, because the condition is the half that keeps it
   *  honest. Absent from a server that predates them. */
  eaten_parts?: EatenPart[] | null;
  eating?: string | null;
}

/** A plant already standing here, and what specifically doesn't suit it. */
export interface PlantMisfit {
  plant_id: number;
  nickname: string;
  species_id: number;
  common_name: string;
  misfits: FitFinding[];
}

/** A limit no catalog this app holds will reach, for a caller that needs
 *  every candidate rather than the best few. The endpoint ranks and then
 *  truncates, so a filter built on a truncated list silently drops whatever
 *  ranked past the cut — and in a "fits this area" filter, a species that
 *  is missing reads as one that does not fit. */
export const EVERY_CANDIDATE = 100_000;


/** The first `limit` of an area's ranked candidates, and how many there are
 *  in all — counted by the server before it cut the list. `total` is null
 *  from a server too old to send the count. `leftOff` is how many species
 *  suit the space but are off the list because no source records a part of
 *  them as eaten: counted only when the area asked for something to eat,
 *  and null otherwise or from a server older than the count. */
export interface CandidatePage {
  rows: Candidate[];
  total: number | null;
  leftOff: number | null;
}

export async function fetchCandidatePage(id: number, limit: number): Promise<CandidatePage> {
  const client = await apiClient();
  const resp = await client.get<Candidate[]>(
    `/growing-areas/${id}/candidates`, { params: { limit } });
  return {
    rows: resp.data,
    total: totalCount(resp.headers),
    leftOff: leftOffCount(resp.headers),
  };
}

export async function fetchMisfits(id: number): Promise<PlantMisfit[]> {
  const client = await apiClient();
  const { data } = await client.get<PlantMisfit[]>(`/growing-areas/${id}/misfits`);
  return data;
}

/** One species against one area, every axis — what Add Plant asks before
 *  the plant is saved. `findings` holds fits, misfits and unknowns alike;
 *  `candidate` is the server's own Candidate verdict, never re-derived. */
export interface SpeciesFit {
  species_id: number;
  common_name: string;
  scientific_name: string;
  score: number;
  candidate: boolean;
  findings: FitFinding[];
}

export async function fetchSpeciesFit(
  areaId: number, speciesId: number,
): Promise<SpeciesFit> {
  const client = await apiClient();
  const { data } = await client.get<SpeciesFit>(
    `/growing-areas/${areaId}/fit/${speciesId}`);
  return data;
}
