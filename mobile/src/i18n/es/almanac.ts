// NEEDS NATIVE REVIEW: first-pass Spanish (Mexican/U.S. neutral, tú form),
// written by Claude, not yet checked by a native speaker. See _meta in common.ts.
import type { Strings } from '../types';
import type en from '../en/almanac';

const almanac: Strings<typeof en> = {
  tiers: {
    beginner: 'Principiante',
    intermediate: 'Intermedio',
    fussy: 'Exigente',
  },
  light: {
    low: '◐ poca',
    medium: '◑ media',
    bright_indirect: '☀ indirecta brillante',
    direct: '☀☀ sol directo',
    noDirect: '☀ sin sol directo',
    upTo: '☀ hasta {{hours}} h de sol directo',
    footcandles: '☀ {{fc}}+ bujías-pie',
  },
  regime: {
    keep_moist: '💧 siempre húmedo',
    keep_barely_moist: '💧 apenas húmedo',
    dry_surface_between: '💧 superficie seca entre riegos',
    dry_thoroughly_between: '💧 seco del todo entre riegos',
    every: '💧 cada {{min}}–{{max}} d',
  },
  screen: {
    all: 'Todas',
    owned: '✿ tú tienes esta',
    loadFailedName: 'el Almanaque',
    intro_one: 'Un recuento vivo de lo que cultiva la gente: {{count}} especie en el catálogo. Lee cualquier especie para conocer sus costumbres.',
    intro_other: 'Un recuento vivo de lo que cultiva la gente: {{count}} especies en el catálogo. Lee cualquier especie para conocer sus costumbres.',
    introOwned_one: 'Un recuento vivo de lo que cultiva la gente: {{count}} especie en el catálogo, {{owned}} en tu colección. Lee cualquier especie para conocer sus costumbres.',
    introOwned_other: 'Un recuento vivo de lo que cultiva la gente: {{count}} especies en el catálogo, {{owned}} de ellas en tu colección. Lee cualquier especie para conocer sus costumbres.',
    search_one: 'Buscar en {{count}} especie…',
    search_other: 'Buscar entre {{count}} especies…',
    anywhere: 'En cualquier lugar',
    fits: 'Apta para {{name}}',
    gradedOnly: 'Solo se califica donde el catálogo registra humedad, temperatura o luz.',
    gradedOnlyUngraded_one: 'Solo se califica donde el catálogo registra humedad, temperatura o luz; {{count}} especie todavía no tiene nada que calificar y no está en ningún nivel.',
    gradedOnlyUngraded_other: 'Solo se califica donde el catálogo registra humedad, temperatura o luz; {{count}} especies todavía no tienen nada que calificar y no están en ningún nivel.',
    shown_one: 'Especies · {{count}} visible',
    shown_other: 'Especies · {{count}} visibles',
    fitNote: 'Se muestran las especies que no tienen nada registrado en contra de {{area}} y que tienen al menos una cosa confirmada. Si falta una planta, quizá el catálogo todavía no puede juzgarla para este lugar. {{rankOrder}}',
    tryAgain: 'Intentar de nuevo',
    checking: 'Revisando qué le va bien a ese lugar…',
    noMatch: 'No hay coincidencias. Prueba otro nombre o amplía el filtro.',
  },
};

export default almanac;
