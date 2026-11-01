import { apiClient } from './client';

// GET /census/summary, read defensively.
//
// The Census tab once threw on first open because the screen read a key the
// server didn't send (Object.entries of undefined). Today's production API
// still speaks the pre-rename names (total_environments, environments_by_type),
// and a later server may drop a field or send a null. None of that should cost
// more than one blank card, so the screen never reads the raw answer: it reads
// this view, where every field has a known shape. A value the server didn't
// report is null and shown as a dash, never as a made-up 0.
//
// There is deliberately no census sync here. Pushing the community census is
// an operator job (POST /census/sync takes an operator credential), not a
// button for caretakers.

export interface CensusSpeciesCount {
  species_id: number;
  common_name: string;
  count: number;
}

export interface CensusView {
  total_plants: number | null;
  total_growing_areas: number | null;
  /** Area counts by kind of place; null when the server didn't say. */
  growing_areas_by_type: Record<string, number> | null;
  /** Most-grown first, as the server sorts it; null when the server didn't say. */
  species_distribution: CensusSpeciesCount[] | null;
}

const count = (v: unknown): number | null =>
  (typeof v === 'number' && Number.isFinite(v) && v >= 0 ? v : null);

function countsByKey(v: unknown): Record<string, number> | null {
  if (!v || typeof v !== 'object' || Array.isArray(v)) return null;
  const out: Record<string, number> = {};
  for (const [key, raw] of Object.entries(v as Record<string, unknown>)) {
    const n = count(raw);
    if (n !== null) out[key] = n;
  }
  return out;
}

function speciesCounts(v: unknown): CensusSpeciesCount[] | null {
  if (!Array.isArray(v)) return null;
  const rows: CensusSpeciesCount[] = [];
  for (const row of v) {
    const r = (row && typeof row === 'object' ? row : {}) as Record<string, unknown>;
    const n = count(r.count);
    if (typeof r.species_id === 'number' && typeof r.common_name === 'string' && n !== null) {
      rows.push({ species_id: r.species_id, common_name: r.common_name, count: n });
    }
  }
  return rows;
}

/** Shape whatever the server answered into something the screen can always
 *  render. Reads the current key names first and the pre-rename ones second
 *  (garden-gnome/app/models/schemas.py, with_pre_rename_census_keys). */
export function normalizeCensusSummary(raw: unknown): CensusView {
  const r = (raw && typeof raw === 'object' && !Array.isArray(raw) ? raw : {}) as Record<string, unknown>;
  const byType = countsByKey(r.growing_areas_by_type) ?? countsByKey(r.environments_by_type);
  const reportedAreas = count(r.total_growing_areas) ?? count(r.total_environments);
  return {
    total_plants: count(r.total_plants),
    total_growing_areas: reportedAreas
      ?? (byType ? Object.values(byType).reduce((a, b) => a + b, 0) : null),
    growing_areas_by_type: byType,
    species_distribution: speciesCounts(r.species_distribution),
  };
}

export async function fetchCensusSummary(): Promise<CensusView> {
  const client = await apiClient();
  const { data } = await client.get<unknown>('/census/summary');
  return normalizeCensusSummary(data);
}
