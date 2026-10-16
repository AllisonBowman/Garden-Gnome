# PlantAdvocate marketing site

**This folder is the built site, and right now it is the only correct copy.**
The live site at https://plantadvocate.ai is *not* this folder. It was
generated on July 17, 2026 by the static-site generator on the desktop machine
(`build.py` and its templates), which has never been brought into this repo.

> **Do not run the desktop generator again until it has been reconciled with
> this folder** (see "Reconciling the generator" below). Running it and
> deploying would put the July 17 pages back: a privacy policy that says "we
> don't collect your precise location", a support page about subscriptions and
> Restore Purchases, paid pricing tiers, and an FAQ that calls the app
> indoor-only. The app links to the privacy and support pages, and App Review
> reads them.

## What is here

13 self-contained pages (inline CSS, no local JS files, no images; fonts load
from Google Fonts):

`index.html`, `how-it-works.html`, `pricing.html`, `nurseries.html`,
`community-garden.html`, `faq.html`, `about.html`, `contact.html`,
`support.html`, `privacy.html`, `recommendations.html`, `resources.html`,
`conservation.html`.

The app links to two of them (`mobile/src/support.ts`):
`PRIVACY_URL = https://plantadvocate.ai/privacy.html` and
`SUPPORT_URL = https://plantadvocate.ai/support.html`. Cloudflare answers both
with a 308 to `/privacy` and `/support`, which is fine.

History:

- 2026-07-19: recovered from the live Cloudflare Pages deployment, with
  Cloudflare's serve-time injections stripped (email obfuscation decoded back
  to `mailto:` links, the challenge-platform script removed). Cloudflare adds
  both back when it serves the pages, so `curl` shows `[email protected]`
  where the files say `support@plantadvocate.ai`. That is expected.
- 2026-10-16: rewritten against the code on `care-advice-honesty` for the App
  Store submission. The privacy policy is new (effective October 16, 2026).
  Support points at in-app deletion. Pricing says the app is free. The FAQ
  covers outdoor gardens. "Verified" became "cited", and the sources named are
  the ones the catalog's citations actually point to. Every form that sent
  nothing is now a `mailto:` link. The placeholder testimonials page is gone.
  The community garden demo no longer sets a cookie.

## Deploying

The site is a Cloudflare Pages project. You need to be logged in once:
`npx wrangler login` (opens a browser), or set `CLOUDFLARE_API_TOKEN` to a
token with Pages edit rights.

**1. Find the project name and its production branch** (once):

```bash
npx wrangler pages project list
npx wrangler pages deployment list --project-name=<project>
```

The project is the one whose domains include `plantadvocate.ai`. Its
production branch is the Branch shown on the deployment whose Environment is
Production (often `main`).

**2. Check the links** (from the repo root; must end "0 broken"):

```bash
python3 - site <<'EOF'
import pathlib, re, sys
from html.parser import HTMLParser
site = pathlib.Path(sys.argv[1]); pages = {p.name: p for p in site.glob("*.html")}
class C(HTMLParser):
    def __init__(s): super().__init__(); s.links = []; s.ids = set()
    def handle_starttag(s, tag, attrs):
        a = dict(attrs)
        if a.get("id"): s.ids.add(a["id"])
        s.links += [a[k] for k in ("href", "src", "action") if a.get(k)]
parsed = {}
for n, p in pages.items(): c = C(); c.feed(p.read_text(encoding="utf-8")); parsed[n] = c
bad = []
for n, c in parsed.items():
    for l in c.links:
        if re.match(r"^(https?:|mailto:|tel:|data:|javascript:)", l): continue
        t, _, f = l.partition("#"); t = t or n
        if t not in parsed: bad.append(f"{n}: {l} -> no such file")
        elif f and f not in parsed[t].ids: bad.append(f"{n}: {l} -> no id {f!r}")
print(f"{len(pages)} pages, {len(bad)} broken"); [print(" ", b) for b in bad]
EOF
```

**3. Deploy** (from the repo root). This copies the pages to a temporary
folder without this README, so the README is not published on
plantadvocate.ai, and deploys that:

