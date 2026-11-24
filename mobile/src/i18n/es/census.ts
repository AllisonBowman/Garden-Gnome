// NEEDS NATIVE REVIEW: first-pass Spanish (Mexican/U.S. neutral, tú form),
// written by Claude, not yet checked by a native speaker. See _meta in common.ts.
import type { Strings } from '../types';
import type en from '../en/census';

const census: Strings<typeof en> = {
  loadFailed: 'No se pudo cargar el censo.',
  almanacEyebrow: 'Almanaque de especies',
  almanacTitle: 'Lee el catálogo ›',
  almanacBody: 'Todas las especies que tenemos, con su perfil de cuidados y qué tan exigente es cuidarlas, y cuáles le van bien a cada una de tus áreas de cultivo.',
  plants: 'Plantas',
  growingAreas: 'Áreas de cultivo',
  areasByType: 'Áreas de cultivo por tipo',
  noAreas: 'Todavía no hay espacios de cultivo. Agrega uno desde Tus espacios de cultivo en Inicio.',
  topSpecies: 'Especies principales',
  noPlants: 'Todavía no hay plantas. Cuando agregues algunas, aquí aparecerán las que más cultivas.',
};

export default census;
