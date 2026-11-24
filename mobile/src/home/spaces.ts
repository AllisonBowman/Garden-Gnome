import { GrowingArea } from '../types';
import { VitalSpace } from '../types/site';
import { t } from '../i18n';

// "Your growing spaces" on Home. The server's vitals list them (zones of the
// property and every other space); when the feature is off Home builds the
// same list from the growing areas the app already reads.

export function spacesFromAreas(areas: GrowingArea[]): VitalSpace[] {
  return areas.map((a) => ({
    growing_area_id: a.id,
    name: a.name,
    kind: 'space' as const,
    vegetation_type: null,
    indoor: a.temp_exposure === 'indoor',
    plant_count: a.plant_count ?? 0,
  }));
}

/** Zones first (they are the land), then outdoor spaces, then indoor ones;
 *  the server's order within each. */
export function orderSpaces(spaces: VitalSpace[]): VitalSpace[] {
  const rank = (s: VitalSpace) => (s.kind === 'zone' ? 0 : s.indoor ? 2 : 1);
  return spaces
    .map((s, i) => ({ s, i }))
    .sort((a, b) => rank(a.s) - rank(b.s) || a.i - b.i)
    .map(({ s }) => s);
}

/** "3 plants, indoors" / "No plants yet, outdoors" / "1 plant, part of your land". */
export function spaceLine(space: VitalSpace): string {
  const plants = space.plant_count === 0
    ? t('home.spaces.noPlants')
    : t('home.spaces.plants', { count: space.plant_count });
  const where = space.kind === 'zone'
    ? t('home.spaces.zone')
    : space.indoor ? t('home.spaces.indoors') : t('home.spaces.outdoors');
  return t('home.spaces.line', { plants, where });
}
