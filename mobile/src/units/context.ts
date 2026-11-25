// The °F/°C context on its own, with no storage imports, so light modules
// (the crash card's screen wrapper) can read the unit.
import { createContext, useContext } from 'react';
import type { TempUnit } from './temperature';

export interface UnitsCtx {
  unit: TempUnit;
  setUnit: (unit: TempUnit) => void;
}

export const UnitsContext = createContext<UnitsCtx | null>(null);

/** The unit, or °F outside a provider (tests, the crash card). */
export function useTempUnitOrDefault(): TempUnit {
  return useContext(UnitsContext)?.unit ?? 'F';
}
