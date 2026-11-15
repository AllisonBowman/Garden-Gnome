# How deploys work

> **One-time setup is still required** — see "Turning it on" below. Until the
> `FLY_API_TOKEN` secret exists on the `production` environment, the deploy
> job fails at its Deploy step with `no access token available`, nothing is
> deployed, and deploys stay manual.

## The rule

**Master is what runs in production.** Merging to master deploys. Nobody
deploys from a laptop.

## Why it works this way

For four days in July 2026, production ran a build that existed on no branch.
`fly deploy` builds the **working directory**, not git — so a single manual
deploy from a dirty checkout shipped an uncommitted `/products/*` router into
production while omitting seven committed modules, including the entire weather
service. The weather feature appeared broken for days; it had simply never been
deployed.

Nobody noticed because nothing compared the two. The full account is in
`docs/pre-deploy-checklist.md` and PR #15; the recovered source is on
`rescue/deployed-production`.

A laptop's uncommitted state cannot reach production through a CI runner. That
is the entire point.

## What runs when

`.github/workflows/ci.yml`:

| trigger | backend tests | mobile tests | deploy |
|---|---|---|---|
| pull request | ✓ | ✓ | — |
| push to master | ✓ | ✓ | ✓ |

The deploy job `needs: [backend, mobile]`, so a red test suite blocks the
release. Mobile is included deliberately: the app is the API's only client, and
shipping a server whose client no longer typechecks against it is a broken
release even when the server's own tests pass.

Two concurrency groups, at two levels:

- **The workflow** is grouped per ref (`ci-${{ github.ref }}`). A pull
  request's runs never share a queue with master's, so they can't wait behind
  a deploy or push one out of the queue. A new push to a pull request cancels
  that pull request's stale run. A running master run is never cancelled.
- **The deploy job** has its own group, `deploy-production`, with
  `cancel-in-progress: false` — two deploys never race, and an in-flight one
  is never interrupted. Cancelling mid-deploy is worse than queueing, because
  migrations run at container boot.

The deploy step is pinned twice: the `superfly/flyctl-actions/setup-flyctl`
action by commit SHA (its 1.6 release) and flyctl itself at `0.4.111`. What
deploys is what was last checked, not whatever landed in either since. Bump
them together, on purpose. It runs `flyctl deploy --remote-only` from
`garden-gnome/`, because the Dockerfile's `COPY app ./app` is relative to that
directory.

After deploying, a smoke check polls `GET /` for up to 5 minutes (300 s), one
try every 10 s, each try allowed at most 10 s. The machine has
`min_machines_running = 0`, so this doubles as a cold start and proves the
container actually boots — a failed migration shows up here as never
answering ("never returned 200 in 5 minutes"). Five minutes, not two: the
first boot of a release runs the migrations and the claim sync before uvicorn
binds, and Fly throttles a shared CPU once its burst balance is spent.

A 200 is not enough to pass. The root JSON carries `catalog.synced`, and the
step fails unless it is `true`. It is `false` when the boot logged `claim
sync skipped` and the API is serving the old catalog; the step then prints
"The API is up but is not serving the catalog this build ships" and turns the
run red on purpose. That isn't a rollback case: the API is up and serving.
Read `fly logs -a garden-gnome-api` for `claim sync skipped` and the traceback
above it. The step also prints `/ai/status`, so the run log records which AI
backends production reports.

The VM is `shared-cpu-1x` with 512 MB (`garden-gnome/fly.toml`). A 256 MB
guest could not hold the process when ten phones loaded the catalog at once;
with the species-list cache it reaches about 153 MB, and the rest is
headroom.

## Turning it on

One secret, created scoped to this app:

```bash
fly tokens create deploy -x 999999h -a garden-gnome-api
```

Store the output as a secret named **`FLY_API_TOKEN`** on the repository's
**`production` environment**, not as a repository-wide secret. The token is
printed once; paste it straight into the prompt:

```bash
gh secret set FLY_API_TOKEN --env production --repo AllisonBowman/Garden-Gnome
```

```bash
gh secret list --env production --repo AllisonBowman/Garden-Gnome
```

