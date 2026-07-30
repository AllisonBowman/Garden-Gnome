import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchPlants, fetchCareLogs } from '../api/plants';
import { fetchSpecies } from '../api/species';
import { CareLog, Species } from '../types';
import { computeCareTasks, CareTask } from './schedule';

export const CARE_TASKS_QUERY_KEY = ['careTasksData'] as const;

interface CareTasksData {
  logsByPlant: Record<number, CareLog[]>;
  speciesById: Record<number, Species>;
  plants: Awaited<ReturnType<typeof fetchPlants>>;
}

// One aggregate load feeding both the environment calendar and the Plants
// to-do list: plants, each plant's care logs, and full species records (plant
// lists embed species WITHOUT care_schedules, so the schedules — the whole
// point — must be fetched per unique species, exactly as reminders.ts does).
async function fetchCareTasksData(): Promise<CareTasksData> {
  const plants = await fetchPlants();

  const logsByPlant: Record<number, CareLog[]> = {};
  await Promise.all(plants.map(async (p) => {
    logsByPlant[p.id] = await fetchCareLogs(p.id);
  }));

  const speciesIds = [...new Set(plants.map((p) => p.species_id))];
  const speciesById: Record<number, Species> = {};
  await Promise.all(speciesIds.map(async (id) => {
    speciesById[id] = await fetchSpecies(id);
  }));

  return { plants, logsByPlant, speciesById };
}

export interface UseCareTasksResult {
  tasks: CareTask[];
  isLoading: boolean;
  isError: boolean;
  refetch: () => void;
  isRefetching: boolean;
}

/**
 * Next-due care tasks across all of the user's plants, recomputed against the
 * live clock. Pass an `environmentId` to scope to one environment (the
 * calendar); omit it for everything (the to-do list). The heavy fetch is
 * shared under one query key, so both screens hit the cache, not the network.
 */
export function useCareTasks(environmentId?: number): UseCareTasksResult {
  const { data, isLoading, isError, refetch, isRefetching } = useQuery({
    queryKey: CARE_TASKS_QUERY_KEY,
    queryFn: fetchCareTasksData,
  });

  const tasks = useMemo(() => {
    if (!data) return [];
    const all = computeCareTasks(data);
    return environmentId == null
      ? all
      : all.filter((t) => t.environmentId === environmentId);
  }, [data, environmentId]);

  return { tasks, isLoading, isError, refetch, isRefetching };
}
