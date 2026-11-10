import { Platform } from 'react-native';
import { apiClient } from './client';
import { fetchSpecies } from './species';
import { localDateString } from './serverDate';
import {
  Plant, CareLog, CareOutcome, CareType, Species, StewardshipRecord, WeatherAttribution,
} from '../types';

// ── The garden's care data, loaded once and shared ──────────────────────────
// The to-do list, the streak badges and the reminder planner all need the
// same three things: every plant, each plant's care log, and each species'
// schedules (the plant list embeds species without them). Each used to load
// them on its own — three fan-outs of one request per plant and per species,
// all at launch, into a server that may be waking up. Now there is one load;
// whoever asks while it is running gets the same answer.

export interface GardenCareData {
  plants: Plant[];
  logsByPlant: Record<number, CareLog[]>;
  speciesById: Record<number, Species>;
  /** Plants whose care log or species couldn't be read this time. Every
   *  schedule leaves them out, rather than reading a missing log as "never
   *  cared for" or a missing species as "no schedule on record". */
  unreadPlantIds: number[];
}

let gardenGeneration = 0;
let gardenLoad: { generation: number; promise: Promise<GardenCareData> } | null = null;
/** Counts sessions that have ended on this phone. A load belongs to the
 *  session it started in. */
let sessionEpoch = 0;

/** Anything loaded before now is out of date, so the next ask starts a fresh
 *  load instead of joining one that began before the change. Every write in
 *  this module calls it once the server has accepted the write. */
export function gardenChanged(): void {
  gardenGeneration += 1;
}

/** What a load still running when its session ended settles with, instead of
 *  the garden it read: that garden belongs to whoever signed out. */
export class GardenLoadAbandoned extends Error {
  constructor() {
    super('The garden load belonged to a session that has ended.');
    this.name = 'GardenLoadAbandoned';
  }
}

/**
 * The session ended (sign-out, a deleted account, a refused session): the
 * load in flight, if any, is the last account's. Drop it, so the next account
 * to sign in on this phone starts its own load rather than joining that one,
 * and so whoever was still waiting on it (a reminder reschedule) gets nothing
 * from it to act on. React Query's clear() can't reach this: it lives here,
 * outside the query cache.
 */
export function forgetGardenLoad(): void {
  sessionEpoch += 1;
  gardenGeneration += 1;
  gardenLoad = null;
}

async function fetchGardenCareData(): Promise<GardenCareData> {
  const plants = await fetchPlants();
  const logsByPlant: Record<number, CareLog[]> = {};
  const speciesById: Record<number, Species> = {};
  const unread = new Set<number>();
  const speciesIds = [...new Set(plants.map((p) => p.species_id))];
  const missingSpecies = new Set<number>();
  // Settled one by one: a 404 or a timeout leaves that plant out and says
  // so, instead of blanking every card the way one rejection in a
  // Promise.all did.
  await Promise.all([
    ...plants.map(async (p) => {
      try {
        logsByPlant[p.id] = await fetchCareLogs(p.id);
      } catch {
        unread.add(p.id);
      }
    }),
    ...speciesIds.map(async (id) => {
      try {
        speciesById[id] = await fetchSpecies(id);
      } catch {
        missingSpecies.add(id);
      }
    }),
  ]);
  for (const p of plants) if (missingSpecies.has(p.species_id)) unread.add(p.id);
  return {
    plants, logsByPlant, speciesById,
    unreadPlantIds: [...unread].sort((a, b) => a - b),
  };
}

/** The garden's plants, care logs and species schedules — one load shared by
 *  everyone who asks while it runs. Rejects only when the plant list itself
 *  can't be read. */
export function loadGardenCareData(): Promise<GardenCareData> {
  if (gardenLoad && gardenLoad.generation === gardenGeneration) return gardenLoad.promise;
  const epoch = sessionEpoch;
  const promise = fetchGardenCareData().then((data) => {
    if (epoch !== sessionEpoch) throw new GardenLoadAbandoned();
    return data;
  });
  const load = { generation: gardenGeneration, promise };
  gardenLoad = load;
  const settle = () => {
    if (gardenLoad === load) gardenLoad = null;
  };
  load.promise.then(settle, settle);
  return load.promise;
}

/** The plants whose care log and species both came back. */
export function readablePlants(data: GardenCareData): Plant[] {
  const unread = new Set(data.unreadPlantIds);
  return data.plants.filter((p) => !unread.has(p.id));
}

export async function fetchPlants(): Promise<Plant[]> {
  const client = await apiClient();
  const { data } = await client.get<Plant[]>('/plants/');
  return data;
}

export async function fetchPlant(id: number): Promise<Plant> {
  const client = await apiClient();
  const { data } = await client.get<Plant>(`/plants/${id}`);
  return data;
}

export interface PlantDraft {
  /** Optional — the server generates "Tomatoes — south fence" when it's blank,
   *  because a planting has no name of its own but every surface that talks
   *  about a plant still needs something to call it. */
  nickname?: string;
  species_id: number;
  /** How many physical plants this row stands for. Omit for an individual. */
  quantity?: number;
  growing_area_id?: number;
  location?: string;
  intake_notes?: string;
  /** 'YYYY-MM-DD'. Left out, it is today on this phone's calendar. */
  acquired_on?: string;
}

