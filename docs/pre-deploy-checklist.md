# Pre-deploy checklist — the first deploy after the drift

> **STATUS: RUN AND VERIFIED (2026-07-27, v14).** Kept as the runbook for future
> deploys. Outcome recorded at the bottom — including two things that looked
> like failures and weren't, which is the part worth reading before the next
> one.
>
> Every fact here was verified against the recovered production image
> (`rescue/deployed-production`, `8f02b7b`) and against master. Nothing is
> inferred from the feature list.

This is not a routine deploy. Production has been running an unversioned build
since **Jul 23** — see the banner in `docs/local-session-handoff.md`. Its source
is now archived under `recovered/` on the rescue branch, so the deploy can no
longer destroy anything irrecoverably. What it *can* still do is change the
live database and remove a running feature, and both deserve a deliberate look
before anyone types the command.

---

## What this deploy changes

**Adds** (present in master, absent from the running image):

| | why it matters |
|---|---|
| `services/weather.py` | **this is the weather fix.** The four WeatherKit secrets have been correctly deployed the whole time for a service that does not exist in the image |
| `routers/ai.py` | `/ai/status` — currently 404 in production |
| `services/grounding.py`, `persona.py`, `toxicity.py`, `name_match.py` | groundedness guard, gnome voice, nuanced toxicity |
| `data/expansion/`: `populate_catalog.py`, `genus_fill.py`, `wiki_enrich.py`, `research_review.py`, `book_*.py` | the newer catalog pipeline. Absent from the image, which is why Section A of the handoff doc cannot run in-container as written |

**Removes** (in the running image, in no commit until the rescue):

| | |
|---|---|
| `routers/products.py`, `services/products.py`, `services/affiliate.py`, `services/plant_profile.py`, `data/product_catalog.json` | the 71-item Amazon affiliate feature |

Verified: **nothing we ship calls those routes.** `grep -rn "products\|affiliate\|amazon" mobile/src/` and `grep -rln "/products" site/` are both empty. Removing them breaks no client. The source survives on `rescue/deployed-production`.

---

## The one irreversible part

Rolling back a Fly release restores the **image**. It does not restore the
**database**.

The good news, and it was the sharpest risk: the migration chains are **not
forked**.

```
deployed image:  0001 0002 0003 0004
master:          0001 0002 0003 0004 0005
```

A strict superset. The only new revision is `0005_environment_climate`, and its
`upgrade()` is three `add_column` calls on `environment` (`shelter`,
`temp_exposure`, `sun_exposure`) — additive, no drops. Migrations run at boot
via `python -m app.data.seed` (see the `CMD` in the Dockerfile).

