// Design tokens — the two-theme system from the design lab.
// Source of truth: docs/design/PlantAdvocate.dc.html (the pixel reference).
// Values are copied verbatim from that file's :root (light "Almanac") and
// [data-theme=dark] ("Observatory", Okabe-Ito colorblind-safe accents) blocks.

export type ThemeName = 'almanac' | 'observatory';

export interface Palette {
  bg: string;      // page background
  desk: string;    // recessed surface behind cards
  card: string;    // card surface
  card2: string;   // subtle/secondary card fill
  ink: string;     // primary text
  sub: string;     // secondary text
  faint: string;   // eyebrow labels / hints
  acc: string;     // accent (primary actions, "due" pills)
  accSoft: string; // accent tint fill
  warn: string;    // warnings / heat / clay
  warnSoft: string;
  good: string;    // healthy / done
  hedge: string;   // muted gold
  line: string;    // borders
  line2: string;   // faint borders
  btn: string;     // primary button bg
  btnInk: string;  // primary button text
  // Controls (the Controls row's tiles and other one-tap controls). Always
  // solid, never translucent, and checked by theme/contrast.test.ts:
  // label on fill at least 7:1, border against the card and the page at
  // least 3:1.
  tile: string;      // a tile's fill when its setting is off or it is a link
  tileInk: string;   // label and state words on `tile`
  tileBorder: string;
  tileOn: string;    // a tile's fill when its setting is on
  tileOnInk: string; // label and state words on `tileOn`
}

export interface Fonts {
  display: string; // headings — serif in light, system sans in dark
  label: string;   // eyebrow labels — serif in light, mono in dark
  numeric: string; // stats/numbers
}

// --- Light: "Almanac" (warm field-notebook) ---
export const ALMANAC: Palette = {
  bg: '#F7EFDD', desk: '#EAE2CD', card: '#FFFDF6', card2: 'rgba(255,253,246,0.65)',
  ink: '#2F4A33', sub: '#5A6B52', faint: '#6D5836',
  acc: '#2F4A33', accSoft: 'rgba(47,74,51,0.10)',
  warn: '#A9542F', warnSoft: 'rgba(169,84,47,0.08)',
  good: '#3F6B34', hedge: '#8A6414',
  line: '#CDBD9A', line2: '#E5D9BC',
  btn: '#2F4A33', btnInk: '#FFFDF6',
  tile: '#FFFDF6', tileInk: '#2F4A33', tileBorder: '#6F7F62',
  tileOn: '#2F4A33', tileOnInk: '#FFFDF6',
};

// --- Dark: "Observatory" (Okabe-Ito accents) ---
export const OBSERVATORY: Palette = {
  bg: '#131A1D', desk: '#0C1114', card: '#1A2327', card2: 'rgba(232,240,236,0.04)',
  ink: '#E8F0EC', sub: '#9FB3AB', faint: '#8DA39A',
  acc: '#56B4E9', accSoft: 'rgba(86,180,233,0.13)',
  warn: '#E69F00', warnSoft: 'rgba(230,159,0,0.12)',
  good: '#00B884', hedge: '#C8B273',
  line: 'rgba(232,240,236,0.22)', line2: 'rgba(232,240,236,0.12)',
  btn: '#56B4E9', btnInk: '#0C1114',
  tile: '#1A2327', tileInk: '#E8F0EC', tileBorder: '#7E918A',
  tileOn: '#56B4E9', tileOnInk: '#0C1114',
};

// --- Increase Contrast (iOS Accessibility > Display > Increase Contrast) ---
// A stronger palette, not just a darker one: every fill solid, secondary
// text pulled toward the ink, borders that read as lines.
export const ALMANAC_HIGH_CONTRAST: Palette = {
  bg: '#FBF7EC', desk: '#EFE8D6', card: '#FFFFFF', card2: '#FFFFFF',
  ink: '#1E3322', sub: '#3E4A37', faint: '#4A3A1E',
  acc: '#1E3322', accSoft: '#E3E8E1',
  warn: '#8A3D1C', warnSoft: '#F5E6DE',
  good: '#2C5224', hedge: '#6A4C0C',
  line: '#4A5A42', line2: '#8A9580',
  btn: '#1E3322', btnInk: '#FFFFFF',
  tile: '#FFFFFF', tileInk: '#1E3322', tileBorder: '#1E3322',
  tileOn: '#1E3322', tileOnInk: '#FFFFFF',
};

export const OBSERVATORY_HIGH_CONTRAST: Palette = {
  bg: '#000000', desk: '#000000', card: '#0B1012', card2: '#0B1012',
  ink: '#FFFFFF', sub: '#D3DEDA', faint: '#C2D1CB',
  acc: '#9AD5F7', accSoft: '#12303F',
  warn: '#FFB84D', warnSoft: '#3A2A0A',
  good: '#3EE0A8', hedge: '#E3CF92',
  line: '#B8C7C1', line2: '#6E807A',
  btn: '#9AD5F7', btnInk: '#000000',
  tile: '#0B1012', tileInk: '#FFFFFF', tileBorder: '#D3DEDA',
  tileOn: '#9AD5F7', tileOnInk: '#000000',
};

// Fonts. The reference uses Newsreader (serif) for light; until the font files
// are bundled (expo-font → needs a rebuild), we use the system-available serif
// stand-in. iOS ships Georgia + Menlo, so this needs no bundling and no rebuild.
export const ALMANAC_FONTS: Fonts = { display: 'Georgia', label: 'Georgia', numeric: 'Georgia' };
export const OBSERVATORY_FONTS: Fonts = { display: 'System', label: 'Menlo', numeric: 'Menlo' };

export const SPACING = { xs: 4, sm: 8, md: 12, lg: 16, xl: 24 } as const;
export const RADII = { chip: 12, card: 14, pill: 999 } as const;

export const PALETTES: Record<ThemeName, Palette> = { almanac: ALMANAC, observatory: OBSERVATORY };
export const HIGH_CONTRAST_PALETTES: Record<ThemeName, Palette> = {
  almanac: ALMANAC_HIGH_CONTRAST, observatory: OBSERVATORY_HIGH_CONTRAST,
};
export const FONTS: Record<ThemeName, Fonts> = { almanac: ALMANAC_FONTS, observatory: OBSERVATORY_FONTS };