/** The day a new plant was added is the first anchor every check schedule
 *  has. The server stamps its own date when none is sent, and its clock runs
 *  on UTC: a plant added on a Tokyo morning would be dated yesterday, and one
 *  added on a California evening tomorrow. So the phone says which day it is
 *  here. */
function datedToday(draft: PlantDraft, today: string): PlantDraft {
  return draft.acquired_on ? draft : { ...draft, acquired_on: today };
}

export async function createPlant(payload: PlantDraft): Promise<Plant> {
  const client = await apiClient();
  const { data } = await client.post<Plant>('/plants/', datedToday(payload, localDateString()));
  gardenChanged();
  return data;
}

export interface BulkCreateResult {
  created: number;
  plants: Plant[];
}

/**
 * Create many plants in one transaction — all or nothing.
 *
 * This is how a captured garden lands. Posting them one at a time means a
 * failure halfway through leaves a half-imported garden the caretaker can't
 * tell the shape of, and hundreds of requests against a backend that has to
 * cold-start reliably time out before they finish.
 */
export async function createPlantsBulk(plants: PlantDraft[]): Promise<BulkCreateResult> {
  const client = await apiClient();
  const today = localDateString();
  const { data } = await client.post<BulkCreateResult>('/plants/bulk', {
    plants: plants.map((p) => datedToday(p, today)),
  });
  gardenChanged();
  return data;
}

export async function logCare(
  plantId: number,
  action: CareType,
  notes = '',
  outcome?: CareOutcome,
): Promise<CareLog> {
  const client = await apiClient();
  const { data } = await client.post<CareLog>(`/plants/${plantId}/logs`, {
    action,
    notes,
    ...(outcome ? { outcome } : {}),
  });
  gardenChanged();
  return data;
}

export interface AdviceResponse {
  plant_id: number;
  nickname: string;
  species: string;
  backend: string;
  advice: string;
  /** True when model output failed the server's groundedness guard and this
   * is the rule-based fallback. `backend` already reads "stub" in that case,
   * so the badge is honest either way. */
  guarded?: boolean;
  /** Present only when the local forecast informed this advice. Apple's terms
   *  require the credit wherever WeatherKit data is shown, and advice for an
   *  exposed plant restates the forecast in words. Null for indoor plants and
   *  whenever no forecast was fetched. */
  weather_attribution?: WeatherAttribution | null;
}

export async function getAdvice(plantId: number, symptoms = ''): Promise<AdviceResponse> {
  const client = await apiClient();
  const { data } = await client.post<AdviceResponse>(`/plants/${plantId}/advice`, {
    symptoms,
  });
  return data;
}

export interface DiagnosisResponse {
  plant_id: number;
  nickname: string;
  species: string;
  backend: string;
  diagnosis: string;
}

export async function diagnosePlantPhoto(
  plantId: number,
  asset: { uri: string; mimeType?: string; fileName?: string | null },
  notes = '',
): Promise<DiagnosisResponse> {
  const client = await apiClient();
  const form = new FormData();
  const name = asset.fileName ?? 'photo.jpg';
  const type = asset.mimeType ?? 'image/jpeg';
  if (Platform.OS === 'web') {
    // Picker returns a data/blob URI on web; convert to a File for upload
    const blob = await (await fetch(asset.uri)).blob();
    form.append('photo', new File([blob], name, { type: blob.type || type }));
  } else {
    form.append('photo', { uri: asset.uri, name, type } as unknown as Blob);
  }
  form.append('notes', notes);
  const { data } = await client.post<DiagnosisResponse>(
    `/plants/${plantId}/diagnose-photo`, form, {
      // Let axios/the browser set the multipart boundary; local vision models are slow
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 190000,
    },
  );
  gardenChanged();
  return data;
}

export async function fetchCareLogs(plantId: number): Promise<CareLog[]> {
  const client = await apiClient();
  const { data } = await client.get<CareLog[]>(`/plants/${plantId}/logs`);
  return data;
}

/**
 * Remove a plant and everything recorded about it. The server cascades its
 * care logs and stewardship history, so this cannot be undone from the app —
 * callers must confirm first.
 */
export async function deletePlant(plantId: number): Promise<void> {
  const client = await apiClient();
  await client.delete(`/plants/${plantId}`);
  gardenChanged();
}

export async function transferPlant(
  plantId: number,
  toGrowingAreaId: number,
  notes = '',
): Promise<Plant> {
  const client = await apiClient();
  const { data } = await client.post<Plant>(`/plants/${plantId}/transfer`, {
    to_growing_area_id: toGrowingAreaId,
    transfer_notes: notes,
  });
  gardenChanged();
  return data;
}

export async function fetchStewardship(plantId: number): Promise<StewardshipRecord[]> {
  const client = await apiClient();
  const { data } = await client.get<StewardshipRecord[]>(`/plants/${plantId}/stewardship`);
  return data;
}
