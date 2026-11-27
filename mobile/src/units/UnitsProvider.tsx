import React, { useCallback, useContext, useEffect, useState } from 'react';
import { UnitsContext, UnitsCtx } from './context';
import { Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';
import { getLocales } from 'expo-localization';
import { TempUnit, setTempUnitForFormatting } from './temperature';

const UNIT_KEY = 'garden_gnome_temp_unit';

/** The phone's own unit (Settings > General > Language & Region), the
 *  default until the person picks one in the app. */
export function phoneTempUnit(): TempUnit {
  try {
    return getLocales()[0]?.temperatureUnit === 'celsius' ? 'C' : 'F';
  } catch {
    return 'F';
  }
}

async function loadUnit(): Promise<TempUnit | null> {
  const raw = Platform.OS === 'web'
    ? (typeof localStorage !== 'undefined' ? localStorage.getItem(UNIT_KEY) : null)
    : await SecureStore.getItemAsync(UNIT_KEY);
  return raw === 'C' || raw === 'F' ? raw : null;
}

async function saveUnit(unit: TempUnit): Promise<void> {
  if (Platform.OS === 'web') {
    if (typeof localStorage !== 'undefined') localStorage.setItem(UNIT_KEY, unit);
  } else {
    await SecureStore.setItemAsync(UNIT_KEY, unit);
  }
}

const Ctx = UnitsContext;

export function useUnits(): UnitsCtx {
  const c = useContext(Ctx);
  if (!c) throw new Error('useUnits must be used inside <UnitsProvider>');
  return c;
}

export function UnitsProvider({ children }: { children: React.ReactNode }) {
  const [unit, setUnitState] = useState<TempUnit>(() => {
    const u = phoneTempUnit();
    setTempUnitForFormatting(u);
    return u;
  });

  useEffect(() => {
    void loadUnit().then((stored) => {
      if (stored) {
        setTempUnitForFormatting(stored);
        setUnitState(stored);
      }
    });
  }, []);

  const setUnit = useCallback((next: TempUnit) => {
    setTempUnitForFormatting(next);
    setUnitState(next);
    void saveUnit(next);
  }, []);

  return <Ctx.Provider value={{ unit, setUnit }}>{children}</Ctx.Provider>;
}
