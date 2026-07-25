import React, { createContext, useContext, useEffect, useState } from 'react';
import { Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';
import {
  Provider as PaperProvider, MD3LightTheme, MD3DarkTheme,
} from 'react-native-paper';
import { PALETTES, FONTS, ThemeName, Palette, Fonts } from './tokens';

const THEME_KEY = 'garden_gnome_theme';

// Build a Paper MD3 theme from a palette so stock Paper components adopt the
// design-lab colors even before a screen is hand-restyled.
function buildPaperTheme(name: ThemeName) {
  const p = PALETTES[name];
  const base = name === 'observatory' ? MD3DarkTheme : MD3LightTheme;
  return {
    ...base,
    dark: name === 'observatory',
    colors: {
      ...base.colors,
      primary: p.acc,
      onPrimary: p.btnInk,
      secondary: p.sub,
      background: p.bg,
      surface: p.card,
      surfaceVariant: p.desk,
      onSurface: p.ink,
      onSurfaceVariant: p.sub,
      outline: p.line,
      outlineVariant: p.line2,
      error: p.warn,
      // Flatten elevation tints so cards read as paper, not tinted grey.
      elevation: {
        level0: p.bg, level1: p.card, level2: p.card,
        level3: p.card, level4: p.card, level5: p.card,
      },
    },
  };
}

interface ThemeCtx {
  name: ThemeName;
  palette: Palette;
  fonts: Fonts;
  toggle: () => void;
}

const Ctx = createContext<ThemeCtx | null>(null);

/** Access the active palette/fonts and the light/dark toggle. */
export function useAppTheme(): ThemeCtx {
  const c = useContext(Ctx);
  if (!c) throw new Error('useAppTheme must be used inside <AppThemeProvider>');
  return c;
}

async function loadTheme(): Promise<ThemeName | null> {
  const raw = Platform.OS === 'web'
    ? (typeof localStorage !== 'undefined' ? localStorage.getItem(THEME_KEY) : null)
    : await SecureStore.getItemAsync(THEME_KEY);
  return raw === 'observatory' || raw === 'almanac' ? raw : null;
}

async function saveTheme(name: ThemeName): Promise<void> {
  if (Platform.OS === 'web') {
    if (typeof localStorage !== 'undefined') localStorage.setItem(THEME_KEY, name);
  } else {
    await SecureStore.setItemAsync(THEME_KEY, name);
  }
}

export function AppThemeProvider({ children }: { children: React.ReactNode }) {
  const [name, setName] = useState<ThemeName>('almanac');

  useEffect(() => {
    void loadTheme().then((stored) => { if (stored) setName(stored); });
  }, []);

  const toggle = () => {
    setName((prev) => {
      const next: ThemeName = prev === 'almanac' ? 'observatory' : 'almanac';
      void saveTheme(next);
      return next;
    });
  };

  const value: ThemeCtx = {
    name,
    palette: PALETTES[name],
    fonts: FONTS[name],
    toggle,
  };

  return (
    <Ctx.Provider value={value}>
      <PaperProvider theme={buildPaperTheme(name)}>{children}</PaperProvider>
    </Ctx.Provider>
  );
}