(Or in the browser: Settings → Environments → production → Add environment
secret.) The deploy job declares `environment: production`, so it reads the
secret from there, and no other job can see it. The comment in `ci.yml` still
says "repo secret"; a repository secret would also work, but the environment
is where it belongs and where the 1.1.3 handoff puts it.

Use a **deploy token**, not a personal auth token. A deploy token can deploy
this one app and nothing else; a personal token can do anything your Fly account
can, and it would be sitting in CI.

Because of that `environment: production`, GitHub also shows deploys in the
Environments tab. If you want a manual approval gate before each production
deploy, add a required reviewer to that environment in repo settings —
nothing in the workflow changes.

## What this does not cover

- **Migrations still run at container boot** (`CMD` in the Dockerfile:
  `python -m app.data.seed`, which migrates and then runs the claim sync,
  before uvicorn starts), not as a separate step. Additive migrations are
  safe; a destructive one would apply before anything could check it. Read
  `alembic/versions/` before merging one. 0017 renames a table, and SQLite
  can't roll that back if it fails partway.
- **Rolling back restores the image, not the database.** Snapshot the volume
  before any deploy carrying a migration you haven't run before. Find the
  `gnome_data` volume with `fly volumes list -a garden-gnome-api`, then
  `fly volumes snapshots create VOLUME_ID`, and wait for it in
  `fly volumes snapshots list VOLUME_ID`. Fly's automatic daily snapshot is
  not a substitute: it can be a day old. A copied file also works if it is
  taken with SQLite's own backup (the one-liner in
  `docs/2026-10-16-app-store-finish-line-handoff.md`, step 2), not by copying
  the live file.
- **Every push to master deploys**, including docs-only changes. That's
  deliberate — it keeps "master is what runs" literally true rather than
  approximately true. Add a path filter if the build minutes ever matter more
  than the invariant.
- **Secrets are not managed here.** `fly secrets set` remains manual, and
  changing one requires a deploy to take effect.

## Deploying by hand

Should be rare. If CI is down and it's urgent, `docs/pre-deploy-checklist.md`
has the full procedure — including the two gates that matter (back up the
volume; verify `git status --porcelain` *and* `git log origin/master..HEAD` are
both empty) and the two normal conditions that look like a failed deploy and
aren't.

## Rolling back 1.2.0 (migrations 0023 to 0031)

1.2.0 adds nine migrations, `0023_property` to `0031_site_override`. The
image before it (master `26525f9`) only knows up to
`0022_backfill_acquired_on`. Everything below was tried on 2026-11-15 on a
copy of the schema with invented rows (Python 3.12.13, the old and new trees
exported with `git archive`), not on production. Commands marked
**(not run here)** were never run against Fly; check what they print.

### Do not just deploy the old image

The old image cannot start against a 0031 database. Its boot
(`python -m app.data.seed`) stops with:

```
alembic.util.exc.CommandError: Can't locate revision identified by '0031_site_override'
```

and exits 1, so uvicorn never starts and the smoke check never gets a 200.
The old image also cannot repair this itself: it does not contain the
0023 to 0031 files, so it cannot downgrade. If this has already happened,
deploy 1.2.0 again first, then follow path A.

### Two ways back, and what each loses

| | path A: downgrade, then old image | path B: snapshot `vs_wNoyJ8J0oQ0f7wXmkw9` |
|---|---|---|
| Plants, care logs, accounts, sign-ins written while 1.2.0 ran | kept | **lost** (everything after the snapshot) |
| Properties (pin, lot contents, goals) | **lost** | lost (none existed before) |
| Zone details: boundary, vegetation, leaf habit, sun source, whole lot, which property | **lost** | lost |
| Zones themselves | kept, as ordinary growing areas, plants still in them | lost, with their plants |
| Owner corrections (`site_override`), seasonal answers (`season_event_state`) | **lost** | lost |
| Site readings, forecast, freeze, tile caches and provider counts | lost (refetchable) | lost |

Prefer path A. Use B only if the downgrade fails or the data itself is
damaged.

After path A, a zone such as "Whole lot" or "Veg bed" shows up in the old app
as one more growing area. Owners will see these; that is expected.

