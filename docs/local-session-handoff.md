# Handoff — local terminal session

> **STATUS: ACTIVE (2026-07-25).** Written by the cloud session for the local
> Claude Code session on the MacBook Air. Delete or mark DONE once the three
> pending commands below have been run and their output acted on.

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
| `master` | `db5c520` (PR #11 merged) |
| Working branch | `claude/plant-advocate-screenshots-xxt8ed`, even with master |
| Backend | **261 passed** (`.venv/bin/python -m pytest`) |
| Mobile | `tsc --noEmit` clean, **47 passed** (`npx jest`) |
| Stale branches | `claude/anthropic-vision-backend`, `recover/anthropic-vision` — **deleted** |

The last merge added the Census Species Almanac (search, difficulty filters,
care fingerprint) and changed `GET /species/` to return `SpeciesRead`, so the
internal review trail — `review_status`, `review_note`, `source`, `source_ref`
— no longer reaches clients.

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

Read-only, nothing leaves the server. The machine sleeps
(`min_machines_running = 0` in `fly.toml`), so wake it first:

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

- **Cloud vision backend is unreachable from the app.** `VISION_BACKEND` has no
  hosted option wired up; `/species/identify-photo` degrades to the stub, which
  returns no candidates. On-device identify works; the cloud path was never
  built.
- **No consent copy anywhere in the app.** This is an App Review blocker for a
  build that uploads photos, and it is zero lines of UI today.
- **All catalog tooling is fixture-verified only.** Wikipedia, GBIF, and the
  public-domain book sources are all blocked from the cloud container, and no
  populated species DB is reachable there. The logic has tests; it has never
  been run against real data. Section A above is the first time it will be.
