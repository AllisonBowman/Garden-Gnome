import { Platform } from 'react-native';
import { apiClient } from './client';
import { Species } from '../types';

export async function fetchSpeciesList(): Promise<Species[]> {
  const client = await apiClient();
  const { data } = await client.get<Species[]>('/species/');
  return data;
}

export interface IdentifyCandidate {
  id: number;
  common_name: string;
  scientific_name: string;
}

export interface IdentifyResponse {
  backend: string;
  observation: string;
  candidates: IdentifyCandidate[];
}

export async function identifySpeciesPhoto(asset: {
  uri: string;
  mimeType?: string;
  fileName?: string | null;
}): Promise<IdentifyResponse> {
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
  const { data } = await client.post<IdentifyResponse>('/species/identify-photo', form, {
    // Let axios/the browser set the multipart boundary; local vision models are slow
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 190000,
  });
  return data;
}

export async function fetchSpecies(id: number): Promise<Species> {
  const client = await apiClient();
  const { data } = await client.get<Species>(`/species/${id}`);
  return data;
}
