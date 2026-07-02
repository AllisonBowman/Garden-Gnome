import { apiClient } from './client';
import { CensusSummary } from '../types';

export async function fetchCensusSummary(): Promise<CensusSummary> {
  const client = await apiClient();
  const { data } = await client.get<CensusSummary>('/census/summary');
  return data;
}

export async function syncCensus(): Promise<{ status: string; message?: string }> {
  const client = await apiClient();
  const { data } = await client.post('/census/sync');
  return data;
}
