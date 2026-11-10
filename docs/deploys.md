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
