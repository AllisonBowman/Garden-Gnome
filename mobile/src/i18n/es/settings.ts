// NEEDS NATIVE REVIEW: first-pass Spanish (Mexican/U.S. neutral, tú form),
// written by Claude, not yet checked by a native speaker. See ES_META in es/index.ts.
import type { Strings } from '../types';
import type en from '../en/settings';

const settings: Strings<typeof en> = {
  reminderToggles: {
    water: 'Revisiones de riego',
    fertilize: 'Revisiones de abonado',
    prune: 'Revisiones de poda',
    repot: 'Revisión de trasplante en primavera',
    rotate: 'Revisiones de giro',
  },
  remindersHint:
    'Recibe un aviso para revisar una planta cuando llega a su periodo habitual, según el '
    + 'calendario de revisiones de su especie y tu registro de cuidados. Las plantas que tocan el mismo día comparten una '
    + 'notificación. Una planta cuya especie no tiene un calendario de revisiones registrado no recibe '
    + 'recordatorios. Los recordatorios se planean con un mes de anticipación cada vez que abres '
    + 'PlantAdvocate, así que ábrela al menos una vez al mes para que sigan llegando.',
  remindersMobileOnly: 'Los recordatorios están disponibles en la app móvil (iOS y Android).',
  deleteConfirm: {
    title: '¿Eliminar tu cuenta?',
    body: 'Esto elimina para siempre tu cuenta, tus plantas, tu historial de cuidados y '
      + 'tus áreas de cultivo de PlantAdvocate. No se puede deshacer.',
    confirm: 'Eliminar para siempre',
  },
  deleteFailed: {
    title: 'No se pudo eliminar',
    body: 'PlantAdvocate no pudo eliminar tu cuenta. Revisa tu conexión e intenta de nuevo.',
  },
  censusFailed: {
    title: 'No se pudo guardar',
    body: 'PlantAdvocate no pudo comunicarse con el servidor para cambiar tu ajuste del '
      + 'censo, así que nada cambió. Revisa tu conexión e intenta de nuevo.',
  },
  notificationsDisabled: 'Notificaciones desactivadas',
  alertsNeedPermission: 'PlantAdvocate necesita permiso de notificaciones para las alertas de helada y del tiempo. Puedes activarlo en los ajustes de tu dispositivo.',
  remindersNeedPermission: 'PlantAdvocate necesita permiso de notificaciones para los recordatorios de cuidado. Puedes activarlo en los ajustes de tu dispositivo.',
  account: 'Cuenta',
  signedIn: 'Sesión iniciada',
  signOut: 'Cerrar sesión',
  deleteAccount: 'Eliminar cuenta',
  appearance: 'Apariencia',
  themeDark: '🌙 Observatorio (oscuro)',
  themeLight: '☀️ Almanaque (claro)',
  themeHint: 'Almanaque es el aspecto cálido de libreta de campo; Observatorio es un tema nocturno oscuro, apto para daltonismo.',
  careReminders: 'Recordatorios de cuidado',
  weatherShift: '🌦️ Ajustar el riego según el tiempo',
  weatherShiftHint: 'Mueve los recordatorios de riego uno o dos días para las plantas al aire libre y sin resguardo. Más tarde antes de la lluvia, antes en una ola de calor. Necesita una ubicación en el área de cultivo.',
  weatherShiftNeedsWater: 'Activa arriba los recordatorios de riego para usar esto.',
  frostAlerts: 'Alertas de helada y del tiempo',
  frostAlertsHint: 'Un aviso antes de una noche de helada o congelación y de otros momentos de tu plan de temporada, como máximo uno al día y ninguno entre las 9 p. m. y las 8 a. m. Cada alerta usa el pronóstico de la última vez que abriste la app y dice cuándo se hizo ese pronóstico, así que puede estar desactualizado. Necesita que hayas agregado tu terreno.',
  privacy: 'Privacidad y datos',
  seeCensus: 'Ver el censo',
  seeCensusA11y: 'Ver el censo de lo que cultivan todos',
  flowA11yShow: '{{title}}. {{destination}}. Mostrar detalles.',
  flowA11yHide: '{{title}}. {{destination}}. Ocultar detalles.',
  readPolicy: 'Leer la política completa',
  aboutSupport: 'Acerca de y soporte',
  build: 'compilación {{number}} ({{commit}})',
  aboutBody: 'Toda planta merece quien la defienda. Calendarios de cuidado, recordatorios y un motor de cuidados basado en una base de datos de especies seleccionada.',
  perenual: 'Datos de especies proporcionados en parte por Perenual (perenual.com).',
  helpSupport: 'Ayuda y soporte',
};

export default settings;
