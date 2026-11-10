import { apiClient } from './client';
import { Species } from '../types';
import { aToZ } from '../care/catalog';

/** The catalog, A to Z by common name. The server sends it in the order the
 *  rows were added, which for a thousand species is no order at all. */
export async function fetchSpeciesList(): Promise<Species[]> {
  const client = await apiClient();
  const { data } = await client.get<Species[]>('/species/');
  return aToZ(data);
}

export async function fetchSpecies(id: number): Promise<Species> {
  const client = await apiClient();
  const { data } = await client.get<Species>(`/species/${id}`);
  return data;
}