### Path A: downgrade with 1.2.0 still deployed

1. Snapshot the volume first (same as before any deploy):
   `fly volumes list -a garden-gnome-api`, then
   `fly volumes snapshots create VOLUME_ID`, and wait for it in
   `fly volumes snapshots list VOLUME_ID`.
2. Write down the release to go back to. `fly releases -a garden-gnome-api`
   lists them; you want the image of the release before 1.2.0
   **(not run here; check the output shows an image reference)**.
3. Check the database is at 0031:

   ```bash
   fly ssh console -a garden-gnome-api -C "python -c \"import sqlite3;print(sqlite3.connect('/data/garden_gnome.db').execute('select * from alembic_version').fetchone())\""
   ```

   Expect `('0031_site_override',)` **(not run here)**.
4. Run the downgrade inside the running 1.2.0 machine. It is the only image
   that has the downgrade code:

   ```bash
   fly ssh console -a garden-gnome-api -C "sh -c 'cd /app && DATABASE_URL=sqlite:////data/garden_gnome.db python -m alembic downgrade 0022_backfill_acquired_on'"
   ```

   **(not run here.)** Locally it printed nine `Running downgrade` lines,
   the last one `0023_property -> 0022_backfill_acquired_on`, and exited 0.
   Every table and row that existed at 0022 came back identical. The only
   differences were rows added while 1.2.0 ran and line breaks in the
   rebuilt `growingarea` schema.
5. Go straight to step 6. Between step 4 and step 6:
   - the running 1.2.0 process answers `GET /` with 200 but
     `GET /growing-areas` with 500, because its model still expects the
     zone columns;
   - **do not restart the machine.** A 1.2.0 boot runs the migrations again
     and puts the database back at 0031, with empty new tables. If that
     happens, repeat step 4.
6. Deploy the previous image:
   `fly deploy --image PREVIOUS_IMAGE -a garden-gnome-api`, from
   `garden-gnome/` **(not run here)**.
7. Check it came up: `fly logs -a garden-gnome-api` shows
   `claim sync: ...` and no traceback, and step 3's command prints
   `('0022_backfill_acquired_on',)`. Locally the old tree then booted
   (seed exit 0), `GET /` returned 200 with `"synced": true`, it listed
   growing areas and plants, and it saved a new care log.
8. Stop master from deploying 1.2.0 again. Every push to master deploys, and
   the next push would run 0023 to 0031 again. Revert the 1.2.0 merge on
   master before anything else lands there.

### Path B: restore the snapshot

`vs_wNoyJ8J0oQ0f7wXmkw9` was taken on 2026-11-15 just before the deploy.
Check that it is listed in `fly volumes snapshots list VOLUME_ID`. Fly
restores a snapshot into a new volume, and the machine then has to use that
volume. The commands for that are not in this repository and were **not run
here**. Look them up rather than guessing. Then deploy the previous image
(path A, step 6), never 1.2.0: 1.2.0 would migrate the restored file to 0031
again on boot. Do step 8 too.

### SQLite journal mode: nothing to do

1.2.0 switches the file to write-ahead logging (WAL), and the setting stays
in the file after the downgrade. The old code does not set a journal mode,
so it keeps using WAL. Locally that worked even with a `-wal` file still
holding unsaved writes, both from 1.2.0 and from after the downgrade. The
old boot read all of them, and every one showed up in `carelog`.

- No checkpoint is needed before rolling back. If you want the main file
  complete on its own anyway:
  `python -c "import sqlite3;c=sqlite3.connect('/data/garden_gnome.db');print(c.execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchone())"`
  (inside `fly ssh console`). Locally it printed `(0, 0, 0)`, and after it
  the `.db` file alone held every row.
- Do not try to switch back to the old journal mode while the app is
  running. Locally, `PRAGMA journal_mode=DELETE` failed with
  `database is locked` while another connection was open. It is not needed.
- Never copy `garden_gnome.db` by itself while the app runs. Unsaved writes
  live in `garden_gnome.db-wal`. A plain copy of the `.db` file left out a
  care log that a SQLite backup kept. Use the SQLite backup one-liner
  mentioned above, or a volume snapshot.
