// NEEDS NATIVE REVIEW: first-pass Spanish (Mexican/U.S. neutral, tú form),
// written by Claude, not yet checked by a native speaker. See _meta in common.ts.
import type { Strings } from '../types';
import type en from '../en/onboarding';

const onboarding: Strings<typeof en> = {
  growingAreasTab: 'Áreas de cultivo',
  getStarted: 'Comenzar',
  next: 'Siguiente',
  skip: 'Omitir',
  welcomeTitle: 'Te damos la bienvenida a PlantAdvocate',
  welcomeBody: 'PlantAdvocate te ayuda a cuidar tu terreno y las plantas que crecen en él, a lo largo de las temporadas.',
  landTitle: 'Agrega tu terreno',
  landBody: 'Escribe una dirección o usa tu ubicación, y luego pon un marcador en tu casa. '
    + 'PlantAdvocate consulta mapas públicos para estimar el sol, dónde se junta el agua, el suelo, '
    + 'la zona de rusticidad y las fechas de helada. Cada estimación dice qué tan segura es y de dónde viene, '
    + 'y puedes corregir cualquiera de ellas. Los mapas cubren terrenos en los Estados Unidos.',
  seeTitle: 'Mira tu terreno',
  seeBody: 'Inicio muestra un mapa de tu terreno con las capas Sol, Árboles y Agua, el pronóstico del tiempo '
    + 'y una línea de tiempo de la temporada. Cada paso dice qué hacer y por qué.',
  plantsTitle: 'Agrega plantas y registra cuidados',
  plantsBody: 'Agrega cada planta donde crece y luego toca para registrar riego, abonado y más. '
    + 'Cada especie tiene datos de cuidado y riesgos, con fuentes cuando se conocen. '
    + 'La página de cada planta también da consejos de cuidado, calculados con reglas fijas a partir de su especie y su registro de cuidados.',
};

export default onboarding;
