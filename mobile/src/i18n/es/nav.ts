// NEEDS NATIVE REVIEW: first-pass Spanish (Mexican/U.S. neutral, tú form),
// written by Claude, not yet checked by a native speaker. See ES_META in es/index.ts.
import type { Strings } from '../types';
import type en from '../en/nav';

const nav: Strings<typeof en> = {
  propertySetup: 'Agrega tu terreno',
  land: 'Tu terreno',
  zoneMap: 'Mapa de zonas',
  season: 'La temporada',
  growingArea: 'Área de cultivo',
  plants: 'Mis plantas',
  plant: 'Planta',
  addPlant: 'Agregar planta',
  captureGarden: 'Recorre el jardín',
  species: 'Catálogo de especies',
  speciesDetail: 'Especie',
  almanac: 'Almanaque de especies',
  settings: 'Ajustes',
  census: 'Censo',
};

export default nav;
