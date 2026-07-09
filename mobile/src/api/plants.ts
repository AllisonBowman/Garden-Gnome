import { Platform } from 'react-native';
import { apiClient } from './client';
import { Plant, CareLog, CareType, StewardshipRecord } from '../types';

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

export async function createPlant(payload: {
  nickname: string;
  species_id: number;
  environment_id?: number;
  location?: string;
  intake_notes?: string;
  acquired_on?: string;
}): Promise<Plant> {
  const client = await apiClient();
  const { data } = await client.post<Plant>('/plants/', payload);
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
