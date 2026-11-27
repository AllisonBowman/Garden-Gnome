// Contrast arithmetic (WCAG 2.2 relative luminance), and a way to make a
// palette fully solid for Reduce Transparency. Pure, so the ratios the
// palettes promise are pinned by contrast.test.ts.
import type { Palette } from './tokens';

type RGBA = { r: number; g: number; b: number; a: number };

export function parseColor(c: string): RGBA {
  const s = c.trim();
  const m = s.match(/^rgba?\(([^)]+)\)$/i);
  if (m) {
    const [r, g, b, a] = m[1].split(',').map((x) => Number(x.trim()));
    return { r, g, b, a: Number.isFinite(a) ? a : 1 };
  }
  const h = s.replace('#', '');
  const full = h.length === 3 ? h.split('').map((x) => x + x).join('') : h;
  return {
    r: parseInt(full.slice(0, 2), 16),
    g: parseInt(full.slice(2, 4), 16),
    b: parseInt(full.slice(4, 6), 16),
    a: 1,
  };
}

const hex2 = (n: number) => Math.round(Math.max(0, Math.min(255, n))).toString(16).padStart(2, '0').toUpperCase();

/** `color` painted over the solid `under`, as a solid hex. */
export function flatten(color: string, under: string): string {
  const c = parseColor(color);
  const u = parseColor(under);
  const mix = (x: number, y: number) => x * c.a + y * (1 - c.a);
  return `#${hex2(mix(c.r, u.r))}${hex2(mix(c.g, u.g))}${hex2(mix(c.b, u.b))}`;
}

export function luminance(color: string): number {
  const { r, g, b } = parseColor(color);
  const f = (v: number) => {
    const x = v / 255;
    return x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4);
  };
  return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
}

/** The contrast ratio of two colors, 1 to 21. A translucent foreground is
 *  first flattened over the background. */
export function contrastRatio(fg: string, bg: string): number {
  const solidBg = parseColor(bg).a < 1 ? flatten(bg, '#FFFFFF') : bg;
  const solidFg = parseColor(fg).a < 1 ? flatten(fg, solidBg) : fg;
  const a = luminance(solidFg);
  const b = luminance(solidBg);
  return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
}

/** The same palette with every translucent token flattened over the page
 *  (cards sit on the page, so that is what shows through them). */
export function solidPalette(p: Palette): Palette {
  const out = { ...p };
  (Object.keys(out) as (keyof Palette)[]).forEach((k) => {
    if (parseColor(out[k]).a < 1) out[k] = flatten(out[k], k === 'line' || k === 'line2' ? p.card : p.bg);
  });
  return out;
}
