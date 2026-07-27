# How deploys work

> **One-time setup is still required** — see "Turning it on" below. Until the
> `FLY_API_TOKEN` secret exists, the deploy job fails and deploys stay manual.

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

`concurrency: deploy-production` with `cancel-in-progress: false` — two deploys
never race, and an in-flight one is never interrupted. Cancelling mid-deploy is
worse than queueing, because migrations run at container boot.

After deploying, a smoke check polls `/` for up to two minutes. The machine has
`min_machines_running = 0`, so this doubles as a cold start and proves the
container actually boots — a failed migration shows up here as never answering.

## Turning it on

One secret, created scoped to this app:

```bash
fly tokens create deploy -x 999999h -a garden-gnome-api
```

Add the output as a repository secret named **`FLY_API_TOKEN`**
(Settings → Secrets and variables → Actions → New repository secret).

Use a **deploy token**, not a personal auth token. A deploy token can deploy
this one app and nothing else; a personal token can do anything your Fly account
can, and it would be sitting in CI.

The workflow also references an `environment: production`, so GitHub will show
deploys in the Environments tab. If you want a manual approval gate before each
production deploy, add a required reviewer to that environment in repo settings
— nothing in the workflow changes.

## What this does not cover

- **Migrations still run at container boot** (`CMD` in the Dockerfile), not as a
  separate step. Additive migrations are safe; a destructive one would apply
  before anything could check it. Read `alembic/versions/` before merging one.
- **Rolling back restores the image, not the database.** Back up the volume
  before any deploy carrying a migration you haven't run before:
  `fly ssh sftp get /data/garden_gnome.db backup-$(date +%Y%m%d).db -a garden-gnome-api`
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