```bash
D=$(mktemp -d) && cp -R site/. "$D" && rm "$D/README-SITE.md" && npx wrangler pages deploy "$D" --project-name=<project> --branch=<production-branch>
```

Why each part matters:

- `--branch` is required. Inside a git checkout, wrangler takes the branch
  from git (for example `care-advice-honesty`), and a branch that isn't the
  production branch publishes to a preview URL, not to plantadvocate.ai.
- The live deployment has a Pages Function at `/api/waitlist` that the July
  homepage posted early-access emails to. This repo has no `functions/`
  folder, so the new deployment will not have that endpoint. Nothing in these
  pages calls it any more (early access is a `mailto:` link now). If you want
  the addresses already collected, export them from wherever that function
  stored them (KV or D1, in the Cloudflare dashboard) before or after the
  deploy; the data stays, only the endpoint goes. The privacy policy says
  those addresses are used only to tell people about PlantAdvocate.
- `testimonials.html` will no longer exist. With no `404.html`, Pages serves
  the homepage for any unmatched path, so an old link lands on the homepage.

The dashboard works too (Workers & Pages, the project, Create deployment,
upload the files), but drag-and-drop can't carry Functions either, and you
must leave `README-SITE.md` out by hand.

## Verifying the deploy

Run from anywhere. Every line must print `ok`:

```bash
check() { n=$(curl -sL "$1" | grep -c -- "$2"); if [ "$3" = present ]; then [ "$n" -gt 0 ]; else [ "$n" = 0 ]; fi && echo "ok   $1  $2" || echo "FAIL $1  $2 (on $n lines)"; }
check https://plantadvocate.ai/privacy.html 'Effective Date: October 16, 2026' present
check https://plantadvocate.ai/privacy.html 'Apple Weather' present
check https://plantadvocate.ai/privacy.html 'Walk the garden' present
check https://plantadvocate.ai/privacy.html "don't collect your precise location" absent
check https://plantadvocate.ai/privacy.html 'Purchase status' absent
check https://plantadvocate.ai/privacy.html 'JULY 17' absent
check https://plantadvocate.ai/support.html 'Settings &rarr; Account &rarr; Delete account' present
check https://plantadvocate.ai/support.html 'Restore Purchases' absent
check https://plantadvocate.ai/support.html 'billing' absent
check https://plantadvocate.ai/pricing.html '[$]6\|[$]12' absent
check https://plantadvocate.ai/faq.html "isn't currently on the roadmap" absent
check https://plantadvocate.ai/index.html 'EVERY FACT CITED' present
```

Then confirm the two URLs the app opens still resolve:

```bash
curl -s -o /dev/null -w '%{http_code} %{url_effective}\n' -L https://plantadvocate.ai/privacy.html
curl -s -o /dev/null -w '%{http_code} %{url_effective}\n' -L https://plantadvocate.ai/support.html
```

Both should print `200`. Finally open https://plantadvocate.ai/privacy on a
phone and read the top: the date and the "What changed" line should be there.

In App Store Connect, the Privacy Policy URL can be
`https://plantadvocate.ai/privacy.html` (what the app uses) or
`https://plantadvocate.ai/privacy`; they are the same page.

## When the app changes

`privacy.html` is the binding policy; the app's Settings card calls it "the
binding version". If code starts sending data somewhere new (a new weather
service, an AI backend switched on, a census recipient), change `privacy.html`
in the same change, update its effective date and "What changed" line, and
redeploy. The policy already describes photo check-ups and free-text
questions going to Anthropic once switched on, and promises the app asks
first, so that consent has to ship before either backend is turned on.

## Reconciling the generator (desktop machine)

- [ ] Copy `build.py` and its source/templates into this repo (for example
      `site-src/`).
- [ ] Port the October 16 edits in this folder INTO the templates. Do not
      regenerate over these pages and then fix the output.
- [ ] Decide whether `/api/waitlist` stays. If it does, bring its
      `functions/` folder into the repo so deploys carry it, and make sure the
      privacy policy's "This Website" section still matches what it stores.
- [ ] Point the generator's output at `site/` and deploy only from this repo,
      so source, build and deploy are one path.
- [ ] Then, and only then, delete the warning at the top of this file.
