// NEEDS NATIVE REVIEW: first-pass Spanish (Mexican/U.S. neutral, tú form),
// written by Claude, not yet checked by a native speaker. See _meta in common.ts.
import type { Strings } from '../types';
import type en from '../en/notifications';

const notifications: Strings<typeof en> = {
  careVerbs: {
    water: 'revisión',
    fertilize: 'revisión de abonado',
    prune: 'revisión de poda',
    repot: 'revisión de raíces',
    rotate: 'revisión para girarla',
  },
  windowWords: {
    fertilize: 'abonado',
    prune: 'poda',
    rotate: 'giro',
  },
  repotTitle: '🪴 Revisión de primavera de {{name}}',
  repotBody: 'Échale un vistazo a {{name}}: ¿las raíces salen de la maceta? ¿Se ven la corona o las raíces en la superficie? ¿Se marchita poco después de regarla o dejó de crecer? Si es así, trasplántala, o solo agrega sustrato nuevo encima.',
  lookTitle: '🪴 Conviene revisar a {{name}}',
  waterBody: 'Revisa a {{name}}: {{been}}. {{check}}',
  been_one: 'ha pasado {{count}} día',
  been_other: 'han pasado {{count}} días',
  windowTitle: '🪴 Es momento de revisar a {{name}}',
  windowBody: '{{name}} llegó a su temporada de {{window}}. Échale un vistazo y decide si lo necesita.',
  lookBody: 'Conviene revisar a {{name}}. Decide si necesita algo.',
  batchTitle_one: '🪴 Conviene revisar {{count}} planta hoy',
  batchTitle_other: '🪴 Conviene revisar {{count}} plantas hoy',
  batchItem: '{{name}}: {{verb}}',
  more: ' +{{count}} más',
  waterCheck: {
    moist: 'Según sus fuentes: {{regime}}; riega si la superficie se siente seca.',
    depth: 'Toca el suelo a {{depth}} de profundidad; riega solo si ahí está seco.',
    regime: 'Según sus fuentes: {{regime}}; toca el suelo antes de regar.',
    plain: 'Toca el suelo antes de regar.',
  },
  channel: 'Recordatorios de cuidado',
};

export default notifications;
