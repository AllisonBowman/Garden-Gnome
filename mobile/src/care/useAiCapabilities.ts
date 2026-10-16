import { useQuery } from '@tanstack/react-query';
import { AI_STATUS_QUERY_KEY, fetchAiStatus } from '../api/aiStatus';
import { photoDiagnosisOffered, symptomsOffered } from './aiCapabilities';

export interface AiCapabilities {
  /** Show the photo check-up card. */
  photoDiagnosis: boolean;
  /** Show the free-text "anything wrong?" box above care advice. */
  symptoms: boolean;
}

/**
 * What the care engine can do right now, asked of the server once and shared
 * by every plant screen. Both answers are false until the server says yes:
 * a feature that would answer "not switched on yet" is not shown at all.
 *
 * The status changes only with a deploy, so it is cached for the session
 * rather than refetched per screen; a failed call is retried once and then
 * simply leaves the optional features off.
 */
export function useAiCapabilities(): AiCapabilities {
  const { data } = useQuery({
    queryKey: AI_STATUS_QUERY_KEY,
    queryFn: fetchAiStatus,
    staleTime: Infinity,
    retry: 1,
  });
  return {
    photoDiagnosis: photoDiagnosisOffered(data),
    symptoms: symptomsOffered(data),
  };
}
