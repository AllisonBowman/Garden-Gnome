import { apiClient } from './client';
import { Species } from '../types';

export async function fetchSpeciesList(): Promise<Species[]> {
  const client = await apiClient();
  const { data } = await client.get<Species[]>('/species/');
  return data;
}

export async function fetchSpecies(id: number): Promise<Species> {
  const client = await apiClient();
  const { data } = await client.get<Species>(`/species/${id}`);
  return data;
}
