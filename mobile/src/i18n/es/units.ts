// NEEDS NATIVE REVIEW: first-pass Spanish (Mexican/U.S. neutral, tú form),
// written by Claude, not yet checked by a native speaker. See _meta in common.ts.
import type { Strings } from '../types';
import type en from '../en/units';

const units: Strings<typeof en> = {
  tempF: '{{n}}°F',
  tempC: '{{n}}°C',
  degrees: '{{n}}°',
  symbolF: '°F',
  symbolC: '°C',
  spokenF: 'grados Fahrenheit',
  spokenC: 'grados Celsius',
};

export default units;
