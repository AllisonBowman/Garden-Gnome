# Deploying PR #20 to Fly: what only you can do

Written 2026-10-01 about master at `35dbf1e` (the merge of PR #20) and PR #21,
which has to land on top of it before anything is deployed. Every step needs
your Fly login or your GitHub admin rights, so none of it can be done from the
dev machine. The commands run as written in PowerShell on the Windows box or
zsh on the Mac: no `&&`, nothing bash-only, and in steps 1 to 5 it does not
matter which folder you are in. The one command that needs a different
spelling per machine is under Verify.

## Why this matters

PR #20 (growing areas, the fit engine, the size-backfill catalog work) merged
into master on 2026-10-01 as `35dbf1e`. CI's test jobs passed on run
36940954939, then "Deploy to Fly" failed at its Deploy step:
`Error: no access token available. Please login with 'flyctl auth login'`.
The workflow reads `secrets.FLY_API_TOKEN`, which exists nowhere, neither on
the repo nor on the `production` environment (both lists were empty when
checked; the environment has no protection rules). The previous master run
(PR #19, 2026-08-08) failed the same way, so CI has never deployed production.

Production is up anyway, on older code: https://garden-gnome-api.fly.dev/
answers 200 with 29 paths in its `openapi.json`, including `/environments` and
no `/growing-areas` (re-checked while writing this). Master has 36. The seven
new URLs are the five `/growing-areas` ones plus deprecated
`/environments/{id}/candidates` and `/misfits` aliases; every URL production
serves today still answers. No new Fly secrets are needed (only `JWT_SECRET`
and `FERNET_KEY` are required, and production is running).

URLs are not the whole story for the TestFlight 1.1.2 app. PR #20 renamed the
plant fields from `environment_id` to `growing_area_id` (and the census keys
with them), and 1.1.2 still sends and reads the old names. Deployed as
`35dbf1e` stands, that breaks it five ways: moving a plant gets a 422, a plant
added from Add Plant or Capture Garden lands in your oldest area, each area's
own care list is empty, the weather nudge stops, and the Census tab crashes.
PR #21 ("Make master deployable over TestFlight 1.1.2, Species tab excepted")
fixes all five on the server, by accepting the old field names, returning
`environment_id` beside `growing_area_id`, and restoring the old census keys;
15 replay tests of 1.1.2's exact requests and responses pass against it. That
is why step 5 merges #21 instead of re-running the failed CI run, which would
deploy `35dbf1e` without it.

The Species tab is the exception, and no server alias can fix it without
inventing catalog data. 1.1.2's Species list, species page and plant care guide
call `light_need.replace(...)` unguarded, and the claim sync mints species with
`light_need` empty on purpose (ADR 0005): 515 of 644 on a fresh seed, and on
production however many the first boot's `species created` line says. After
the deploy the Species tab throws once one of those rows scrolls into view or
matches a search, and their own pages throw. A plant's page throws only if its
species is a minted one; existing rows keep their `light_need`, so only a plant
newly added from the catalog is at risk. Care tracking, areas, add and move,
census and reminders keep working. All of this is from 1.1.2's source (commit
a5d0d07) and the replay tests, not from a phone.

Whether to deploy before a new TestFlight build ships is your call. The new
build needs this backend (it calls `/growing-areas`), so the real choice is how
long 1.1.2 sits on it with the Species tab broken. The secret is the switch:
without steps 3 and 4, merging #21 deploys nothing, so you can merge it, cut the
build, and do steps 1 to 4 and the re-run (end of step 5) when the build is
ready to go out. Separately, #21 fixes a bug in the new client: its Census tab
read `total_growingAreas` and `growingAreas_by_type`, keys the server has never
sent, and some text said "GrowingAreas" where it should read "Growing areas".
Cut the next build from master after #21 has merged, not before, and check
first that `CensusScreen.tsx` on master reads `total_growing_areas` and
`growing_areas_by_type`.

## Step 1: Log in to Fly

```
fly auth login
fly auth whoami
```

`login` opens a browser; sign in as the account that owns `garden-gnome-api`.
Look for `whoami` printing your email rather than an error. flyctl 0.4.76 is
installed on the Mac (not logged in as of earlier today). I could not look at
the Windows box: if `fly` is not found there, do steps 1 to 3 on the Mac.
Steps 4 and 5 need only the GitHub CLI or a browser.

## Step 2: Snapshot the volume

Do this before anything that changes production. The first boot of the new
image runs migrations 0010 through 0020 against the live database (PR #19
carried them only through 0009, so unless something was deployed by hand
since, that is where production sits), then the claim sync rewrites every
species row. 0017 renames the `environment` table to `growingarea` and the
`environment_id` columns on `plant` and `stewardshiprecord` to
`growing_area_id`, as batch table rebuilds that move no data. I ran the real
boot command on a scratch database built at 0009 with a few rows (two areas,
four plants): 3 to 10 s on a laptop at about 115 MB peak (the VM has 256 MB and
is slower), every row and link survived, `foreign_key_check` empty. Those rows
were synthetic, so what nobody has seen is 0017 on production's real data, and
Alembic's DDL on SQLite is not transactional: a failure partway through can
leave a half-migrated file. That is what the snapshot is for.

```
fly volumes list -a garden-gnome-api
fly volumes snapshots create <volume-id>
fly volumes snapshots list <volume-id>
```

Replace `<volume-id>` with the ID of the volume named `gnome_data` (mounted at
`/data`). Look for a new snapshot from today in the last command's output; if
it still shows as being created, wait and list again. Fly also takes automatic
daily snapshots. That is a fallback, not a substitute: the newest one can be a
day old, and only a snapshot taken now has the database as it is before the
migrations run.

## Step 3: Create a deploy token

```
fly tokens create deploy -x 999999h -a garden-gnome-api
```

This is the command the workflow's own comment prescribes. A deploy token can
deploy this app and nothing else; do not use a personal auth token. The token
is printed once. Copy it straight into step 4, and never paste it into chat or
a file.

## Step 4: Store it as the GitHub secret the workflow reads

```
gh secret set FLY_API_TOKEN --env production --repo AllisonBowman/Garden-Gnome
gh secret list --env production --repo AllisonBowman/Garden-Gnome
```

The first command prompts for the value; paste the token. Look for
`FLY_API_TOKEN` in the second command's output (it was empty before). Without
the CLI, use the web UI: the repo's Settings > Environments > production > Add
secret, name `FLY_API_TOKEN`. docs/deploys.md describes a repository-level
secret instead; the job reads either, and the environment-level one is the
narrower choice. Once the secret exists, every push to master deploys on its
own, docs-only ones included.

## Step 5: Merge PR #21, which is what deploys

Do not re-run the failed CI run, 36940954939. A re-run checks out the commit it
started from, `35dbf1e`, which has no compatibility shim, so it would break
1.1.2 in the five ways above. Merging PR #21 instead pushes master and starts a
fresh CI run whose deploy job has the secret. First open PR #21 and check that
its Backend tests and Mobile typecheck and tests are green.

```
gh pr merge 21 --repo AllisonBowman/Garden-Gnome --merge
gh run list --repo AllisonBowman/Garden-Gnome --branch master --limit 1
gh run watch <run-id> --repo AllisonBowman/Garden-Gnome
```

The first command merges with a real merge commit, as every earlier PR here has
been; if gh refuses, stop and bring me its message. The second lists the newest
master run: if it still shows 36940954939, wait a few seconds and list again.
Put the new run's ID (the number in the ID column) in place of `<run-id>`. That
run repeats the two test jobs, then the deploy job runs
`flyctl deploy --remote-only` from `garden-gnome/`, then a smoke check requests
https://garden-gnome-api.fly.dev/ up to 12 times, ten seconds apart, waiting for
HTTP 200. The `production` environment has no approval gate, so nothing waits
for you. Look for all three jobs green and `up after N attempt(s)` in the smoke
check's output; N above 1 is normal, since the machine is cold-starting and
migrating.

If the deploy job fails for lack of the secret, or you held steps 3 and 4 on
purpose, fix that, then re-run the failed job of the newest master run (never
the old one):

```
gh run rerun <run-id> --failed --repo AllisonBowman/Garden-Gnome
```

## Step 6: Or deploy by hand

Do steps 1 and 2, skip 3 and 4, and merge PR #21 with the first command of
step 5 (the CI deploy job will go red for lack of a token; that is expected
here). Clone master only after that merge: an earlier clone has no compatibility
shim. Use one route or the other, since CI's one-deploy-at-a-time lock does not
cover your own machine and both run migrations at boot.

`flyctl deploy` ships the working directory, not git, which is how production
once ran an uncommitted router for four days (the header of
`.github/workflows/ci.yml` tells it). So deploy only from a checkout of master
that passes both gates from docs/pre-deploy-checklist.md. Each of these must
print nothing:

```
git status --porcelain
git log origin/master..HEAD
```

The Mac's main checkout does not pass them as I write this: it is on the
`care-advice-honesty` branch (PR #21's branch) with unrelated uncommitted files
in the tree (mobile icons and `app.json`, tool folders). Do not switch it or
stash those just to pass; a fresh clone passes by construction. I have not
looked at the Windows checkout; the same gates apply there. Run these from a
folder outside the existing checkout:

```
git clone https://github.com/AllisonBowman/Garden-Gnome.git Garden-Gnome-deploy
cd Garden-Gnome-deploy/garden-gnome
git log --oneline -1
flyctl deploy --remote-only
```

Look for the merge of PR #21, or a later master commit, from `git log`. There
is no smoke check on this route, so go straight to Verify; if the first request
fails, wait ten seconds and retry, since the machine is cold-starting. This
deploys once: CI stays red on every merge to master until steps 3 and 4 are
done.

## Verify

```
curl -s https://garden-gnome-api.fly.dev/openapi.json | python -c "import json,sys; p=json.load(sys.stdin)['paths']; print(len(p), any(k.startswith('/growing-areas') for k in p))"
```

Look for `36 True`; today it prints `29 False`. On the Mac the interpreter is
`python3` (there is no `python`). On Windows PowerShell, write `curl.exe`
instead of `curl` (plain `curl` there is usually an alias for
Invoke-WebRequest, which rejects `-s`), and use `python` or `py`.

A 200 from the new image already shows the migrations ran, because uvicorn only
starts if the seed step succeeds. It cannot show the claim sync worked: that
step is fenced, so if it fails the API still boots with stale species data.
That is what the logs are for.

```
fly logs -a garden-gnome-api
```

Run it soon after the deploy. It streams until you press Ctrl+C; add
`--no-tail` to print what is buffered and exit. Look for, in order:

- A first upgrade line like
  `INFO  [alembic.runtime.migration] Running upgrade 0009_aloe_vera -> 0010_claims, ...`,
  one line per migration after it, and a last one reading
  `Running upgrade 0019_fit_fields -> 0020_climbs, ...`. The first line shows
  where production's database actually was. If it starts anywhere else,
  something was deployed by hand in between; that is not a problem by itself,
  but tell me.
- `claim sync: written`, then an indented block of counts beginning
  `claims stored           6989` and `claims already present  0`. The species
  counts below those depend on production's species table and I cannot predict
  them.
- No traceback, and no line reading `claim sync skipped`.

On every later cold start you will see `Species catalog already up to date.`
and `claim sync: tranche unchanged, nothing to do`. Both are normal.

## If it fails

If the Deploy step says `no access token available` again, the secret is not
where the job reads it. Run the `gh secret list` command from step 4 and check
the name (`FLY_API_TOKEN`) and the environment (`production`) letter by letter.
Nothing was deployed; production is untouched.

If the Deploy step fails while building or uploading the image (Docker or pip
output in the log), nothing was released, so production is still on the old
code; Verify prints `29 False` if you want to confirm. CI's tests run on Python
3.12, the same as the Dockerfile, so this would be a new finding. Bring back
the whole Deploy log and do not patch anything live.

If Deploy goes green but the smoke check ends with `never returned 200`, the
new machine either is not coming up or has not finished. Two look-alikes are
not failures (see docs/pre-deploy-checklist.md). The warning
`WARNING The app is not listening on the expected address`, listing only
`/.fly/hallpass`, is the window before uvicorn binds. And `curl` returning
HTTP 000 minutes later is `auto_stop` idling the machine; `stopped` in the
output of `fly status -a garden-gnome-api` means asleep, not broken. This first
boot also runs the migrations and the claim sync before uvicorn binds, so give
it another minute or two, run the Verify curl again, and read the logs
(`fly logs -a garden-gnome-api`) for a traceback naming a migration. Read the
log before you restore anything.

If the log shows a migration itself failing, the snapshot is the way back. This
is not the usual rollback: the one in docs/pre-deploy-checklist.md (redeploy
the previous image) is safe only for additive migrations, as v14's was. Here
0017 renames a table, so the old code cannot read the migrated file, and a
failure partway through can leave a file that neither version can read.
Restoring costs everything written to the database since the snapshot was
taken. flyctl 0.4.76 has no one-step restore: `fly volumes snapshots --help`
lists only `create` and `list`. `fly volumes create` has a `--snapshot-id`
option ("Create the volume from the specified snapshot"), after which the
machine has to be put onto the new volume. I have not tested that sequence and
it is destructive, so it is not scripted here: stop at that point, keep the
log, and bring both back (the `snapshots list` command from step 2 gives you
the snapshot ID). Restoring also does not fix the cause; the new code fails the
same way on its next boot until that is fixed.

If the log shows `claim sync skipped`, the API is up but the species rows are
stale: the sync failed, was fenced so it could not take the boot down, and the
traceback is in the lines just above that message. It runs again on the next
boot, which heals a one-off failure; a deterministic one will print it again.
No rollback needed. Bring the traceback back.

## What to report back

Whatever happens: how the Deploy and Smoke check steps ended (or the last lines
of `flyctl deploy` if you went by hand), what the Verify command printed, and,
if anything looks off, the `fly logs` lines from the first `Running upgrade`
through the claim sync, or the traceback. If you deployed before a new
TestFlight build, also whether the Species tab in 1.1.2 crashes after the
deploy, and whether its Census tab opens. Tell me when it is green too, so the
"one-time setup is still required" banner in docs/deploys.md can come down.

## Also yours, later: the mobile app

TestFlight is at 1.1.2, and the growing-area UI exists only in the `mobile/`
source. Getting it onto phones needs a new EAS build from the Windows box and
your Apple account, cut from master after #21 has merged (see "Why this
matters"), so it is a separate handoff. Until it ships, 1.1.2 runs against the
new backend with the one exception listed there: the Species tab.
