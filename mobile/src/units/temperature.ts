// Temperatures in the person's unit, °F or °C. The server and the forecast
// speak °F; every temperature the app writes itself goes through here.
//
// The unit is a runtime setting (Controls row, Settings), unlike the
// language, so it lives in module state that UnitsProvider keeps current and
// the pure modules read when they build a sentence. A unit change remounts
// the screens (App.tsx keys the navigator on it), so nothing built with the
// old unit lingers. Under jest it is °F unless a test sets it.
//
// Numbers go through Intl.NumberFormat in the app's language, so "-2" gets
// the locale's minus sign and grouping.
import { localeTag, t } from '../i18n';

export type TempUnit = 'F' | 'C';

let current: TempUnit = 'F';

export function getTempUnit(): TempUnit {
  return current;
}

/** Called by UnitsProvider (and tests). */
export function setTempUnitForFormatting(unit: TempUnit): void {
  current = unit;
}

/** A Fahrenheit reading in `unit`, unrounded. */
export function fromFahrenheit(f: number, unit: TempUnit = current): number {
  return unit === 'C' ? (f - 32) * 5 / 9 : f;
}

/** A temperature difference (a span of degrees, not a reading) in `unit`. */
export function spanFromFahrenheit(df: number, unit: TempUnit = current): number {
  return unit === 'C' ? df * 5 / 9 : df;
}

let numberFormat: Intl.NumberFormat | null = null;

function formatNumber(n: number): string {
  try {
    numberFormat ??= new Intl.NumberFormat(localeTag, { maximumFractionDigits: 0 });
    return numberFormat.format(n);
  } catch {
    return String(Math.round(n));
  }
}

/** "35 °F" / "2 °C" from a Fahrenheit reading. */
export function formatTemp(f: number, unit: TempUnit = current): string {
  const n = formatNumber(Math.round(fromFahrenheit(f, unit)));
  return unit === 'C' ? t('units.tempC', { n }) : t('units.tempF', { n });
}

/** "35°" with no letter, for chart labels whose caption names the unit. */
export function formatDegrees(f: number, unit: TempUnit = current): string {
  return t('units.degrees', { n: formatNumber(Math.round(fromFahrenheit(f, unit))) });
}

/** A whole number in the unit, for sentences that place their own °F/°C. */
export function roundedTemp(f: number, unit: TempUnit = current): string {
  return formatNumber(Math.round(fromFahrenheit(f, unit)));
}

/** "°F" or "°C". */
export function unitSymbol(unit: TempUnit = current): string {
  return unit === 'C' ? t('units.symbolC') : t('units.symbolF');
}

/** What a screen reader says for the unit: "degrees Fahrenheit". */
export function unitSpoken(unit: TempUnit = current): string {
  return unit === 'C' ? t('units.spokenC') : t('units.spokenF');
}
