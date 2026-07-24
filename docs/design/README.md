# Design lab — source of truth

These files are the canonical visual reference for the PlantAdvocate app reskin.

- **`PlantAdvocate.dc.html`** — the pixel reference. Its `<style>` block defines
  the two-theme token system; each screen mock shows the intended layout,
  type scale, and component treatments (eyebrow labels, pill chips, the
  "specimen" header, the OUTSIDE → IN HERE lens, dashed "add" affordances).
- **`Explorations.dc.html`** — earlier explorations / alternates.

## Themes

| | Almanac (light) | Observatory (dark) |
|---|---|---|
| mood | warm field notebook | night observatory |
| accents | deep green `#2F4A33` / clay `#A9542F` | Okabe-Ito sky `#56B4E9` / amber `#E69F00` (colorblind-safe) |
| fonts | Newsreader serif | system sans + Menlo mono |

## Where the tokens live in the app

The token values are transcribed verbatim into **`mobile/src/theme/tokens.ts`**
(`ALMANAC` / `OBSERVATORY` palettes, `FONTS`, `SPACING`, `RADII`), and turned
into Paper MD3 themes by **`mobile/src/theme/ThemeProvider.tsx`**. Screens read
the active palette via `useAppTheme()`.

If a token value here and in `tokens.ts` ever disagree, **this file wins** —
update `tokens.ts` to match.

## Font note

The reference uses **Newsreader** (a Google font). Until the `.ttf` files are
bundled via `expo-font` (which requires a native rebuild), `tokens.ts` uses the
system-available serif stand-in (Georgia on iOS) so the reskin needs no rebuild.
Bundling Newsreader for an exact match is a follow-up.
