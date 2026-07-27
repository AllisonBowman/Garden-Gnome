# Accessibility — plantadvocate.ai

> **STATUS: WCAG 2.1 AA issues fixed in markup (2026-07-27).** Automated and
> manual-inspection checks pass. The parts that need a real screen reader and a
> real keyboard are listed at the bottom and have **not** been done.

## First: Cloudflare cannot do this

There is no Cloudflare product, setting, or rule that makes a site accessible.
Cloudflare moves and caches bytes; accessibility is a property of the bytes.

The thing that *is* usually meant by "accessibility through Cloudflare" is
injecting a third-party **accessibility overlay** (accessiBe, UserWay,
AudioEye) via a Worker, a Snippet, or Zaraz. That is worth actively avoiding:

- Overlays do not confer legal compliance. They sit on top of markup that is
  still broken underneath.
- They are a **litigation magnet rather than a shield**. Hundreds of US ADA
  lawsuits have been filed against sites that had an overlay installed — the
  overlay is discoverable evidence that the operator knew about the obligation
  and bought a widget instead of fixing the site.
- The National Federation of the Blind has formally condemned the largest
  vendor, and the "Overlay Fact Sheet" opposing them carries signatures from
  hundreds of accessibility practitioners, including blind users of the tools.
- They frequently make things *worse* — hijacking keyboard focus, fighting the
  user's own assistive tech, and announcing controls that don't exist.

Real conformance comes from the HTML and CSS. Those live in `site/`, so that is
where this work was done.

*Not legal advice.* "ADA compliance" is a legal determination, not a build
step. What is achievable in code is conformance to **WCAG 2.1 Level AA**, the
standard the DOJ adopted for Title II entities in 2024 and the benchmark courts
have consistently referenced for commercial sites. That is the target used here.

---

## What was wrong, and what changed

All 14 pages. Verified by measurement, not by eye.

### Colour contrast — WCAG 1.4.3 (AA)

The `--clay` accent failed everywhere it was used as text:

| where | before | after |
|---|---|---|
| section labels, tier numbers on `--paper` | **4.39:1** | **5.63:1** |
| testimony labels on the marigold tint | **4.07:1** | **5.22:1** |
| `.problem-card .mark` on `--ink-soft` | **2.21:1** | **5.00:1** |

`--clay` darkened `#A9542F` → `#904728` for light backgrounds. One accent
cannot serve both a light and a dark background, so dark contexts get a new
`--clay-on-dark` `#E09A75`. Every text pair on the site now measures ≥ 4.5:1;
the lowest is the `--leaf` accent at 4.73:1.

The `#A9542F` remaining in `community-garden.html` is an SVG fill in a
decorative illustration, not text. Non-text content needs 3:1 and it measures
4.39:1, so it stays as drawn.

### Bypass blocks — WCAG 2.4.1 (A)

No skip link on any page, and no `<main>` landmark to skip *to*. A keyboard or
screen-reader user had to traverse the whole nav on every page.

Added a real skip link — visually hidden, visible on focus, contrast 6.60:1 —
and wrapped page content in `<main id="main" tabindex="-1">`. The `tabindex`
is what makes focus actually land there when the link is followed.

### Heading structure — WCAG 1.3.1 (A)

Every page jumped from `h2` to `h4`, because the footer columns were `h4`.
`contact.html` and `recommendations.html` jumped `h1` → `h4`; `pricing.html`
also had `h1` → `h3` for its tier cards.

Footer column headings are now `h2`, pricing tiers are now `h2`, and the CSS
selectors moved with them so nothing changed visually. Main content was already
correct — `h1` → `h2` → `h3` throughout.

### Form labels — WCAG 3.3.2 (A)

The beta signup on `index.html` had a placeholder and no label. A placeholder
is not a label: it disappears on input and many screen readers ignore it.
Added a `.visually-hidden` `<label for="email-input">`.

### Also added

`aria-current="page"` on the active nav link, so a screen reader announces
which page you're on rather than reading seven identical links.

### Already correct before this work

Worth recording so nobody redoes it: `lang` on every `<html>`, visible `:focus`
styles, `prefers-reduced-motion` support, semantic `<nav>`/`<header>`/`<footer>`,
and no images at all — so no missing `alt` text anywhere.

---

## ⚠️ These edits are fragile until the generator is reconciled

`site/` is **built output**, not source. Per `site/README-SITE.md`, the static
site generator (`build.py` and its templates) still lives on the desktop
machine. **A generator run will silently overwrite everything above**, exactly
as it threatens to overwrite the July 19 privacy-policy edit.

This is the same pathology that put an unversioned build into production for
four days (see `docs/deploys.md`) — source of truth on one machine, edits made
to the deployed artifact. It has already cost this project a day.

Either reconcile the generator into this repo and point it at `site/`, or
retire it and make `site/` the source. Until one of those happens, treat every
fix here as provisional.

---

## Not done — needs a human

Automated checks and measurement cover perhaps half of WCAG. These need real
assistive technology and are worth doing before claiming conformance publicly:

- **Keyboard-only pass.** Tab through every page. Confirm the skip link is
  first, focus order matches visual order, nothing is reachable but invisible,
  and no trap.
- **Screen reader pass.** VoiceOver on macOS/iOS is free and installed. Listen
  to each page's heading outline and landmark list.
- **200% zoom and 320px reflow** — WCAG 1.4.10. The layout is fluid, but this
  is untested.
- **Focus visibility against every background** — WCAG 2.4.7. Styles exist;
  their contrast in each section is unmeasured.
- **An `accessibility` statement page**, linked in the footer, with a contact
  route for access problems. Standard practice and often the first thing a
  plaintiff's firm looks for.
