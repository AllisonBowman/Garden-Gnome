// Which palette the app draws with, under the person's iOS display
// settings. Pure, so contrast.test.ts can pin it.
import { HIGH_CONTRAST_PALETTES, PALETTES, Palette, ThemeName } from './tokens';
import { solidPalette } from './contrast';

/** The iOS display settings the app follows (Settings > Accessibility >
 *  Display & Text Size). Differentiate Without Color is not exposed to
 *  React Native; the app meets it by construction instead: every state is
 *  a word, never a color alone. */
export interface DisplayPrefs {
  /** Increase Contrast: the stronger palette. */
  increaseContrast: boolean;
  /** Bold Text: heavier weights on labels the app styles itself. */
  boldText: boolean;
  /** Reduce Transparency: every translucent fill flattened to solid. */
  reduceTransparency: boolean;
}

export const NO_PREFS: DisplayPrefs = { increaseContrast: false, boldText: false, reduceTransparency: false };

/** The palette for a theme under the person's display settings. Pure. */
export function paletteFor(name: ThemeName, prefs: DisplayPrefs): Palette {
  if (prefs.increaseContrast) return HIGH_CONTRAST_PALETTES[name];
  return prefs.reduceTransparency ? solidPalette(PALETTES[name]) : PALETTES[name];
}

