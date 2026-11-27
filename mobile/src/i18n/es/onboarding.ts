// NEEDS NATIVE REVIEW: first-pass Spanish (Mexican/U.S. neutral, tú form),
// written by Claude, not yet checked by a native speaker. See _meta in common.ts.
import type { Strings } from '../types';
import type en from '../en/onboarding';

const onboarding: Strings<typeof en> = {
  growingAreasTab: 'Áreas de cultivo',
  getStarted: 'Comenzar',
  next: 'Siguiente',
  skip: 'Omitir',
  slideOf: 'Página {{n}} de {{total}}',
  almanacTitle: 'Un almanaque para tu terreno',
  almanacBody: 'PlantAdvocate abre con una página para la semana: la fecha, la semana de la temporada '
    + 'y lo único que importa, como una helada que se acerca.',
  tasksTitle: 'Hasta tres cosas por hacer',
  tasksBody: 'Las tareas de esta semana vienen de tu plan de temporada y de las revisiones de tus plantas. '
    + 'Toca Hecho u Omitir y el plan sigue adelante.',
  controlsTitle: 'Tus controles, a la vista',
  controlsBody: 'Los avisos de helada, tu terreno, las zonas, °F o °C y los recordatorios de tareas están en una fila '
    + 'en la primera pantalla. Cada uno dice si está activado, y un toque lo cambia.',
  landTitle: 'Agrega tu terreno',
  landBody: 'Escribe una dirección o usa tu ubicación, y luego pon un marcador en tu casa. '
    + 'PlantAdvocate consulta mapas públicos para estimar el sol, dónde se junta el agua, el suelo, '
    + 'la zona de rusticidad y las fechas de helada. Si un valor parece incorrecto, “¿No es correcto? Corrígelo” '
    + 'te deja corregir cualquiera. Los mapas cubren terrenos en los Estados Unidos.',
  howTitle: 'Cómo lo sabemos',
  howBody: 'Cada pantalla tiene una página Cómo lo sabemos: de dónde viene cada valor, cómo se calculó '
    + 'y qué tan seguro es. Las plantas y las especies también muestran ahí sus fuentes.',
};

export default onboarding;
