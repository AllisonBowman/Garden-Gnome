import { apiClient } from './client';
import {
  Environment, EnvironmentType, Shelter, TempExposure, SunExposure,
} from '../types';

export interface EnvironmentClimate {
  shelter?: Shelter;
  temp_exposure?: TempExposure;
  sun_exposure?: SunExposure;
}

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
} & EnvironmentClimate): Promise<Environment> {
  const client = await apiClient();
  const { data } = await client.post<Environment>('/environments/', payload);
  return data;
}

export async function updateEnvironment(
  id: number,
  patch: Partial<{
    name: string;
    type: EnvironmentType;
    city: string;
    region: string;
    country: string;
    lat: number;
    lng: number;
  } & EnvironmentClimate>,
): Promise<Environment> {
  const client = await apiClient();
  const { data } = await client.patch<Environment>(`/environments/${id}`, patch);
  return data;
}
