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
  location_description?: string;
  initial_condition?: string;
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
  const { data } = await client.post<CareLog>(`/plants/${plantId}/log`, {
    action,
    notes,
  });
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
