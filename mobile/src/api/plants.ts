import { Platform } from 'react-native';
import { apiClient } from './client';
import {
  Plant, CareLog, CareType, StewardshipRecord, WeatherAttribution,
} from '../types';

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
  environment_id?: number;
  location?: string;
  intake_notes?: string;
  acquired_on?: string;
}

export async function createPlant(payload: PlantDraft): Promise<Plant> {
  const client = await apiClient();
  const { data } = await client.post<Plant>('/plants/', payload);
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
  const { data } = await client.post<BulkCreateResult>('/plants/bulk', { plants });
  return data;
}

export async function logCare(
  plantId: number,
  action: CareType,
  notes = '',
): Promise<CareLog> {
  const client = await apiClient();
  const { data } = await client.post<CareLog>(`/plants/${plantId}/logs`, {
    action,
    notes,
  });
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
  return data;
}

export async function fetchCareLogs(plantId: number): Promise<CareLog[]> {
  const client = await apiClient();
  const { data } = await client.get<CareLog[]>(`/plants/${plantId}/logs`);
  return data;
}

export async function transferPlant(
  plantId: number,
  toEnvironmentId: number,
  notes = '',
): Promise<Plant> {
  const client = await apiClient();
  const { data } = await client.post<Plant>(`/plants/${plantId}/transfer`, {
    to_environment_id: toEnvironmentId,
    transfer_notes: notes,
  });
  return data;
}

export async function fetchStewardship(plantId: number): Promise<StewardshipRecord[]> {
  const client = await apiClient();
  const { data } = await client.get<StewardshipRecord[]>(`/plants/${plantId}/stewardship`);
  return data;
}
