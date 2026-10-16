import { apiClient } from './client';
import { AiStatus } from '../care/aiCapabilities';

export const AI_STATUS_QUERY_KEY = ['aiStatus'] as const;

/** GET /ai/status: public, cheap, and changes only with a deploy. */
export async function fetchAiStatus(): Promise<AiStatus> {
  const client = await apiClient();
  const { data } = await client.get<AiStatus>('/ai/status');
  return data;
}
