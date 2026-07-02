import { apiClient } from './client';
import { Environment, EnvironmentType } from '../types';

export async function fetchEnvironments(): Promise<Environment[]> {
  const client = await apiClient();
  const { data } = await client.get<Environment[]>('/environments/');
  return data;
}

export async function fetchEnvironment(id: number): Promise<Environment> {
  const client = await apiClient();
  const { data } = await client.get<Environment>(`/environments/${id}`);
  return data;
}

export async function createEnvironment(payload: {
  name: string;
  type: EnvironmentType;
  city?: string;
  region?: string;
  country?: string;
  lat?: number;
  lng?: number;
}): Promise<Environment> {
  const client = await apiClient();
  const { data } = await client.post<Environment>('/environments/', payload);
  return data;
}