Had production been sitting on a revision master didn't contain, `alembic
upgrade head` would fail on boot and take the API down. It isn't. But back the
volume up anyway — it costs one command and it is the only part of this that
can't be undone.

---

## Pre-flight

**1. Back up the live database.**

```bash
fly ssh sftp get /data/garden_gnome.db backup-$(date +%Y%m%d-%H%M).db -a garden-gnome-api
ls -la backup-*.db
```

Confirm it's a real size, not zero bytes. Keep it off the repo — it holds real
user data and `garden_gnome.db` is gitignored for that reason.

**2. Deploy from a clean checkout of master.**

This is the whole cause of the drift: `fly deploy` builds the **working
directory**, not git. Uncommitted files ship; committed-but-absent files don't.

```bash
cd ~/Garden-Gnome
git checkout master && git pull
git status --porcelain          # MUST be empty
```

If that prints anything, stop and resolve it. A dirty tree here is how the
`products` router got into production with no commit behind it.

> The Mac also has an unpushed local commit (the `1.0.1` version bump). Decide
> whether it belongs in this deploy and push it, or stash it — do not let it
> ride along unexamined.

**3. Confirm what the secrets actually say.**

```bash
fly secrets list -a garden-gnome-api
```

All twelve should read `Deployed`. Note that `ADVISOR_BACKEND` and
`VISION_BACKEND` share a digest — they hold the same value, which constrains it
to `stub` or `ollama` and rules out `anthropic`. There is no `ANTHROPIC_API_KEY`
in the list at all.

---

## Deploy

```bash
fly deploy -a garden-gnome-api
```

Watch it boot. Migrations and seed run before uvicorn binds, so a migration
failure shows up as a boot loop, not a 500.

---

## Post-deploy verification

**1. The endpoint that didn't exist before:**

```bash
curl -s https://garden-gnome-api.fly.dev/ai/status
```

This is the first time the *value* of `ADVISOR_BACKEND` becomes visible rather
than inferred from a digest.

> ⚠️ **Expect a possible surprise here.** If the value is `ollama`, master has
> no such backend — `_BACKENDS.get(backend, _advise_stub)` (`advisor.py:455`)
> and `_IDENTIFY_BACKENDS.get(backend, _identify_stub)` (`vision.py:370`) both
> **fall back to the stub silently**. No crash, no error, no log line at the
> call site. The advice would keep working and keep being rule-based.
>
> If `/ai/status` reports `ollama`, that is the moment to decide about Claude:
> `fly secrets set ADVISOR_BACKEND=anthropic ANTHROPIC_API_KEY=sk-ant-... -a garden-gnome-api`

**2. Weather, the actual point of the deploy:**

Open an environment that has coordinates (set one in the app first if needed —
PR #13 added the picker to the weather card). The forecast should render, with
the Apple Weather credit beneath it.

**3. Nothing else regressed:**

```bash
curl -s https://garden-gnome-api.fly.dev/ | python3 -m json.tool
curl -s https://garden-gnome-api.fly.dev/products/status    # expect 404 now
```

That 404 is the affiliate feature leaving production. Expected, not a fault.

**4. The catalog question, finally answerable:**

```bash
fly ssh console -a garden-gnome-api
cd /app && python -m app.data.expansion.populate_catalog --dry-run
exit
```

The recovered `expansion_report.json` showed **1,714 flagged for review against
123 imported** — but that is a report file from a past run, not a query against
the live volume. After this deploy the modules exist in the image and the number
can be read for real.

---

## Rollback

```bash
fly releases -a garden-gnome-api
fly deploy --image <previous-digest> -a garden-gnome-api
```

Restores the code. **Does not restore the schema** — `0005`'s three columns stay
added. They're additive and the old code ignores unknown columns, so the old
build runs fine against the migrated DB. That's why the superset chain mattered.

If something worse happens, the volume backup from step 1 is the real
insurance.

---

## Not blocking, but decide eventually

The affiliate feature is archived, not integrated. Bringing it back is a real
job, not a cherry-pick: `models.py`, `schemas.py` and `catalog.py` all differ
between the two trees, so `products.py` may not even import against current
master. It also ships live FTC disclosure copy — *"As an Amazon Associate,
PlantAdvocate earns from qualifying purchases"* — that has never been reviewed,
and `affiliate_configured` is `false`, so it has never earned anything either.

Its own branch, its own PR, its own tests. Not this deploy.

---

## Outcome — v14, 2026-07-27

Deployed as **v14**, image `deployment-01KYJ8V85Y8RXAQ35515TVJG4G`. Both gates
passed. Migration `0005` applied; species count unchanged at **1,940** across
it. Volume backed up first (2,789,376 bytes, integrity `ok`, `alembic_version`
`0004` — confirming the superset analysis from the outside).

### Two things that look like a broken deploy and aren't

Both will recur on every future deploy. Read these before rolling anything back.

**1. `WARNING The app is not listening on the expected address`**, listing only
`/.fly/hallpass` on port 22. This is the exact signature described above for a
migration boot loop. **It is not one** — it's the window before uvicorn binds.
`/` returned 200 immediately after.

**2. `curl` returning `http 000` a few minutes later.** Also not a crash:
`auto_stop_machines` idles the machine down (`min_machines_running = 0` in
`fly.toml`). The next request cold-starts it.

Anyone reading either as a failure will roll back a healthy deploy. Check
`fly status` before concluding anything — `stopped` means asleep, not broken.

### Results

| check | outcome |
|---|---|
| `/ai/status` | `{"advisor_backend":"stub","vision":{"backend":"stub","ready":false}}` |
| `/products/status` | **404** — affiliate feature removed, source on the rescue branch |
| `/environments/{id}/weather` | **401** — route exists and is auth-gated; it did not exist before v14 |
| `populate_catalog --dry-run` | refused correctly until `genus_fill` ran; then real numbers (below) |

### The AI answer, stated precisely

`ADVISOR_BACKEND` is **set, and set to `stub`**. Not unset-and-defaulting, which
is what was assumed twice. The shared digest with `VISION_BACKEND` is explained:
both hold the literal string `stub`.

The predicted `ollama` silent-fallback trap did not fire. But the distinction
matters for what happens next: **someone deliberately configured stub.** Turning
the AI on is a decision to reverse, not an oversight to fix — it needs
`ADVISOR_BACKEND=anthropic` *and* an `ANTHROPIC_API_KEY`, which is still not in
the secrets list.

### The catalog number, at last

Against the live volume, not a recovered artifact:

```
needs_review: 1688 pending, 252 approved siblings across 198 genera
verdicts: {'uncertain': 1239, 'corrected': 449}
```

The free offline genus pass proposes values for **449** of 1,688 — about 27% —
and leaves **1,239** needing `wiki_enrich`, paid research, or manual work.
Nothing was written; `apply_review` remains a separate deliberate step.

The stale in-container artifact had said 1,714 flagged. Close enough to show it
was broadly right, far enough off that quoting it as the number would have been
wrong.

### Still open

**WeatherKit has never been exercised.** A 401 proves the route and service are
deployed; it does not prove the credentials authenticate against Apple, because
that only happens on a real authenticated request. Those four secrets sat
configured for a service that didn't exist — the first call from the app is the
first test they have ever had.

If the forecast fails to render, *that* is finally the WeatherKit-credentials
problem, and only then.
