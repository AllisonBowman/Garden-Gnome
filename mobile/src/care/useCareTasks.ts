import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { loadGardenCareData, readablePlants } from '../api/plants';
import {
  computeCareTasks, CareTask, unscheduledPlants, UnscheduledPlant,
} from './schedule';

export const CARE_TASKS_QUERY_KEY = ['careTasksData'] as const;

/**
 * Plants, each plant's care log, and full species records (plant lists embed
 * species WITHOUT care_schedules, so the schedules — the whole point — come
 * from each species' own record). One query feeds the to-do list, the growing
 * area calendar and the streak badges, and its load is shared with the
 * reminder planner (api/plants.ts loadGardenCareData), so a launch costs one
 * fan-out rather than three.
 */
export function useGardenCareData() {
  return useQuery({
    queryKey: CARE_TASKS_QUERY_KEY,
    queryFn: loadGardenCareData,
  });
}

export interface UseCareTasksResult {
  tasks: CareTask[];
  /** Plants whose species has no check schedule on record: nothing is
   *  scheduled for them, and nothing may claim they're fine. */
  unscheduled: UnscheduledPlant[];
  /** Plants left out because their log or species couldn't be read. */
  unreadCount: number;
  /** True once any load has arrived. A failed refresh keeps the last one,
   *  so "failed" means something only while this is false. */
  loaded: boolean;
  isLoading: boolean;
  isError: boolean;
  refetch: () => void;
  isRefetching: boolean;
}

const NOTHING = { tasks: [] as CareTask[], unscheduled: [] as UnscheduledPlant[], unreadCount: 0 };

/**
 * Next-due care tasks across all of the user's plants, recomputed against the
 * live clock. Pass an `growingAreaId` to scope to one growing area (the
 * calendar); omit it for everything (the to-do list). The heavy fetch is
 * shared under one query key, so both screens hit the cache, not the network.
 */
export function useCareTasks(growingAreaId?: number): UseCareTasksResult {
  const { data, isLoading, isError, refetch, isRefetching } = useGardenCareData();

  const derived = useMemo(() => {
    if (!data) return NOTHING;
    const input = {
      plants: readablePlants(data),
      logsByPlant: data.logsByPlant,
      speciesById: data.speciesById,
    };
    const here = <T extends { growingAreaId?: number }>(rows: T[]) => (
      growingAreaId == null ? rows : rows.filter((r) => r.growingAreaId === growingAreaId));
    const unread = new Set(data.unreadPlantIds);
    return {
      tasks: here(computeCareTasks(input)),
      unscheduled: here(unscheduledPlants(input)),
      unreadCount: data.plants.filter((p) => unread.has(p.id)
        && (growingAreaId == null || p.growing_area_id === growingAreaId)).length,
    };
  }, [data, growingAreaId]);

  return { ...derived, loaded: data != null, isLoading, isError, refetch, isRefetching };
}
