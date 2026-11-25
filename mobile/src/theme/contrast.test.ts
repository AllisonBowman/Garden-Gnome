// The contrast the redesign promises (WCAG 2.2): body text at least 4.5:1,
// large text and control borders at least 3:1, and control labels and the
// almanac's verdict line at least 7:1 (AAA), in all four palettes: Almanac
// and Observatory, each normal and under iOS Increase Contrast.
import { ALMANAC, HIGH_CONTRAST_PALETTES, OBSERVATORY, Palette } from './tokens';
import { contrastRatio, flatten, parseColor, solidPalette } from './contrast';
import { paletteFor } from './paletteFor';

const PALETTES: [string, Palette][] = [
  ['Almanac', ALMANAC],
  ['Observatory', OBSERVATORY],
  ['Almanac, Increase Contrast', HIGH_CONTRAST_PALETTES.almanac],
  ['Observatory, Increase Contrast', HIGH_CONTRAST_PALETTES.observatory],
];

test('the arithmetic matches known WCAG values', () => {
  expect(contrastRatio('#000000', '#FFFFFF')).toBeCloseTo(21, 5);
  expect(contrastRatio('#FFFFFF', '#FFFFFF')).toBeCloseTo(1, 5);
  expect(contrastRatio('#767676', '#FFFFFF')).toBeCloseTo(4.54, 2);
  expect(flatten('rgba(0,0,0,0.5)', '#FFFFFF')).toBe('#808080');
});

describe.each(PALETTES)('%s', (_name, p) => {
  test('control labels reach 7:1 on their fill, on and off', () => {
    expect(contrastRatio(p.tileInk, p.tile)).toBeGreaterThanOrEqual(7);
    expect(contrastRatio(p.tileOnInk, p.tileOn)).toBeGreaterThanOrEqual(7);
  });

  test('the verdict line and headings (ink) reach 7:1 on the card and the page', () => {
    expect(contrastRatio(p.ink, p.card)).toBeGreaterThanOrEqual(7);
    expect(contrastRatio(p.ink, p.bg)).toBeGreaterThanOrEqual(7);
  });

  test('body and secondary text reach 4.5:1 on the card and the page', () => {
    for (const fg of [p.sub, p.faint, p.acc, p.warn]) {
      expect(contrastRatio(fg, p.card)).toBeGreaterThanOrEqual(4.5);
      expect(contrastRatio(fg, p.bg)).toBeGreaterThanOrEqual(4.5);
    }
  });

  test('control borders reach 3:1 against the card and the page', () => {
    expect(contrastRatio(p.tileBorder, p.card)).toBeGreaterThanOrEqual(3);
    expect(contrastRatio(p.tileBorder, p.bg)).toBeGreaterThanOrEqual(3);
  });

  test('control fills are solid, never translucent', () => {
    for (const c of [p.tile, p.tileOn, p.tileBorder, p.tileInk, p.tileOnInk]) expect(parseColor(c).a).toBe(1);
  });

  test('the header button (Settings, Done) reaches 7:1 on its fill and 3:1 against the header', () => {
    expect(contrastRatio(p.btn, p.btnInk)).toBeGreaterThanOrEqual(7);
    expect(contrastRatio(p.btnInk, p.acc)).toBeGreaterThanOrEqual(3);
  });
});

test('Increase Contrast palettes are wholly solid', () => {
  for (const p of Object.values(HIGH_CONTRAST_PALETTES)) {
    for (const c of Object.values(p)) expect(parseColor(c).a).toBe(1);
  }
});

test('Reduce Transparency flattens every translucent token', () => {
  for (const p of [ALMANAC, OBSERVATORY]) {
    for (const c of Object.values(solidPalette(p))) expect(parseColor(c).a).toBe(1);
  }
});

test('the provider picks the stronger palette under Increase Contrast', () => {
  const off = { increaseContrast: false, boldText: false, reduceTransparency: false };
  expect(paletteFor('almanac', off)).toBe(ALMANAC);
  expect(paletteFor('almanac', { ...off, increaseContrast: true })).toBe(HIGH_CONTRAST_PALETTES.almanac);
  expect(parseColor(paletteFor('observatory', { ...off, reduceTransparency: true }).line).a).toBe(1);
});
