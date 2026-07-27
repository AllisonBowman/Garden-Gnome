# Handoff — local terminal session

> **STATUS: ACTIVE (2026-07-26).** Written by the cloud session for the local
> Claude Code session on the MacBook Air.

---

## ⛔ Read first: production is not this repository

**Do not run `fly deploy`** until the recovery on PR #15 is finished and pushed.

`garden-gnome-api.fly.dev` serves a `/products/*` router — a 71-item Amazon
affiliate catalog with FTC disclosure copy — **whose source is in no commit on
any branch.** Verified from both sessions:

```
$ git log --all --oneline -S"products"      # nothing
$ curl -s https://garden-gnome-api.fly.dev/products/status   # live, 71 products
```

It also does **not** serve `/ai/status`, which *is* committed (`ai.py`,
registered at `main.py:54`). So production has diverged in both directions: it
is not behind master, it is a different lineage.

**The mechanism.** There is no `.github/workflows/` — no automated deploy — and
`fly deploy` builds the *working directory*, not git (`COPY app ./app`).
Uncommitted files ship; committed-but-absent files don't. One manual deploy from
a dirty tree explains both halves. The Windows box is the likely origin.

**Why the ban matters.** That source exists in exactly two places: whichever
machine's disk still has it, and the running container image. A deploy from this
tree overwrites the second one permanently.

**Everything downstream is affected.** Any reasoning that starts "the code says
X, therefore production does X" is invalid until the drift is measured — that
includes the `ADVISOR_BACKEND` default, the four WeatherKit values, and
Section A below, which runs *container* code, not repo code.

Recovery procedure and progress: **PR #15**.

---

The project is being worked from two places. This file is the seam between
them, so neither has to re-derive what the other already knows.

- **Cloud session** (Claude Code on the web) — repo work only: code, tests,
  PRs. Runs while the laptop is closed. Its container has its own clone, no
  `fly` binary, no credentials, and a network policy that rejects every
  outbound host except npm / PyPI / Anthropic. Verified, not assumed: a
  `CONNECT` to `garden-gnome-api.fly.dev:443` comes back **403** from the
  gateway.
- **Local session** (this one) — anything touching the machine or the Apple /
  Fly accounts: `fly`, the iOS Simulator, the catalog database, TestFlight.

Anything below marked **local-only** is blocked in the cloud for the reason
just given, not because it wasn't tried.

> **The two sessions now have a channel: GitHub issue #14.** Post command
> output there instead of relaying it by hand — see `docs/session-mailbox.md`.
> `gh issue view 14 --repo AllisonBowman/Garden-Gnome --comments`

---

## Verified state

Checked on this exact checkout, not quoted from a PR description:

