# PlantAdvocate marketing site — recovered artifact

**⚠️ This folder is the *built* site, not the source.** The static-site
generator (`build.py` + its source/templates) still lives on the desktop
machine and has **not** been reconciled into this repo yet. Until it is,
treat these files as the working copy of record — but reconcile the generator
here as soon as practical, and re-point it at this folder as its output, or
future generator runs on the desktop will silently overwrite the edits made
here (starting with the July 19, 2026 privacy-policy update).

## What this is

The 14 production pages of https://plantadvocate.ai, recovered from the live
Cloudflare Pages deployment on 2026-07-19, then edited in place:

- All pages are fully self-contained (inline CSS, no local JS, no image
  assets; fonts load from Google Fonts). There are no favicon files — the
  deployment serves a fallback page for unmatched paths.
- Cloudflare's serve-time injections were stripped so these files match the
  original artifact: email obfuscation (`/cdn-cgi/l/email-protection` +
  `email-decode.min.js`) was decoded back to real `mailto:` links, and the
  challenge-platform `<script>` blob was removed from every page.
- `privacy.html` was then updated (effective date 2026-07-19): new "Account
  Information" section (Apple/Google sign-in, name + email, Apple private
  relay, account identifier, no marketing/tracking), in-app account deletion
  under "Your Rights and Choices" (Settings → Delete Account, effective
  immediately, email as alternative), and an explicit opt-in/off-by-default
  sentence for anonymized community data sharing.
- Contact-email sweep: the only contact address anywhere is
  `support@plantadvocate.ai` (the `you@email.com` strings are form input
  placeholders, not contacts).

## Deploying

The site is hosted on **Cloudflare Pages**. Two options:

1. **Wrangler** (once authenticated): from the repo root —
   `npx wrangler pages deploy site --project-name=<pages-project-name>`.
   Requires a one-time `npx wrangler login` (browser) or a
   `CLOUDFLARE_API_TOKEN` env var.
2. **Dashboard drag-drop:** Cloudflare dashboard → Workers & Pages → the
   PlantAdvocate Pages project → Create deployment → upload the contents of
   this `site/` folder.

## To reconcile later (desktop machine)

- [ ] Copy `build.py` + source/templates into this repo (e.g. `site-src/`)
- [ ] Diff generator output against these recovered pages (this folder has
      the newer privacy text — port those edits INTO the source, don't
      regenerate over them)
- [ ] Point the generator's output at `site/` and make deploys flow
      source → build → deploy from this repo
