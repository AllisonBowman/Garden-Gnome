// NEEDS NATIVE REVIEW: first-pass Spanish (Mexican/U.S. neutral, tú form),
// written by Claude, not yet checked by a native speaker. See _meta in common.ts.
import type { Strings } from '../types';
import type en from '../en/howWeKnow';

const howWeKnow: Strings<typeof en> = {
  button: 'Cómo lo sabemos',
  buttonA11y: 'Cómo lo sabemos',
  buttonHint: 'Abre las fuentes, cómo se calculó cada valor y qué tan seguro es.',
  title: 'Cómo lo sabemos',
  intro: 'De dónde viene cada valor de esta pantalla, cómo se calculó y qué tan seguro es.',
  close: 'Listo',
  closeA11y: 'Cerrar Cómo lo sabemos',
  est: 'aprox.',
  estA11y: 'aproximado',
  checking: 'Consultando',
  checkingA11y: 'Todavía consultando',
  howSure: 'Qué tan seguro: {{label}}',
  howSureLead: 'Qué tan seguro:',
  source: 'Fuente: {{source}}',
  empty: 'Todavía no hay nada que explicar en esta pantalla.',
  sections: {
    almanac: 'La línea del almanaque',
    weather: 'El tiempo',
    land: 'Tu terreno',
    season: 'La temporada que viene',
    tasks: 'Las tareas de esta semana',
    map: 'El mapa',
    zones: 'Tus zonas',
    notes: 'Notas',
    marks: 'Qué significan las marcas',
  },
  weekMethod: 'La semana de la temporada se cuenta desde el primer día de la temporada en el calendario: la primavera desde el 1 de marzo, el verano desde el 1 de junio, el otoño desde el 1 de septiembre y el invierno desde el 1 de diciembre. La semana 1 son los primeros siete días.',
  headlineFrom: 'Lo único que importa viene de tu plan de temporada y del pronóstico. La nota completa de hoy: {{text}}',
  headlineLocal: 'Lo único que importa se calcula en este teléfono a partir del pronóstico y de lo que toca esta semana.',
  forecastFetched: 'Pronóstico de {{name}}, consultado {{when}}.',
  estBody: 'Un valor marcado “aprox.” es una estimación a partir de mapas públicos o de un modelo. Puedes corregir cualquiera en Tu terreno con “¿No es correcto? Corrígelo”.',
  checkingBody: 'Algunos servicios de mapas públicos responden despacio. Un valor marcado “Consultando” se completa cuando llega, y PlantAdvocate sigue intentándolo.',
  unitsNote: 'Los pronósticos y el plan de temporada llegan en °F. PlantAdvocate convierte las temperaturas que escribe; algunas notas escritas por el servidor pueden seguir en °F.',
  taskReason: '{{task}}: {{reason}}',
};

export default howWeKnow;