| | |
|---|---|
| `master` | `3b78258` (PR #13 merged) |
| Working branch | `claude/plant-advocate-screenshots-xxt8ed` |
| Backend | **291 passed** (`.venv/bin/python -m pytest`) |
| Mobile | `tsc --noEmit` clean, **97 passed** (`npx jest`) |
| Open PR | **#15** — the session channel, and where the recovery is running |

These numbers describe **this repository**, which is not what production runs.
See the banner above.

Merged since the last revision of this file:

- **#11** Census Species Almanac; `GET /species/` returns `SpeciesRead`, so the
  internal review trail no longer reaches clients.
- **#12** Consent copy — Settings → Privacy & data, the photo-upload notice, and
  the census opt-in switch, which the privacy policy had promised for months
  while no control existed anywhere in the app. Also stopped requesting
  microphone access the app never uses.
- **#13** An environment can be given a location *after* it was created. This
  was the weather bug: `updateEnvironment` sat unused in the API client, so
  environments predating the address picker had no coordinates and no way to get
  any. Location permission was never the problem.

---

## The catalog database — read this before running anything

**A fresh clone has no populated catalog.** This is the thing most likely to
waste an hour.

`garden-gnome/app/data/species_catalog.json` holds only the **129 curated**
species, all with no `review_status`. The expanded catalog — roughly 1,940 rows,
including the entire `needs_review` backlog the expansion pipeline exists to
work down — lives *only in a database*, and the live one is on the Fly volume at
`/data/garden_gnome.db`.

Both `genus_fill` and `populate_catalog` read `DATABASE_URL`, which defaults to
`sqlite:///garden_gnome.db` relative to the current directory
(`app/db/database.py`). So running them against a fresh Mac clone reports
`0 pending, 0 approved siblings` and writes an empty review file. That is not a
bug and not an empty backlog — it is the wrong database.

Two ways forward, in the order they should be tried.

### A. Get the coverage number without moving any data (local-only)

> ⚠️ **In question since the drift was found.** This runs the expansion scripts
> *inside the container*, which is container code — and container code is not
> repo code. The volume data is presumably still the real catalog, but the
> script reading it may not be the script in this branch, and the package may
> not be in the image at all. Check first:
> `ls /app/app/data/expansion/`. Treat any tally it prints as coming from an
> unknown version until the diff on PR #15 says otherwise.

Read-only, nothing leaves the server. The machine sleeps
(`min_machines_running = 0` in `fly.toml`), so wake it first — though in
practice it has been answering `/` immediately without one:

```bash
curl -s https://garden-gnome-api.fly.dev/ > /dev/null
fly ssh console -a garden-gnome-api
```

Inside the container — `cd` matters, the module needs `/app` as the working
directory, and `DATABASE_URL` is already set to the volume by the image:

```bash
cd /app
python -m app.data.expansion.populate_catalog --dry-run
python -m app.data.expansion.genus_fill --all
exit
```

`--dry-run` writes nothing at all. `genus_fill` writes only a draft-verdict JSON
inside the container — never the catalog. Both print their tallies to stdout.
**That number decides where the catalog work goes next**, which is why it's the
highest-value item on the list.

Note the draft file is ephemeral there: the container's filesystem is not the
volume, so it's gone on restart. Fine for reading the tally, not for applying.

### B. Pull the database down to work on it properly (local-only)

Needed only if the answer to A is "yes, there's real backlog to fill."

```bash
cd ~/Garden-Gnome/garden-gnome
fly ssh sftp get /data/garden_gnome.db garden_gnome.db -a garden-gnome-api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.data.expansion.genus_fill --all
```

If the two-argument `sftp get` is rejected, drop the destination — it writes to
the current directory, which is where it needs to land. `garden_gnome.db` is
gitignored (`garden-gnome/.gitignore:11`), so it won't dirty the tree.

That leaves `app/data/expansion/output/genus_fill_review.json`.

> **Do not run `apply_review` on it unhesitatingly.** Those values are
> *inferred from genus siblings*, not verified against a source. `apply_review`
> is the one step in the pipeline that mutates the catalog. Read the file first.
>
> The standing rule the pipeline enforces, worth restating because it is easy to
> undo by hand: **toxicity may only ever move non-toxic → toxic.** Clearing a
> pet-safety warning because a source was silent about it is not a correction,
> it's a guess with a bad failure mode. `genus_fill` only proposes a toxicity
> value when the whole genus agrees unanimously.

---

## The other two pending items

### Confirm the WeatherKit key actually deployed (local-only)

```bash
fly secrets list -a garden-gnome-api
```

Want `WEATHERKIT_PRIVATE_KEY` showing a **digest** and a recent timestamp.
Staged-but-not-deployed is the failure mode here — a `flyctl` panic during
`fly secrets set` left it staged once already, and `fly deploy` is what applies
it.

The `.p8` private key goes into Fly secrets read directly from the file. It
should never be pasted into a chat, this repo, or a terminal argument.

### See the Almanac on the simulator (local-only)

```bash
cd ~/Garden-Gnome/mobile
npm run sim
```

`scripts/sim-build.sh` syncs the checkout to
`origin/claude/plant-advocate-screenshots-xxt8ed` — currently even with master —
so it picks up the Almanac with no extra step. No native dependencies changed
since the last build, so it skips the slow prebuild and hot-reloads through
Metro. Census tab → the Almanac card.

---

## Known-open, not yet scheduled

- **Deploys have no guard rail.** No CI, no deploy workflow, and `fly deploy`
  ships whatever is in the working directory. This is the root cause of the
  drift above, and it is still unfixed — the next manual deploy from a dirty
  tree recreates the same problem. Worth a GitHub Actions workflow deploying
  from `master` on merge, which needs a `FLY_API_TOKEN` repo secret and is
  therefore Allison's call.
- **`site/privacy.html` still contradicts the app.** It denies the photo upload
  that ships today and omits location entirely, though coordinates reach Apple
  WeatherKit. Exact replacement paragraphs are in
  `docs/privacy-policy-corrections.md`; publishing them is the owner's call.
- **Cloud vision backend is unreachable from the app.** `VISION_BACKEND` has no
  hosted option wired up in this tree; `/species/identify-photo` degrades to the
  stub. On-device identify works. (What *production* does here is now an open
  question, not a known.)
- **All catalog tooling is fixture-verified only.** Wikipedia, GBIF, and the
  public-domain book sources are blocked from the cloud container, and no
  populated species DB is reachable there. The logic has tests; it has never run
  against real data.
- **`app.json` changed in #12 and again in the Apple team pin**, so the next
  `npm run sim` does a full prebuild (minutes, not the fast path).
