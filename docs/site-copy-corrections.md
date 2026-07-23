# Site copy corrections — privacy & pricing vs. what the app actually does

**Important:** `site/` in this repo is a **recovered copy** of the live site,
not its source. The real pages are produced by a `build.py` generator that
lives on the desktop machine and deploys to Cloudflare Pages
(`site/README-SITE.md`). **Editing `site/*.html` here does not change the live
site** — and a future generator run on the desktop would overwrite these edits.

So this file is the portable artifact: apply these corrections to the
**generator templates on the desktop**, regenerate, and
`wrangler pages deploy site`. The matching edits have also been made to the
`site/*.html` copies here so the repo is internally consistent.

The corrections below fix two places where the published copy describes a
different product than the code runs (flagged in
`docs/plantadvocate-audit-2026-07.md`).

---

## 1. Privacy policy — photos are NOT sent to servers for identification

**Why:** species identification runs **on-device** (Apple Foundation Models +
Vision on iOS; Gemini Nano / ML Kit on Android). The photo is analyzed locally;
only the model's text guess is matched against the on-device catalog. Server
photo diagnosis is **not currently enabled**. So the claim that photos are
"transmitted to our servers for processing" is inaccurate today.

### `privacy.html` → "Photos" paragraph

**Was:**
> Photos you submit are transmitted to our servers for processing and are used
> solely to provide identification or diagnosis results.

**Now:**
> Species identification runs entirely on your device — the photo is analyzed
> locally and is not transmitted to our servers or to any third party. If we
> introduce server-based photo diagnosis in the future, photos submitted to
> that feature would be transmitted for processing, and we will update this
> policy before doing so.

### `privacy.html` → "PlantAdvocate uses artificial intelligence…" paragraph

**Was:** photos "may be processed by third-party AI service providers on our
behalf."

**Now:**
> PlantAdvocate uses a mix of on-device and server-based intelligence.
> Photo-based species identification and the gnome's tone run on your device and
> are not sent anywhere. Care advice is generated on our servers by a
> deterministic engine grounded in a curated plant-care database; some optional
> text features (such as free-text symptom questions) may be processed by a
> third-party AI service provider on our behalf, solely to generate your
> results, and only the text you provide — never your photos — is sent. …

### `privacy.html` → "How We Use Information" list item

**Was:** "Process photos you submit for species identification or diagnosis."
**Now:** "Analyze photos on your device for species identification (photos are
not uploaded for this); process photos server-side only if you use a
future diagnosis feature."

---

## 2. Pricing — paid tiers are not purchasable (no billing exists)

**Why:** the page shows Sprout $0 / Bloom $6 / Estate $12 per month, but there
is **no billing, subscription, or entitlement code** anywhere in the app or
backend. The page already hedges ("illustrative and subject to change"); make
the not-yet-available status unambiguous so it can't read as a live offer.

### `pricing.html` → intro sub-paragraph

**Add / strengthen:**
> PlantAdvocate is currently free while in beta. The paid plans below are a
> preview of what we're considering — they are **not available for purchase
> yet**, and prices may change before public launch.

**Product decision for you (not resolved here):** either (a) keep the tiers as a
"coming soon" preview as above, or (b) remove the paid tiers until billing is
actually built. If you later build billing (RevenueCat / StoreKit), that's a
separate feature, and the privacy policy will need a payments section.

---

## Applying this

1. Edit the generator templates on the desktop to match the above.
2. Regenerate the site.
3. `wrangler pages deploy site --project-name=<your-project>` (after
   `wrangler login`), or drag-drop the built folder in the Cloudflare dashboard.
4. Reconcile the generator into this repo eventually (see
   `site/README-SITE.md`) so these edits stop being at risk of being
   overwritten.
