// NEEDS NATIVE REVIEW: first-pass Spanish (Mexican/U.S. neutral, tú form),
// written by Claude, not yet checked by a native speaker. See _meta in common.ts.
import type { Strings } from '../types';
import type en from '../en/season';

const season: Strings<typeof en> = {
  dates: {
    weekdaysShort: 'dom,lun,mar,mié,jue,vie,sáb',
    weekdaysLong: 'domingo,lunes,martes,miércoles,jueves,viernes,sábado',
    monthsShort: 'ene,feb,mar,abr,may,jun,jul,ago,sep,oct,nov,dic',
    monthsLong: 'enero,febrero,marzo,abril,mayo,junio,julio,agosto,septiembre,octubre,noviembre,diciembre',
    today: 'Hoy',
    tomorrow: 'Mañana',
    yesterday: 'Ayer',
    shortDay: '{{weekday}} {{day}} {{month}}',
    spokenDay: '{{day}} de {{month}}',
    clockHour: '{{hour}} {{ampm}}',
    clockMinute: '{{hour}}:{{minute}} {{ampm}}',
    am: 'a. m.',
    pm: 'p. m.',
  },
  status: {
    happened: 'Registrado en tu región',
    happening: 'Está pasando ahora',
    forecast: 'En el pronóstico',
    expected: 'Previsto',
    typically_around: 'Suele ser alrededor de',
    done: 'Hecho',
    not_needed: 'No hace falta este año',
  },
  actions: {
    mark_happened: 'Ya pasó aquí',
    mark_not_yet: 'Todavía no en mi casa',
    mark_done: 'Hecho',
    mark_not_needed: 'No hace falta',
    clear: 'Borrar mi respuesta',
  },
  sections: {
    now: 'Requiere atención ahora',
    ahead: 'Los próximos doce meses',
    settled: 'Ya pasó o está resuelto',
  },
  taskStates: {
    open: 'Por hacer',
    done: 'Hecho',
    not_needed: 'No hace falta',
  },
  frostRisk: {
    frost: 'Posible helada',
    freeze: 'Congelación',
    hard_freeze: 'Congelación fuerte',
  },
  cells: {
    noTemperature: 'Sin temperatura',
    degreesF: '{{temp}}°F',
    rain: '{{pct}}% lluvia',
    a11yHigh: 'máxima de {{temp}} grados Fahrenheit',
    a11yLow: 'mínima de {{temp}} grados Fahrenheit',
    a11yRain: '{{pct}} por ciento de probabilidad de lluvia',
  },
  credit: {
    providerFallback: 'el proveedor del pronóstico',
    forecastBy: 'Pronóstico: {{name}}.',
    forecastByAsOf: 'Pronóstico: {{name}}, actualizado a las {{time}} del {{day}}.',
  },
  frostNights: 'Heladas en el pronóstico: {{nights}}.',
  frostNight: '{{day}} ({{risk}})',
  alerts: {
    asOf: 'Pronóstico de las {{time}} del {{weekday}} {{day}} de {{month}}.',
    data: 'Datos: {{source}}.',
  },
  timeline: {
    range: 'del {{from}} al {{to}}',
    runsPast: 'Sigue después del final de esta línea de tiempo',
    beganBefore: 'Empezó antes del inicio de esta línea de tiempo',
    span: '{{from}} de {{fromYear}} a {{to}} de {{toYear}}',
    opensEvent: 'Abre este evento',
  },
  screen: {
    titleFallback: 'Tu plan de temporada',
    loadFailed: 'No se pudo cargar tu plan de temporada.',
    noForecast: 'Por ahora no hay pronóstico. Las fechas de abajo son las típicas de tu región, no el pronóstico de este año.',
    notSaved: 'No se guardó esa respuesta. Revisa tu conexión e inténtalo de nuevo.',
    yearAtAGlance: 'El año de un vistazo',
    empty: 'Todavía no hay nada en tu plan de temporada.',
    forecast: 'Pronóstico',
    whenHappened: '¿Cuándo pasó en tu casa?',
    happenedToday: 'Pasó hoy',
    happenedYesterday: 'Pasó ayer',
    happenedOn: 'Pasó el {{day}}',
    whyTaskA11y: '{{why}} de esta tarea. {{toggle}}.',
    hide: 'Ocultar',
    show: 'Mostrar',
    data: 'Datos: {{source}}',
  },
};

export default season;
