// NEEDS NATIVE REVIEW: first-pass Spanish (Mexican/U.S. neutral, tú form),
// written by Claude, not yet checked by a native speaker. See _meta in common.ts.
import type { Strings } from '../types';
import type en from '../en/controls';

const controls: Strings<typeof en> = {
  title: 'Controles',
  settings: 'Ajustes',
  settingsA11y: 'Ajustes',
  settingsHint: 'Abre todos los ajustes.',
  hintTurnOn: 'Toca dos veces para activarlo.',
  hintTurnOff: 'Toca dos veces para desactivarlo.',
  frost: {
    on: 'Avisos de helada: Activados',
    off: 'Avisos de helada: Desactivados',
    a11y: 'Avisos de helada y congelación',
    needsLand: 'Empiezan cuando agregues tu terreno.',
    onNote: 'Un aviso antes de una noche de helada o congelación.',
  },
  land: {
    named: 'Tu terreno: {{name}}',
    add: 'Agrega tu terreno',
    hint: 'Abre tu terreno.',
    addHint: 'Abre los pasos para agregar tu terreno.',
    note: 'Mueve el marcador o agrega otro lugar.',
  },
  zones: {
    count_one: 'Zonas: 1',
    count_other: 'Zonas: {{count}}',
    none: 'Zonas: ninguna aún. Agrega una zona',
    hint: 'Abre el mapa de zonas sobre la vista aérea.',
  },
  fix: {
    label: '¿No es correcto? Corrígelo',
    hint: 'Abre tu terreno, donde puedes corregir cualquier valor.',
    note: 'Corrige cualquier valor sobre tu terreno.',
  },
  units: {
    f: 'Temperaturas: °F',
    c: 'Temperaturas: °C',
    a11yF: 'Temperaturas en Fahrenheit',
    a11yC: 'Temperaturas en Celsius',
    hintToC: 'Toca dos veces para cambiar a Celsius.',
    hintToF: 'Toca dos veces para cambiar a Fahrenheit.',
  },
  reminders: {
    on: 'Recordatorios de tareas: Activados',
    off: 'Recordatorios de tareas: Desactivados',
    a11y: 'Recordatorios de tareas',
    onNote: 'En Ajustes eliges cada tipo de revisión.',
    offNote: 'Activa todos los tipos de revisión de plantas.',
  },
};

export default controls;
