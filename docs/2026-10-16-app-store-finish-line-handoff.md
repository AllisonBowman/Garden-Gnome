# PlantAdvocate 1.1.3 to App Review: what only you can do

Written 2026-10-16 on the Mac about `care-advice-honesty` at `798f905`. Every
step here needs your GitHub, Fly, Cloudflare or Apple login, or a phone in your
hand. The Windows box isn't needed: every command is zsh on this Mac, one
command per block, and the blocks have no `#` comments, because interactive
zsh doesn't treat `#` as a comment unless you've turned that on.

This file supersedes `docs/2026-10-01-fly-deploy-handoff.md`. That doc's
migration range (0010 to 0020), VM size (256 MB), smoke check (12 tries in
2 minutes, with no catalog check) and claim count (6,989) are all out of date.
Where its restore advice still holds, it's repeated here, so you don't need it
open.

**Update, 2026-10-31.** Read this first; the checklist below it is the
launch morning. Written on this Mac in the main checkout, from `26ffeed`.

What landed on `care-advice-honesty` today, all pushed:

- The gtm-critic docs lane (`origin/claude/lane-gtm-critic`, now at
  `a8d64f0`) is folded in: its ten commits, `754411d` to `2ac7b19`, brought
  the go-to-market files and this handoff up to the 2026-10-30 changes.
- This handoff opens with the A to E checklist, the build has its own
  section before step 1, and the step headings carry their letters. The
  pre-launch table in `docs/go-to-market/launch-day-runbook.md` and this
  file's step 4 gained one step the review found: in App Store Connect,
  untick Apple silicon Mac and Apple Vision Pro availability, because an
  iPhone app is offered on both unless you do.
- `fly.toml` says `min_machines_running = 1` (decision 1, yes). Step 2's
  deploy applies it; a one-line PR puts it back after approval.
- `docs/go-to-market/launch-day-site.md` exists. The launch-day site
  branch, `claude/launch-day-site`, was rebased onto the ship tip, reviewed
  against Apple's marketing guidelines, trademark guidelines, trademark
  list and Smart App Banner page, fixed, and pushed at `d279afc`
  (`launch-day-site-reviewed` points at the same commit; the old draft
  `fa4076b` is gone from both). Seven commits on top of the ship tip, all
  under `site/`: text links to the US product page in place of every
  early-access call to action, the banner tag, Open Graph tags, Apple's
  credit line (App Store credited as the registered service mark Apple's
  own footer calls it), a press page, and the README's after-launch-day
  check group. It changes no privacy policy wording and carries no badge.
  Its pull request is not open; the runbook has you ask for it before L.
  Never merge or deploy it before launch morning.
- Four lines on the pre-launch site, found by the same review, ride with
  step 3: the FAQ says every researched species page shows its sources,
  Plant resources says the catalog cites its organizations, the pricing
  page links to the planned nursery program, and the homepage has a meta
  description. `docs/app-store/listing.md` says the United States only.
- The gates on `2ac7b19`, the last commit that touched app code apart from
  `fly.toml`: backend 7,094 passed, mobile 557 passed in 50 suites,
  typecheck clean, leak scan clean, `site/` 13 pages with 0 broken links
  (the launch-day branch 14 and 0). On this Mac jest needs
  `npx jest --watchman=false`, because the sandbox blocks watchman; CI is
  unaffected. PR #22's CI was green on `2ac7b19` and again on `0db827b`, both test
  jobs passing, mergeable and clean; the pushes after it are documents
  only.

Allison answered the seven questions by email at 16:38 ET: "follow
recommendations in all cases". So taro stays on the "something to eat"
lists with its preparation note; the Invasive Species exclusion keeps its
five species off candidate lists; lily of the valley reads "Toxic", as NC
State rates it; 1.1.3 ships with the short care notes, and the lengthened
notes are finished on branch `care-notes-1.1.4` so she can demo both
versions; `min_machines_running` stays 1 through App Review and goes back
to 0 after approval; screenshots 03 and 06 are not retaken; and the work
runs on this Mac. Decisions 1, 6 and 12 below are settled by that answer.

The care notes: `care-notes-1.1.4` was cut from `2ac7b19`. Its lengthening
runs as a workflow, two writers, a judge and three adversarial verifiers
per species, every sentence traced to a quote in the species' verified
record, then an assembler that pins the text and the trace in tests and a
completeness critic. The first run hit the account's session limit before
any note cleared verification; it was resumed at 17:33 ET, and the next
block or the branch's own handoff, `docs/2026-10-31-care-notes-1.1.4-handoff.md`,
says how it ended. It is not merged anywhere.

Checked from this Mac today: production still answers
`{"status":"ok","service":"garden-gnome","version":"0.2.0"}` with 29 paths
and no `/growing-areas`, and https://plantadvocate.ai still serves the
October 16 pages (a privacy policy dated October 16, "EVERY FACT CITED" on
the homepage). Nothing was deployed, merged, built or submitted today.
Nothing is open for you beyond the checklist.

## The launch morning, A to E

Everything below, in the order to run it. Each line names the section that
holds the exact commands and what to look for; tick a line only when that
section's checks pass. Nothing here has been done: nothing builds, merges,
deploys or submits until you run it, and every command is yours because it
needs your Apple, GitHub, Fly or Cloudflare sign-in.

Before the morning:

- [ ] Answer the twelve decisions under "Decide these first". Each has a
      default, and the seven questions emailed to you on 2026-10-31 (taro,
      the Invasive Species exclusion, lily of the valley, the short care
      notes, `min_machines_running`, screenshots 03 and 06, and where the
      session runs) carry the same defaults, so silence means the defaults.
- [ ] Decision 1 defaults to yes and is already on PR #22
      (`min_machines_running = 1` since 2026-10-31). If you want it back to
      0, tell me before you merge and wait for CI to go green again.

A. The build (section A):

- [ ] `cd mobile && npx --yes eas-cli@latest build --profile production --platform ios`,
      sign in to Apple when EAS asks, and let it manage credentials.
- [ ] Fill in the three lines in section A from
      `npx --yes eas-cli@latest build:list --platform ios --limit 1`: the
      build number (17 or higher), the EAS build ID, and the commit (the tip
      of `care-advice-honesty`, `2ac7b19` or later).
- [ ] On the build's page, check the image is `macos-tahoe-26.5-xcode-26.6`.

B. Merge PR #22 (section B, step 1):

- [ ] `gh auth status` shows you.
- [ ] `gh pr checks 22 --repo AllisonBowman/Garden-Gnome`: Backend tests
      and Mobile typecheck and tests both `pass`.
- [ ] `gh pr view 22 --repo AllisonBowman/Garden-Gnome --json headRefOid,mergeable,mergeStateStatus`:
      the build's commit, `MERGEABLE`, `CLEAN`.
- [ ] `gh pr merge 22 --repo AllisonBowman/Garden-Gnome --merge`.
- [ ] `gh run list --repo AllisonBowman/Garden-Gnome --branch master --limit 1`
      gives RUN_ID; `gh run watch RUN_ID --repo AllisonBowman/Garden-Gnome`
      ends with the two test jobs green and Deploy to Fly red with
      `no access token available`, which is expected.

C. Fly (section C, step 2):

- [ ] `fly auth login`, then `fly auth whoami` shows your email.
- [ ] `fly status -a garden-gnome-api` and
      `fly secrets list -a garden-gnome-api`; write the secret names down.
- [ ] Wake the machine with `curl -s --max-time 30 https://garden-gnome-api.fly.dev/`,
      open `fly ssh console -a garden-gnome-api`, and run the orphan check
      at the machine's prompt: it must print `[]`. Make the optional
      database copy (decision 4) if you want the rehearsal, then `exit`.
- [ ] `fly volumes list -a garden-gnome-api` gives VOLUME_ID;
      `fly volumes show VOLUME_ID -a garden-gnome-api` (write down the
      retention); `fly volumes snapshots create VOLUME_ID`;
      `fly volumes snapshots list VOLUME_ID` shows a snapshot from now.
- [ ] `fly tokens create deploy -x 999999h -a garden-gnome-api`, pasted
      straight into `gh secret set FLY_API_TOKEN --env production --repo AllisonBowman/Garden-Gnome`;
      then `gh secret list --env production --repo AllisonBowman/Garden-Gnome`
      lists it.
- [ ] `gh run rerun RUN_ID --failed --repo AllisonBowman/Garden-Gnome`, then
      `gh run watch RUN_ID --repo AllisonBowman/Garden-Gnome`: Deploy and
      Smoke check green, with `up after N attempt(s)`.
- [ ] Verify, each as section C prints it: the openapi line prints
      `34 True`; `GET /` shows `"version": "8c520db39b21:6:1"`,
      `"synced": true` and `"claims": 10681`; `/ai/status` is `stub`
      everywhere; `/growing-areas/` answers `401` and `/census/export`
      `404`; `fly scale show` says 512 MB; and
      `fly logs -a garden-gnome-api --no-tail` runs from
      `0009_aloe_vera -> 0010_claims` to
      `0021_pending_apple_revocation -> 0022_backfill_acquired_on`, then
      `curated text refreshed N` with N above 0, then the
      `claim sync: written` block, with no traceback.

D. Cloudflare (sections D1 and D2, the waitlist and step 3):

- [ ] Export the July waitlist first, with the commands in
      `docs/go-to-market/launch-kit/waitlist-email.md` under "Before step
      3", into `$HOME/PlantAdvocate-private`.
- [ ] `cd /Users/allisonbowman/Developer/Garden-Gnome`; `git status --short`
      prints nothing; `git log -1 --format='%h %d'` names
      `care-advice-honesty` at the build's commit or later (if it's older,
      `git pull --ff-only`).
- [ ] `npx wrangler login`; `npx wrangler pages project list` gives PROJECT;
      `npx wrangler pages deployment list --project-name=PROJECT` gives
      PRODUCTION_BRANCH.
- [ ] The link check in section D2 ends `13 pages, 0 broken`.
- [ ] `D=$(mktemp -d) && cp -R site/. "$D" && rm "$D/README-SITE.md" && npx wrangler pages deploy "$D" --project-name=PROJECT --branch=PRODUCTION_BRANCH`.
- [ ] `sed -n '/^## Verifying the deploy/,/^## When the app changes/p' site/README-SITE.md`
      prints the verify block; run it, and every line prints `ok`. The two
      `curl` lines after it print `200`. Open https://plantadvocate.ai/privacy
      on your phone: October 20 and the "What changed" line are at the top.

E. App Store Connect (sections E1 to E3, steps 4 to 6):

- [ ] `cd /Users/allisonbowman/Developer/Garden-Gnome/mobile`;
      `npx --yes eas-cli@latest whoami` shows `allisonbowman`;
      `npx --yes eas-cli@latest build:view EAS_BUILD_ID` shows finished,
      1.1.3, the build number and the commit.
- [ ] `npx --yes eas-cli@latest submit --platform ios --profile production --id EAS_BUILD_ID`,
      signing in to Apple when asked; then wait for Apple's processing email
      and watch it for `ITMS-91` codes.
- [ ] TestFlight: paste What's New from `docs/app-store/listing.md` into
      What to Test, install the build on a phone, and go through the twelve
      checks in section E2. Anything that reads wrong comes to me before
      you submit.
- [ ] App Information from `listing.md` and `age-rating.md` (4+); Pricing
      and Availability: Free, the United States only, no pre-order, and Mac
      and Apple Vision Pro availability unticked; App Privacy from
      `app-privacy.md`, the seven types, published.
- [ ] The 1.1.3 version page: promotional text, description and the
      keywords for the subtitle you chose (decision 10); the support and
      marketing URLs and the copyright; the build by its number; App Review
      Information from `review-notes.md` with Sign-in required ticked, your
      phone in plus-sign format and the Notes block pasted as it is with its
      two brackets filled; Manually release this version.
- [ ] Screenshots: `docs/screenshots/1.1.3/17-pro-max/` to the 6.9" size and
      `17-pro/` to the 6.3" size, each in the order 01, 04, 06, 02, 03, 05,
      07, 08. 03 and 06 go up as they are unless you asked for a retake
      (decision 12).
- [ ] Wake the server: `curl -s --max-time 30 https://garden-gnome-api.fly.dev/`
      shows `"synced": true`. Then Add for Review, Submit for Review, and
      the status reads Waiting for Review.
- [ ] Report back with the list at the end of this file.

**Update, 2026-10-30.** The steps below were brought up to date in place,
and `docs/2026-10-26-go-to-market-handoff.md` is folded into them. Where
the 2026-10-31 block above says something different, it wins.

The go-to-market branch, `claude/go-to-market-strategy-cd07f3`, was folded
into `care-advice-honesty` at `b6fee6b` and pushed. So the °F fix and the 25
mended dashes reach 1.1.3, along with the screenshots, the rewritten review
notes and the go-to-market documents. More lands on that tip today. The
curated care notes stop making safety claims of their own, the 33 "Pet-safe"
notes and the 6 that contradicted their cited records among them. Every boot
now brings the curated prose in line with the catalog file, which replaces
the production one-off the go-to-market handoff described (step 2 says what
to look for in the logs). The hazard sentences change in three ways, all on
the server: readers outside the US are pointed to their local poison
centre, a cited pet verdict names its source, and the words that come from
the code's own tables, the lily, daylily and arum ones among them, are
labelled "PlantAdvocate's own summary". The app shows "These notes repeat
what the sources publish. They are not medical or veterinary advice." under
each hazard note, and a "Report a fact" link at the foot of each species
page's sources. And the site copy fixes ride with step 3, the privacy
policy's narrower marketing-email line among them. Build from the tip of
`care-advice-honesty` that carries all of it, later than `b6fee6b`. Those
changes touch app code, so PR #22's CI runs again on that tip; wait for
green as before.

The build is still yours to start with your Apple sign-in, exactly as the
next block says. Build it on EAS with the image `mobile/eas.json` pins, never
on this Mac (the iOS 27 note in step 4 says why).

The live site isn't the July build any more. By 23 October someone had
deployed the October 16 rewrite, and on 30 October plantadvocate.ai still
served a privacy policy dated October 16 and a homepage that says "EVERY
FACT CITED". So step 3 is a redeploy, for the newer privacy text (effective
October 20) and today's fixes. Export the July waitlist before it, in the new
section between steps 2 and 3.

What else moved: decision 7 points at the Notes' SIGN-IN paragraph;
decisions 10 to 12 are new, 12 being whether to retake three screenshots
that predate today's changes; step 4 has the Notes block's real size, the
plus-sign phone format, the screenshots that already exist and their upload
order, and the iOS 27 note; step 5 checks the new line, the link, the new
hazard wording and the rewritten notes; and "Settled since the lanes
reported" lists what today settled. If
you haven't filed the App Launch featuring nomination yet, it waits on
nothing here (`docs/go-to-market/strategy.md`, "Featuring Nominations").

**The build** is section A below, after the decisions, with its three
lines to fill in.

**Update, 2026-10-17 and 2026-10-20.** The build was never started on the
16th, and on the 20th the attempt from this Mac stopped at the certificate
check described above, so the three lines are still blank and the command
is yours to run. On the 20th the 41 findings of the adversarial review of the
ship diff were fixed in 28 more commits (toxicity sentences scoped to people
and pets separately, census export 4.1 that no identifier links across
exports, cached data kept on a failed refresh, local dates for acquisition,
and the rest); the tip is `b98c2b7`, every gate is green (backend 6,884,
mobile 541, typecheck and leak scan clean), and CI on it was pending as this
was written. Checked
again today: PR #22's CI is green on `62d3a66` and the PR is mergeable;
production still has 29 paths and no `/growing-areas`; the live site still
serves the July pages; the repo still has no secrets; and `npx wrangler
whoami` on this Mac says its token has expired, so step 3 starts with
`npx wrangler login`. Decision 6 below is settled for four of its five
species, which changed the catalog this build ships: the smoke-check numbers
in step 2 now read 10,681 claims and version `8c520db39b21:6:1`, from a
scratch boot on this Mac today.

**Update, 2026-10-20.** A review of the ship branch at `798f905` found
problems that three lanes fixed on top of `307930e`, so build from the tip
that carries them, not from `798f905`. In short: the census export is
version 4.1 (records shuffled, care counted per type per month, moves and
acquisition dated by month); a deleted account's queued Apple revoke is
deleted after 30 days or 10 tries, whichever comes first; a severity word in
a hazard sentence belongs to people only, and a food crop's sentence leads
with the part that's eaten; a species a source rates as a serious or fatal
poison for people is never a candidate unless it is a food crop eaten
without conditions; and the app reads a server date like `2026-10-20` as
that local day, not as midnight UTC. The site, privacy policy and
`docs/app-store/` now say the same. Where that settles something below, it
says so. Nothing was re-checked against production, EAS or the live site
today, and the claim and catalog numbers above weren't re-run.

**Checked from this Mac tonight.** The working tree is clean and
`origin/care-advice-honesty` is `798f905`, 140 commits past `origin/master`
(`db4f561`, the merge of PR #21). `bash .claude/bin/build-precheck.sh
production` says OK to build on `798f905`, with its usual two notes: the old
Android package name, and pick TestFlight builds by build number. (Its
"1.0.0" wording comes from an older version, but the rule still holds.)

Production, https://garden-gnome-api.fly.dev, still runs the old code:

- `openapi.json` has 29 paths and no `/growing-areas`.
- `GET /` answers `{"status":"ok","service":"garden-gnome","version":"0.2.0"}`,
  with no catalog block.
- `/growing-areas/` answers 404 and `/census/export` answers 401.
- `/ai/status` reports every AI backend as `stub`, with vision `ready: false`.

The live https://plantadvocate.ai still serves the July 17 pages: all four
lines of the README's check block that I ran came back FAIL. The `site/`
folder passes its link check (13 pages, 0 broken).

I also ran the new image's boot command on an empty scratch database. The
migrations ended with `0021_pending_apple_revocation -> 0022_backfill_acquired_on`, then
`claim sync: written` with `claims stored 10681`, and `GET /` answered
`"catalog": {"version": "8c520db39b21:6:1", "synced": true, "species": 997,
"claims": 10681}`. The new code's `openapi.json` has 34 paths, six of them
under `/growing-areas`. The orphan check in step 2 printed `[]` on a scratch
database built at 0009.

**Taken from the orchestrator, not re-checked here.** This sandbox can't reach
GitHub. PR #22 (https://github.com/AllisonBowman/Garden-Gnome/pull/22) is open,
and CI on `798f905` was pending. The local gates are green: backend 6,814
tests, mobile 481, typecheck and leak scan clean. Neither the repo nor its
`production` environment has any secrets, so there is no `FLY_API_TOKEN`.

## Why this matters

1.1.3 will be the first version App Review has ever seen. 1.1.0 to 1.1.2 went
to TestFlight only, and the newest of those is 1.1.2 build 15, from August 2.
The ship branch is 140 commits that nobody has run on a phone:

- growing areas and the fit engine
- hazard sentences that name people
- edibility shown only with its conditions
- an operator-only census
- new permission strings, with the Location Always, Motion and Face ID keys
  removed
- iPhone only
- a privacy manifest
- error boundaries and retry states
- a different sign-out rule

The native parts exist only in `app.json` until tonight's build compiles them.
The backend half has never been deployed by CI. Production's database is at
Alembic 0009, so its first boot runs twelve migrations in one go. One of them,
0017, renames the `environment` table to `growingarea`, and SQLite won't roll
that back if it fails partway. The claim sync then rewrites production's
species rows, about 1,900 of which are older uncited imports this sync has
never touched. Meanwhile the privacy page the app links to says the app
doesn't collect precise location, the support page sells subscriptions, and
App Review reads both.

What nobody knows yet:

- how 0017 and the claim sync behave on production's real data (they have
  only run on scratch databases)
- whether the build behaves on a phone
- whether a wrangler deploy from this repo lands on the production domain (it
  has never been done from here; the July site came from a generator on the
  desktop machine)
- how App Review will treat an app that signs in only with Apple or Google and
  has no demo account

One cost starts the moment step 2 deploys, and you're choosing it. TestFlight
1.1.2's Census "Sync now" will get a 404. Its Species tab will throw when a
claim-minted species row scrolls into view, because those rows have no
`light_need` and 1.1.2 reads it unguarded: 868 such rows on a scratch
database, and on production the `species created` line in the logs. That
lasts until testers are on 1.1.3. Step 4's upload doesn't depend on steps 2
and 3, so you can upload first to keep that window short.

## Decide these first

Each one comes with my recommendation. The first twelve change what happens
in the steps. The rest can wait until after you submit; none of them blocks
this submission.

1. **Keep the server awake during review.** Settled yes by Allison on
   2026-10-31, revert after approval, and the yes is on the branch: `fly.toml` says
   `min_machines_running = 1`, so step 2's deploy keeps one machine running.
   Until then the machine sleeps when idle, and a first request after idle
   took 6.7 s on 15 October, an easy way for a reviewer's first screen to
   say it couldn't reach the server. The cost: the machine bills all day
   instead of only while it's answering. If you'd rather not pay it, tell me
   before you merge and I'll put the line back to 0 on PR #22, after which
   CI runs again and you wait for green. After approval, a one-line PR puts
   it back to 0 (the launch-day runbook suggests waiting until L+7). Either
   way, step 6 has you wake the server just before you press Submit.
2. **The VM goes to 512 MB.** `fly.toml` now asks for 512 MB instead of 256,
   and the deploy in step 2 applies that, which changes what Fly charges for
   the machine. Recommend accepting it. Before the new species-list cache,
   ten phones loading the catalog at once took the process past 240 MB. With
   the cache it sits near 155 MB, and the rest is margin. If you don't want
   it, say so before step 1.
3. **`CENSUS_OPERATOR_TOKEN` as a Fly secret.** Recommend no. While it's
   unset, `/census/export` and `/census/sync` answer 404 to everyone. That's
   the safe state, and it's what the privacy answers and review notes assume.
   Nothing in 1.1.3 calls either route. If you ever set it, an export reads
   `"export_version": "4.1"`.
4. **Rehearse the boot on a copy of production's database first.** Recommend
   yes if you have the time. It's the only way to see 0017, the claim sync
   and, since 2026-10-30, the curated-text refresh run against the real rows
   before they run live. Step 2 shows how to make
   the copy. I'd run the migrations and the sync against it on this Mac and
   tell you what production will see. If you skip it, the orphan check and
   the snapshot are the safety net.
5. **Settled: adding species to the shared catalog is now an operator job.**
   The audit found that `POST /species/`, `/species/bulk` and
   `/species/generate` only checked that the caller was signed in, so anyone
   with an Apple ID could have added a plant every user would then see. They
   now take the same `X-Operator-Token` as the census export and are hidden
   from the public schema; with no `CENSUS_OPERATOR_TOKEN` set on Fly they
   answer 404. The app never calls them. The catalog-expansion script
   (`garden-gnome/app/data/expansion/run_expansion.py`) does, so it needs the
   token when you next run it. Backend-only: it ships with the deploy.
6. **Settled for four of the five poisonous species; the fifth is yours.**
   Foxglove, English yew, monkshood and jimsonweed now carry NC State's
   Poisonous to Humans block (Poison Severity: High), re-read on the live
   pages on 2026-10-17 and checked quote by quote. Since the 2026-10-20 fixes,
   "Seriously" in their sentences is about people, because NC State's Poison
   Severity rates harm to people; pets are named as toxic, and as seriously so
   only where a source's own animal wording is grave. Each names NC State's
   rating and is never put forward as a growing-area candidate. Lily of the
   valley is different: NC State's live page rates it Poison Severity: Low
   ("toxic only if large quantities eaten"), while Missouri Botanical Garden
   calls all parts very poisonous. Citing NC State would make the app say "NC
   State Extension rates it low severity" beside "Seriously toxic" (the server
   keeps the graver source), and would take it off candidate lists. Settled by Allison on 2026-10-31: it stays as it is for this
   submission, "Toxic to pets and people", its hazard line shown, still a
   possible candidate for a shady bed. Changing that later is a one-record
   change and a deploy, no app build.
7. **The "Sign-in required" box in App Review Information.** Tick it;
   `docs/app-store/review-notes.md` says the same, under Sign-In
   Information. The app does require sign-in before it shows anything, so
   ticking it is the accurate answer, and the Notes' SIGN-IN paragraph tells
   the reviewer how to get in: tap Sign in with Apple and use their own
   Apple ID. If the form then insists on credentials, put `Sign in with
   Apple` in User name and `none needed` in Password. Never hand over a
   personal Google login.
8. **Does the opt-in census count as Analytics?** It's already declared that
   way, in the manifest and in `app-privacy.md`: Coarse Location and Other
   User Content each list App Functionality plus Analytics. Recommend keeping
   it and confirming it in App Store Connect in step 4. Support email is
   declared as collected Customer Support data, which is also right.
9. **The waitlist addresses.** The July site had a `/api/waitlist` Pages
   Function that its homepage posted early-access emails to. Step 3's
   deploy drops the endpoint, though the data stays in Cloudflare.
   Recommend exporting the addresses before step 3, in the section between
   steps 2 and 3, and leaving the function retired: the new pages use a
   mailto link. The policy promises those addresses are used only to tell
   people about PlantAdvocate. Whether to email them, and how, is in
   `docs/go-to-market/launch-kit/waitlist-email.md`.
10. **The subtitle and keywords you paste in step 4.** Recommend the
   strategy's pair: subtitle `Plants that suit each spot` and the 97-character
   field A in `docs/go-to-market/launch-kit/listing-proposals.md`, which
   adds "cat", "dog", "poison", "indoor" and "gardening". It reaches the two
   thin searches, pet hazards and watering reminders. Those pet words are
   honest only because today's care-note rewrite reaches production with
   step 2's deploy, before you press Release. listing-proposals.md also
   weighs the cost (in pet searches, "plants that suit" can read as "plants
   that are safe") and offers `Plants checked for each spot` with the same
   field. Keeping listing.md's subtitle and keywords is the other choice.
   Name and subtitle change only with a new version, so this is the cheapest
   moment.
11. **Where 1.1.3 is available.** Recommend the United States only, with a
   manual release and no pre-order (`docs/go-to-market/strategy.md`, step
   zero). The app is in English, in feet, inches and Fahrenheit, and the
   few early ratings should land on the one store page the keyword research
   was done for. The hazard sentences no longer argue for it: since 2026-10-30 they
   add "or your local poison centre" after the US number. listing.md still
   says Free in every territory; you choose in Pricing and Availability in
   step 4.
12. **Retake screenshots 03, 05 and 06?** They were shot from `3f6d7da`,
   before the 2026-10-30 changes. Shot 06's Pothos sentence lacks "or your
   local poison centre", the pets' source line and the "PlantAdvocate's own
   summary" label, and no frame shows the not-advice line, which the build
   now puts under the sentence in 06 and under Lady Fern's note in 03. Shot
   05's Sources card may or may not reach down to the new "Report a fact"
   link. Settled by Allison on 2026-10-31: all three stay as they are for
   this submission, because each frame still shows the app truthfully, the
   wording that moved is a clause inside one sentence, and a retake costs
   a two-day screenshot garden on the new backend. If you'd rather the
   frames match the new wording, say so: the recipe is in
   `docs/screenshots/1.1.3/README.md` under "How they were made", the
   retake comes from the build's commit on the iOS 26.5 simulators, and
   `CHECK.md` runs again before step 4.

These can wait until after submission:

- **The ~1,900 uncited Perenual-era species rows production keeps.** They're
  listed in the catalog, so reviewers can open them, and each fact on them is
  labelled as not yet cited. Recommend keeping them for this submission.
  Hiding them means deciding what happens to plants that point at them,
  which is a data change nobody has tested. "More than 990 species" stays
  true either way, because it counts researched species.
- **Who receives census syncs (`CENSUS_API_URL`).** Recommend nobody for now.
  The policy says PlantAdvocate keeps census data and will name any other
  organization before data goes to it. The dated care history that let one
  export be matched to the next is gone (export 4.1, settled below), but a
  planting's monthly care counts can still resemble it from one export to
  the next. That's why the policy promises only that no identifier links
  exports. True totals would need aggregation before anyone outside
  receives it.
- **Water-regime mapping.** Recommend the stricter rule, "a bare MBG or RHS
  rating never sets a regime". One mapping table would invent a
  correspondence the sources don't make: MBG's "Dry to medium" resolves two
  different ways today. The stricter rule drops about 30 regimes and changes
  the pinned claim counts, so it goes through the research loop as its own
  change.
- **The 50 uncited legacy toxicity flags in `species_catalog.json`.** The
  wording is already honest: a bare flag reads "Toxic to pets.", and an
  uncited "no" reads as nothing recorded in our sources yet. Recommend citing
  or nulling them through the research loop.
- **Noxious-weed status for about 14 species** (Bradford pear, butterfly
  bush, Japanese honeysuckle, lantana, sacred lotus, white mulberry, Chinese
  wisteria, burning bush, thorny elaeagnus, tansy, woodland forget-me-not,
  water lettuce, princess flower, small-leaf spiderwort). It lives only in
  research notes, so the exclusion rule fires on nothing. Recommend promoting
  it to a claim field after review. That's a schema and migration decision.
- **US-only Poison Control.** Settled on 2026-10-30, with the hazard
  sentences below: a sentence that names people now says "call Poison
  Control (US 1-800-222-1222) or your local poison centre right away", and
  "Poison Control (US 1-800-222-1222), your local poison centre or a vet"
  where pets are named too. Widening availability past the US is still
  decision 11's question, for after launch.
- **Citing the hazard tables' own words.** Since 2026-10-30 they are
  labelled "PlantAdvocate's own summary" in the sentence (below). Finding a
  cited passage for each, species by species, would let the label go; that
  is research-loop work, after review.
- **A grace window for a just-rotated refresh token** on the server, so a
  refresh whose response got lost doesn't sign someone out. Recommend doing
  it after review, backend only.
- **Wiring the app's network-state awareness**, which needs
  `@react-native-community/netinfo`, a new native dependency. Recommend
  leaving it out of this build.
- **Naming the AI provider in the app.** This is moot while photo check-ups
  and symptom reading are off. When you switch either on, first follow the
  four steps at the end of `docs/app-store/app-privacy.md`, and name the
  company in the in-app consent (the site policy already names Anthropic).
  Keep `ADVISOR_BACKEND` at `stub`, because the policy says everyday advice
  is rule-based.
- **Two species are both named "Blackberry".** Recommend renaming *Rubus
  fruticosus* to "European Blackberry".
- **288 catalog values rest only on Missouri Botanical Garden citations**
  that can't be re-checked from this machine, and 47 of them could cause harm
  if wrong. Recommend a re-verification pass in a browser, harm-capable ones
  first.
- **Amaryllis, Angel's Trumpet, Cattleya and Nymphaea** were researched at
  genus level and never become catalog rows. This needs a representative
  species each, or a genus-row type. After review.
- **Open-Meteo's free tier is for non-commercial use.** Revisit it before
  PlantAdvocate ever charges for anything.
- **The desktop site generator.** Don't run it until it's reconciled with
  `site/` (the checklist at the end of `site/README-SITE.md`). Otherwise it
  puts the July pages back.
- **At launch**, replace the site's "in beta on iPhone", "Email us for early
  access" and the "Get early access" nav button with the App Store link.
  That's why step 4 recommends releasing manually. The edits are reviewed and wait on branch `claude/launch-day-site` (`docs/go-to-market/launch-day-site.md` lists them); don't merge or deploy it before launch day, and follow `docs/go-to-market/launch-day-runbook.md` when the day comes.
- **Two policy statements to confirm.** First, that Fly keeps volume
  snapshots for 5 days (step 2 shows the retention). Second, that Anthropic's
  commercial terms bar training on API content: read the current terms, since
  the policy says so.

Settled since the lanes reported, so not decisions any more:

- The curated care notes (2026-10-30). The 33 that called a plant
  "Pet-safe", "harmless" or "safe for most pets", and the 6 that
  contradicted their cited records (Sage, Thyme, Baby's Breath, Hollyhock,
  China Aster, Moonflower), were rewritten without a safety claim, keeping
  the care advice. Toxicity is stated in one place, the hazard sentence, so
  a care note makes no safety claim of its own.
- Curated prose follows the file on every boot (2026-10-30). `seed()` used
  to skip a species it already had, so production would have kept the
  garbled dashes and the old notes for good. Now, on every boot, it sets
  `care_notes` and `soil_type` on the 129 curated species, and the notes on
  their check schedules, to what `garden-gnome/app/data/species_catalog.json`
  says wherever the two differ. It touches no resolved or claim-backed
  field. The write stamps a new catalog generation the way every catalog
  write does, so phones get the new text on their next fetch. It logs
  `curated text refreshed N`. This replaces the production one-off in
  `docs/2026-10-26-go-to-market-handoff.md`, item 3, which nobody needs to
  run now.
- The three hazard-sentence changes from the go-to-market handoff's item 4
  (2026-10-30, backend only, so they ship with step 2's deploy). Readers
  outside the US are pointed to their local poison centre, after the US
  number. A pet verdict a source settled names it: "For pets, the source is
  NC State Extension." And words that come from the code's own tables
  rather than a cited passage, the lily and daylily kidney wording, the
  arum family's calcium oxalate wording, tomato's and rhubarb's, now follow
  the lead as "PlantAdvocate's own summary: ...". The catalog lane counted
  365 sentences changed: 305 gain the local poison centre, 278 name the pet
  verdict's source and 29 carry the label. That closes the gap the
  go-to-market files flagged in "These notes repeat what the sources
  publish", once the deploy is live.
- The not-advice line is in 1.1.3 (2026-10-30): "These notes repeat what
  the sources publish. They are not medical or veterinary advice." under
  the hazard sentence on species pages, in a plant page's Care guide card
  and under a species picked in Add plant (`mobile/src/care/notAdvice.ts`).
  The listing, the review notes and the 1.4.1 reply now say the app shows
  it.
- A "Report a fact" link is in 1.1.3 too (2026-10-30), at the foot of each
  species page's Sources card, or in the same spot when a species has no
  sources yet. It opens a prefilled email to support naming the species and
  the facts the page shows, like "Report this result".
- The site copy fixes ride with step 3 (2026-10-30): the five in
  `docs/go-to-market/strategy.md`, "The site, riding along with step 3",
  and the sixth the go-to-market handoff added, `recommendations.html`'s
  promise about a fiddle leaf fig in a bathroom, which the fit engine can't
  judge indoors. The same pass narrowed the privacy policy's account
  paragraph, which said flatly "we don't send marketing email", to say the
  address you sign in with never goes on a mailing list and news goes only
  to people who asked for it; it says what a removed early-access address
  leaves behind; and the FAQ carries the not-advice line. The effective date
  stays October 20, and `site/README-SITE.md`'s check block tests all of
  it.
- The go-to-market branch is on `care-advice-honesty`, folded in at
  `b6fee6b` and pushed (2026-10-30).
- Which poisons can be candidates. A species a source rates as a serious
  or fatal poison for people is never put forward unless it is a food crop
  whose cited edibility has no conditions, whatever the bed's goals. So
  potato, eggplant, peanut, tomatillo and butter bean can appear, with their
  hazard line and edibility note; mayapple, taro and wisteria never do, and
  neither do poison hemlock, belladonna or castor bean (2026-10-20 fixes).
- How hazard sentences read. A severity word ("Seriously", "Mildly") comes
  from a rating of harm to people, so it qualifies people only. Animals are
  "toxic to pets", or to cats or dogs, unless a plant's own table or grave
  animal wording says more. A food crop's sentence leads with the part
  that's eaten: "The tubers are the crop; the leaves, stems and sprouts are
  seriously toxic to people and pets." (2026-10-20 fixes.)
- The census export is version 4.1. Its records come in a random order, care
  is counted per type per calendar month, stewardship moves and acquisition
  are dated by month, and every identifier is new for each export. The
  in-app consent and `site/privacy.html` list exactly those fields
  (2026-10-20 fixes).
- A deleted account's queued Apple revoke is deleted after 30 days or 10
  tries, whichever comes first, and the policy's deletion paragraph says the
  encrypted grant can be kept up to 30 days only to retry the revoke
  (2026-10-20 fixes).
- A date-only value from the server, such as a plant's acquired date, is
  read by the app as that local day, so a new plant west of Greenwich no
  longer comes due a day early (2026-10-20 fixes).
- A new plant is dated from the day it's added, so its first check comes due
  (`7dac70d`).
- The manifest and `app-privacy.md` list the same seven types: no Photos,
  Customer Support included (`422b67c`).
- The server refuses model output that turns a warning into an assurance
  (`2e07c6f`).
- The retry states on every screen are in.

- **Taro on candidate lists.** No source rates taro high, so the poison rule
  leaves it in, and it is offered as "something to eat" with the note that it
  is eaten only after preparation. The only rule that would remove it would
  also remove tomato. Recommend leaving it: the note says what matters.
- **The "Invasive Species" exclusion.** NC State's invasive tag now keeps a
  species off candidate lists the way a noxious weed does (ADR 0009). It
  removes 5: Japanese and Chinese wisteria, beefsteak plant, leatherleaf
  mahonia and English ivy. They can still be looked up and added by hand.
  Recommend keeping it; reverting is one line in `toxicity.never_put_forward`.
- **If you ever set `CENSUS_OPERATOR_TOKEN`,** make it at least 32
  characters. A shorter one now counts as unset, with a warning at boot, and
  the export, sync and species-write routes stay at 404.

Engineering leftovers that need nothing from you: Add plant should say a
species has no check schedule before you add it (the species list the
screen reads carries no schedules, so this needs a per-species fetch and
a new build; left for 1.1.4); health checks in `fly.toml` (not before
the first deploy, whose boot runs twelve migrations and the claim sync
before the server answers); and the pinned flyctl 0.4.111 and
`python:3.12.15-slim-trixie` now need deliberate bumps. The `CONTEXT.md`
glossary entry for harm-capable fields now has ADR 0008's wording.

---

## A. The build, yours to start

**Updated 2026-10-20, re-read 2026-10-31.** Not started yet, and it needs you. From
this Mac, `eas build --profile production --platform ios --non-interactive`
gets as far as "Using remote iOS credentials", then stops with "Distribution
Certificate is not validated for non-interactive builds": EAS wants to check
the certificate with Apple, and that takes your Apple sign-in. Run it
yourself, without the non-interactive flag, from the repo root:

```bash
cd mobile && npx --yes eas-cli@latest build --profile production --platform ios
```

Say yes when it asks to validate the certificate and sign in to your Apple
account; let EAS manage credentials if it asks. The attempt on the 20th
already incremented the remote build number from 15 to 16 without building,
so expect the build to come out as 17 (or higher). The build runs on Expo's
machines for 15 to 30 minutes. When it finishes, fill in these three lines
from `npx --yes eas-cli@latest build:list --platform ios --limit 1`:

- Build number: `____` (expect 17 or higher; 1.1.2 was build 15)
- EAS build ID: `____`
- Commit EAS reports: `____` (the tip of `care-advice-honesty` when you
  run it: `2ac7b19` or later. No app code has changed since `26ffeed`;
  everything after it is documents)

Wherever a step below says "the build number", it means the first of those
lines. While you're on the build's page, check that it names the image
`macos-tahoe-26.5-xcode-26.6`, the one `mobile/eas.json` pins.

## B. Step 1: Merge PR #22, only once its CI is green

Check that the GitHub CLI is logged in as you:

```bash
gh auth status
```

Then the PR's checks:

```bash
gh pr checks 22 --repo AllisonBowman/Garden-Gnome
```

Look for **Backend tests** and **Mobile typecheck and tests** both reading
`pass`. The deploy job doesn't run on pull requests. If either still says
`pending`, run the same command with `--watch` added at the end and let it
finish. If either says `fail`, stop and bring me the output. Don't merge.

```bash
gh pr view 22 --repo AllisonBowman/Garden-Gnome --json headRefOid,mergeable,mergeStateStatus
```

Look for `headRefOid` matching the tip that carries the 2026-10-30 changes
(later than `b6fee6b`; or the newer commit, if I added the `fly.toml` line
from decision 1), `MERGEABLE`, and `CLEAN`. Apart from that `fly.toml` commit, it should be the commit EAS reports in
section A. On 2026-10-31 the PR's head was `2ac7b19`, mergeable and clean,
with both test jobs green. If it starts `b6fee6b`, `3f6d7da` or anything
older, the 2026-10-30 changes aren't on the PR yet: stop and tell me.

```bash
gh pr merge 22 --repo AllisonBowman/Garden-Gnome --merge
```

That makes a real merge commit, as every PR here has. It doesn't delete
`care-advice-honesty`, and you shouldn't either: it's the working branch. If
gh refuses, stop and bring me its message.

```bash
gh run list --repo AllisonBowman/Garden-Gnome --branch master --limit 1
```

That's the CI run the merge started. Write down its ID, the number in the ID
column. Step 2 calls it `RUN_ID`. Then watch it:

```bash
gh run watch RUN_ID --repo AllisonBowman/Garden-Gnome
```

Expect the two test jobs to go green, then **Deploy to Fly** to fail at its
Deploy step with `no access token available`. That's expected, because the
secret doesn't exist yet, and it means nothing was deployed: production is
untouched. If the test jobs fail on master after passing on the PR, stop and
bring me the log.

## C. Step 2: Deploy the backend to Fly

Do these in order. The orphan check and the snapshot both have to happen
before anything deploys, and nothing deploys until you re-run the failed job
at the end.

**Log in.**

```bash
fly auth login
```

```bash
fly auth whoami
```

Look for your email, not an error. flyctl on this Mac is 0.4.76, which is
fine: CI deploys with its own pinned 0.4.111.

**Look at what's there.**

```bash
fly status -a garden-gnome-api
```

```bash
fly secrets list -a garden-gnome-api
```

The second command shows names and digests, never values. Look for
`JWT_SECRET` and `FERNET_KEY`, and for the four that let account deletion ask
Apple to revoke the sign-in: `APPLE_TEAM_ID`, `APPLE_KEY_ID`,
`APPLE_BUNDLE_ID` and `APPLE_PRIVATE_KEY`. Look for the absence of
`CENSUS_OPERATOR_TOKEN`, `CENSUS_API_URL`, `ADVISOR_BACKEND`,
`ADVISOR_SYMPTOMS_BACKEND` and `VISION_BACKEND`. Write down the full list of
names for the report.

**Run the orphan check.** 0017 now refuses to rename anything if a plant or
stewardship record points at an area that doesn't exist. That refusal is
clean, but it leaves the API down until the rows are fixed, so look first.
Wake the machine:

```bash
curl -s --max-time 30 https://garden-gnome-api.fly.dev/
```

Expect the old answer, `{"status":"ok","service":"garden-gnome","version":"0.2.0"}`.
Then open a shell on the machine:

```bash
fly ssh console -a garden-gnome-api
```

At the machine's prompt, not your Mac's, paste:

```bash
python -c "import sqlite3;c=sqlite3.connect('/data/garden_gnome.db');print([r for t in ('plant','stewardshiprecord') for r in c.execute(f'PRAGMA foreign_key_check({t})') if r[2]=='environment'])"
```

It must print `[]`. Anything else is a list of rows pointing at missing
areas. Stop there and bring me the output. Don't deploy, and don't edit the
rows by hand.

**Optional, decision 4: copy the database for a rehearsal.** Still at the
machine's prompt:

```bash
python -c "import sqlite3;s=sqlite3.connect('/data/garden_gnome.db');d=sqlite3.connect('/tmp/pa-copy.db');s.backup(d);d.close();print('copied')"
```

That uses SQLite's own backup, so the copy is consistent even if someone is
using the app. Then leave the machine:

```bash
exit
```

Back on your Mac, fetch the copy while the machine is still awake (`/tmp`
there is wiped when it sleeps):

```bash
fly ssh sftp get /tmp/pa-copy.db /Users/allisonbowman/Developer/pa-prod-copy-2026-10-16.db -a garden-gnome-api
```

That puts it outside the repo on purpose, because it holds testers' names,
emails and garden locations. Tell me it's there and stop. I'll run the
migrations and the claim sync against it, tell you what to expect, and then
we both delete it. If your flyctl refuses `sftp get`, skip the rehearsal and
carry on. If you skipped the copy, just type `exit` to leave the machine.

**Snapshot the volume.**

```bash
fly volumes list -a garden-gnome-api
```

Find the volume named `gnome_data` and copy its ID (it starts `vol_`). Below
it's `VOLUME_ID`.

```bash
fly volumes show VOLUME_ID -a garden-gnome-api
```

Write down what it says about snapshot retention. The new privacy policy says
5 days, which is Fly's default (`fly.toml` sets nothing).

```bash
fly volumes snapshots create VOLUME_ID
```

```bash
fly volumes snapshots list VOLUME_ID
```

Look for a snapshot from right now. If it's still being created, wait and
list again. Write down its ID. Fly's automatic daily snapshot isn't a
substitute: it can be a day old.

**Make the deploy token and store it where CI reads it.**

```bash
fly tokens create deploy -x 999999h -a garden-gnome-api
```

A deploy token can deploy this one app and nothing else. Don't use a personal
auth token. It's printed once: paste it straight into the next command's
prompt, and never into chat or a file.

```bash
gh secret set FLY_API_TOKEN --env production --repo AllisonBowman/Garden-Gnome
```

```bash
gh secret list --env production --repo AllisonBowman/Garden-Gnome
```

Look for `FLY_API_TOKEN` in the list. From now on, every push to master
deploys on its own, docs-only pushes included.

**Deploy by re-running the merge run's failed job.**

```bash
gh run rerun RUN_ID --failed --repo AllisonBowman/Garden-Gnome
```

```bash
gh run watch RUN_ID --repo AllisonBowman/Garden-Gnome
```

Use the run from step 1, not an older master run, because a re-run deploys
the commit its run started from. If anything else has reached master since,
use the newest master run instead.

The Deploy step builds and releases the image. The Smoke check then polls
`GET /` for up to 5 minutes: the first boot runs twelve migrations and the
claim sync before the server answers, and Fly throttles a shared CPU. Look
for `up after N attempt(s)`, then the root JSON with `"synced": true`, then
the `/ai/status` JSON, and a green job. A high N is normal.

**Verify.**

```bash
curl -s https://garden-gnome-api.fly.dev/openapi.json | python3 -c "import json,sys; p=json.load(sys.stdin)['paths']; print(len(p), any(k.startswith('/growing-areas') for k in p))"
```

Look for `34 True` (the three species write routes are hidden now, so 34, not 36). It printed `29 False` tonight.

```bash
curl -s https://garden-gnome-api.fly.dev/
```

Look for a `catalog` block with `"version": "8c520db39b21:6:1"`, `"synced":
true` and `"claims": 10681`, the same as the scratch boot. `species` will be
much higher than the scratch database's 997, because production keeps its
older rows. Write the number down.

```bash
curl -s https://garden-gnome-api.fly.dev/ai/status
```

This should be unchanged: `stub` everywhere, and `"ready": false`.

```bash
curl -s -o /dev/null -w '%{http_code}\n' https://garden-gnome-api.fly.dev/growing-areas/
```

```bash
curl -s -o /dev/null -w '%{http_code}\n' https://garden-gnome-api.fly.dev/census/export
```

Expect `401`, then `404`. Tonight they were the other way round. A 401 means
the route exists and wants a signed-in caller. A 404 on the export means the
operator routes are off.

```bash
fly scale show -a garden-gnome-api
```

Look for 512 MB.

```bash
fly logs -a garden-gnome-api --no-tail
```

That prints what's buffered and exits. Look for these, in order:

- A first upgrade line reading `Running upgrade 0009_aloe_vera -> 0010_claims,
  claims and authorities`. If it starts anywhere else, something was deployed
  by hand in between. That isn't a problem in itself, but tell me.
- One line per migration after it, ending with `Running upgrade
  0021_pending_apple_revocation -> 0022_backfill_acquired_on`. 0022 dates
  every plant that has no acquisition date from the day it was added, so
  plants from 1.1.2 start coming due for their first check.
- `Species catalog already up to date.` (or `Seeded N new species from
  catalog.`, if production lacks a curated species the file has), then
  `curated text refreshed N`. That line is the boot bringing the curated
  care notes, soil types and schedule notes in line with the catalog file:
  the 25 mended dashes, the rewritten safety claims, and any other curated
  text that changed since production was seeded. Expect N above 0 on this
  first boot. I can't predict it, because it depends on how old production's
  rows are, so write it down. It replaces the go-to-market handoff's
  one-off: there is nothing to run by hand. If you see `curated text
  refresh skipped` instead, the boot carried on without it; copy the
  traceback above it for me.
- `claim sync: written`, with `claims stored 10681`, `claims already present
  0`, `genus subjects skipped 4` and `fields refused 0`. Copy the whole block:
  the `species created`, `species linked` and `common-name collisions` counts
  depend on production's rows, and I can't predict them.
- No traceback, no line starting `0017:`, and no `claim sync skipped`.
- The first catalog write also stores two new `sync_state` keys,
  `catalog_generation` and `synced_through_species_id`; nothing to do, just
  don't be surprised to see them.

If the boot happened too long ago for the buffer, the smoke check's output in
the run log has the root JSON, which is the part that matters most. On every
later cold start you'll see `Species catalog already up to date.`, `curated
text refreshed 0` and `claim sync: tranche unchanged, nothing to do`. All
three are normal. A later deploy that edits a curated note shows a small N
once, then 0 again. The new text reaches phones on their next catalog fetch,
with no restart, because the refresh stamps a new catalog generation; step 5
has you read it on a phone.

**If the logs show a migration failing, the snapshot is the way back.** It's
not the usual rollback. Redeploying the previous image is safe only for
additive migrations, and the old code can't read a database 0017 has
renamed. flyctl 0.4.76 has no one-step restore. `fly volumes create
--snapshot-id` makes a new volume from the snapshot, and the machine then has
to be moved onto it. That sequence is untested and destructive, so it isn't
scripted here: stop, keep the log, and bring it to me with the snapshot ID.
Restoring costs everything written since the snapshot.

**The screenshot garden** is needed only if you retake a screenshot (step 4
says they already exist). If you do, start it now: it needs care logged one
and two days before the shoot, and it has to be built against this new
backend.

## D1. Between steps 2 and 3: export the July waitlist

Step 3's deploy drops the `/api/waitlist` endpoint. The addresses stay in
Cloudflare's KV or D1 store, but get them out first, so the count is known
before anything leans on it (decision 9). It takes about half an hour.
`docs/go-to-market/launch-kit/waitlist-email.md`, "Before step 3: get the
list out of Cloudflare", has every command, one per block, in this order:

1. Make a private folder outside the repository,
   `$HOME/PlantAdvocate-private`, not in a folder that syncs to iCloud.
2. Sign in with `npx wrangler login` (the same sign-in step 3 starts with),
   find the project whose domains include plantadvocate.ai, and look in its
   production bindings for a KV namespace or a D1 database.
3. Read what the July form promised. The best copy is the homepage in commit
   `25f370f`: "Just an update when the beta opens." Compare it with a July
   deployment if Cloudflare's history can still open one.
4. Export the store into the private folder, and run the check, which
   prints counts and endings but no address, and writes `send-list.txt`,
   `set-aside.txt` and `check-by-eye.txt`.
5. Make the two empty files the removals and the spring note need,
   `removed-hashes.txt` and `later-releases.txt`.

Don't paste the export or any address from it into a Claude session, an
issue or a doc, and don't delete anything in Cloudflare yet. If the project
has no KV or D1 binding at all, stop and tell me before step 3. If step 3
then slips by more than a week or two, export once more just before it. The
check's output is safe to show me once you've looked at its one sample line,
as that file says.

## D2. Step 3: Deploy the website to Cloudflare

The live site isn't the repo's `site/` folder. On 16 October it was the July
17 build from the desktop generator, which says the app doesn't collect
precise location and describes subscriptions. By 23 October someone had
deployed the October 16 rewrite of `site/` over it, and on 30 October it
still served that: a privacy policy dated October 16, which lacks the
October 20 text on census export 4.1 and the 30-day Apple grant, and a
homepage that says "EVERY FACT CITED". So this step is a redeploy, for the
newer text and the 2026-10-30 site fixes. `site/README-SITE.md` has the full
reasoning. These are its commands, in order. Export the waitlist first
(above). Deploying doesn't delete the addresses, but it removes the
endpoint.

```bash
cd /Users/allisonbowman/Developer/Garden-Gnome
```

```bash
git status --short
```

This must print nothing.

```bash
git log -1 --format='%h %d'
```

It should name `care-advice-honesty` and the commit EAS reports at the top of
this file, or a later one, because the deploy copies the `site/` folder this
checkout holds. If it's older, run `git pull --ff-only` and look again. Then:

```bash
npx wrangler login
```

That opens a browser. If npx asks to install wrangler, answer `y`.

```bash
npx wrangler pages project list
```

Find the project whose domains include `plantadvocate.ai`. Below it's
`PROJECT`.

```bash
npx wrangler pages deployment list --project-name=PROJECT
```

Find the deployment whose Environment is Production and note its Branch
(often `main`). Below it's `PRODUCTION_BRANCH`.

Check the links. This must end `13 pages, 0 broken`. It did on `b6fee6b` on
2026-10-30, before that day's site fixes, so run it on the tip you deploy:

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

Deploy. This copies the pages to a temporary folder without the README, so
the README isn't published:

```bash
D=$(mktemp -d) && cp -R site/. "$D" && rm "$D/README-SITE.md" && npx wrangler pages deploy "$D" --project-name=PROJECT --branch=PRODUCTION_BRANCH
```

`--branch` is required. Without it, wrangler takes the branch from git
(`care-advice-honesty`) and publishes a preview, not plantadvocate.ai.

Verify. The check block lives in `site/README-SITE.md`, under "Verifying the
deploy", and the 2026-10-30 site fixes added lines to it, so print it from
the checkout you deployed rather than copying an older list:

```bash
sed -n '/^## Verifying the deploy/,/^## When the app changes/p' site/README-SITE.md
```

Run the block it prints, from the `check()` line to the last `check` line.
Every line must print `ok`. On 2026-10-23, against the October 16 pages then
live, four lines of the older block printed FAIL, among them the October 20
date and "EVERY FACT CITED".

```bash
curl -s -o /dev/null -w '%{http_code} %{url_effective}\n' -L https://plantadvocate.ai/privacy.html
```

```bash
curl -s -o /dev/null -w '%{http_code} %{url_effective}\n' -L https://plantadvocate.ai/support.html
```

Both should print `200`, landing on `/privacy` and `/support`. Last, open
https://plantadvocate.ai/privacy on your phone and read the top: the October
20 date and the "What changed" line should both be there. (This said October
16 until 2026-10-30; `site/privacy.html` has said October 20 since that
day's text was written.)

## E1. Step 4: App Store Connect

**First, send the build up.** This can happen any time after the build
finishes, even before step 2, and doing it early shortens 1.1.2's broken
window.

Only an EAS build goes up. iOS 27 crashes an Expo SDK 57 app at launch when
it is built with the iOS 27 SDK, unless the app adopts the scene life cycle,
which 1.1.3 doesn't. The EAS production profile builds with the image
`macos-tahoe-26.5-xcode-26.6` (`mobile/eas.json`), which links the iOS 26.5
SDK, so Apple's rule doesn't touch it. Don't change that image for 1.1.3, and
never upload a 1.1.3 built on this Mac, whose only Xcode is 27.1
(`docs/2026-10-24-ios27-scene-lifecycle.md`). From April 2027 every upload
needs the iOS 27 SDK, which is why the scene-adopted 1.1.4 has to follow.

```bash
cd /Users/allisonbowman/Developer/Garden-Gnome/mobile
```

```bash
npx --yes eas-cli@latest whoami
```

Look for `allisonbowman`.

```bash
npx --yes eas-cli@latest build:view EAS_BUILD_ID
```

Use the EAS build ID from the top of this file. Look for status finished,
version 1.1.3, the build number from the top of this file, and the commit
listed there.

```bash
npx --yes eas-cli@latest submit --platform ios --profile production --id EAS_BUILD_ID
```

It will ask you to sign in to your Apple account (Team `FK6E9XBY6Y`). The App
Store Connect app ID, 6792203800, is already in `eas.json`. Look for a
message that the build was submitted. Apple then processes it, usually
within half an hour, and emails you when it's done. If it isn't asked about
encryption, that's right: `ITSAppUsesNonExemptEncryption` is false in
`app.json`. Watch that email, and any later one from Apple, for privacy
manifest warnings (codes starting `ITMS-91`), and send me any you get.
`app-privacy.md` suggests Xcode's Generate Privacy Report, but that needs a
local archive, which an EAS build doesn't leave, so Apple's email is the
check we have.

When it has processed, open App Store Connect > PlantAdvocate > TestFlight,
open build 1.1.3 with **the build number from the top of this file**, and
paste the "What's New" block from `docs/app-store/listing.md` into its What
to Test. Pick builds by build number, never by the version string.

**Then the paperwork.** Everything is in `docs/app-store/`, ready to paste
field by field, in the order its `README.md` gives. They were brought up
to `307930e` and the 2026-10-20 fixes, and on 2026-10-30 to that day's
changes, so nothing in them asks you to cut a line any more: every change
they describe is in the build, as long as step 5 agrees. The changes that
matter are the hazard and edibility wording with the not-advice line under
each hazard note, the operator-only census (export 4.1) with no Sync now
button, iPhone only, the three named weather services and the manifest.

1. **App Information** (`listing.md`, `age-rating.md`): name
   `PlantAdvocate: Garden Care`, or `PlantAdvocate` if that name is taken;
   subtitle (decision 10: the strategy's `Plants that suit each spot`, or
   listing.md's); Lifestyle first, Reference second; content rights Yes and
   Yes. Age rating: answer every question as `age-rating.md` does, and the
   result should be 4+. Copyright: `2026 Allison Bowman`, exactly as the
   legal name on your developer account reads (App Store Connect >
   Business, or the Membership page).
2. **Pricing and Availability:** Free, in the territories you chose in
   decision 11 (recommended: the United States only), with no pre-order.
   On the same page, under Apple Silicon Mac Availability and Apple Vision
   Pro Availability, untick "Make this app available" and save: App Store
   Connect offers an iPhone app on both unless you do, nothing has been
   tested on either, and the listing and the press page say iPhone only
   (found by the 2026-10-31 review).
3. **App Privacy** (`app-privacy.md`): Privacy Policy URL
   `https://plantadvocate.ai/privacy` (the app's `/privacy.html` is the same
   page). Then "Do you or your third-party partners collect data?" Yes, and
   these seven types, every one linked to the user and none used for
   tracking:
   - Contact Info > Name: App Functionality
   - Contact Info > Email Address: App Functionality
   - Identifiers > User ID: App Functionality
   - Location > Precise Location: App Functionality
   - Location > Coarse Location: App Functionality and Analytics
   - User Content > Customer Support: App Functionality
   - User Content > Other User Content: App Functionality and Analytics

   Not Photos, not Audio, nothing under Usage Data or Diagnostics. The two
   Analytics ticks are decision 8: confirm them. Publish. The label should
   read "Data Linked to You: Contact Info, Identifiers, Location, User
   Content", with nothing used to track you.
4. **The 1.1.3 version page:**
   - Screenshots (below).
   - Promotional text and description from `listing.md`, and the keywords
     that go with the subtitle you chose in decision 10 (field A in
     `docs/go-to-market/launch-kit/listing-proposals.md` for the strategy's
     subtitle, or listing.md's field for listing.md's).
   - Support URL `https://plantadvocate.ai/support`, Marketing URL
     `https://plantadvocate.ai`, and copyright.
   - Under Build, choose 1.1.3 with **the build number from the top of this
     file**.
   - App Review Information from `review-notes.md`: tick Sign-in required
     (decision 7). Contact: Allison Bowman, a phone number you'll answer
     during review, in international format with a plus sign (`+1` and the
     10 digits for a US number), and an email you read daily, such as
     support@plantadvocate.ai.
   - Paste the Notes block as it is. Fill in its two brackets first: the
     phone you ran the TestFlight build on in step 5, or delete that
     bracket, and the phone number. It is 3,881 of Apple's 4,000 bytes,
     3,914 if the form sends each line break as two bytes, counted on
     2026-10-30 with the brackets in place, so paste it exactly, with
     nothing added at either end.
   - Under Version Release, recommend **Manually release this version**, so
     you can update the site's "in beta" copy before the app appears. Don't
     use pre-order.
5. **Export compliance:** only if asked (`export-compliance.md`).

**Screenshots.** They exist. `docs/screenshots/1.1.3/` holds 16: 8 in
`17-pro-max/` (1320 x 2868, the iPhone 6.9" size) and 8 in `17-pro/` (1206 x
2622, the 6.3" size), shot on iOS 26.5 simulators from `3f6d7da`, with
seven retaken on 2026-10-24 after the °F fix. `CHECK.md` reports all 16
passing. Upload each folder to its size in the order the strategy
recommends, which is not file order: 01, 04, 06, then 02, 03, 05, 07, 08. The
first three are what a searcher sees in the results list: what doesn't suit
a spot, checks not chores, and hazards on Pothos
(`docs/go-to-market/strategy.md`, step zero). Shot 6 is Pothos, not Dumb
Cane: Dumb Cane's care notes still showed garbled dashes on the shoot's
backend, and the shot list allows Pothos. Three of them, 03, 05 and 06,
predate the 2026-10-30 changes to the hazard wording, the not-advice line
and the Report a fact link; decision 12 leaves them as they are unless you
say otherwise. If CHECK.md says otherwise on the day you upload, follow
CHECK.md.

`docs/app-store/screenshots.md` still has the demo garden, the shots' set-ups
and the simulator commands, for any retake. Two notes if you retake one:

- On shot 2 (Good candidates), read every visible name. Lily of the valley
  can appear (decision 6); scroll it out of frame. If monkshood, English
  yew, foxglove, jimsonweed, mayapple, taro or wisteria is in frame, the
  candidate rule isn't in the build: don't shoot it, and tell me.
- `screenshots.md`'s two-day plan already counts on a new plant being dated
  the day it's added (`7dac70d`), and gives the same two checks. Follow it
  as written.

A phone works instead of the simulator if it has a Dynamic Island. An iPhone
15 Pro saves 1179 x 2556, which is accepted for the required medium size;
`screenshots.md` lists the sizes. The `sips` check in that file tells you
what you've got. Phone shots come from the real TestFlight build, which is a
point in their favour. Keep Settings out of every shot.

## E2. Step 5: TestFlight on a phone

Delete PlantAdvocate from the phone first, so every permission prompt shows
fresh. Your garden lives on the server and comes back when you sign in. Then
in TestFlight, install 1.1.3 with **the build number from the top of this
file**. Write down the phone's model and iOS version (Settings > General >
About), and whether Apple Intelligence is on. If the phone runs iOS 27, the
build launching at all is the first time 1.1.3 has started on iOS 27; name
the phone in the Notes' TESTED ON bracket (`docs/app-store/review-notes.md`).

Go through these and note what you see for each:

1. **Login screen.** Above the buttons: "Signing in creates your account, so
   your plants, care log and growing areas follow you to a new phone." Tap
   Sign in with Apple. As Apple's sheet closes and the app talks to the
   server, the Apple button should dim, show a spinner, and ignore a second
   tap.
2. **Permission prompts, word for word.**
   - New growing area > Use my location: "PlantAdvocate uses your location
     to set a growing area's place, so it can fetch that area's local
     forecast." There should be no "Always" choice.
   - Walk the garden, then the microphone icon: the microphone prompt reads
     "On Walk the garden, PlantAdvocate listens while you say what's planted,
     so you can add plants without typing. PlantAdvocate never receives or
     keeps the sound." The speech prompt reads "On Walk the garden,
     PlantAdvocate turns what you say into a list of plants. Your phone does
     this itself where it can, and Apple does it otherwise. PlantAdvocate
     only receives the plants you confirm."
   - Camera, whenever it's first asked: "PlantAdvocate uses the camera to
     photograph a plant. Your phone can suggest what it is, and when photo
     check-ups are offered you can send the photo for one. On Walk the garden
     the camera shows your garden behind your list. That view isn't recorded
     or sent anywhere."
   - Photos, if it's asked at all: "PlantAdvocate lets you choose a photo of
     a plant. Your phone can suggest what it is, and when photo check-ups are
     offered you can send the photo for one."
   - There should be no Face ID prompt anywhere.
3. **Census tab.** It opens against production and shows your summary, or
   plain empty states. There's no Sync now card and no error.
4. **A plant comes due without logged care.** During the day, add Basil (water
   every 1 to 2 days) to any area and log nothing. (The server dates a new
   plant by the UTC calendar, so one added late on a US evening can be dated
   tomorrow and come due a day later.) By tomorrow, the Plants tab's "Checks
   for today" card should list it, with Watered and Still damp. Before
   `7dac70d` it never came due. It must not be listed the same day you add it:
   west of Greenwich it used to be, because the app read the date as midnight
   UTC. A plant whose species has no check schedule should be named on that
   card as left out, and "All caught up" shouldn't appear while one is.
5. **Hazard sentences.** In the Species tab, search each of these. Nothing
   anywhere should say "You can eat". Three rules hold on every hazard
   sentence since the 2026-10-20 fixes: a severity word ("Seriously",
   "Mildly") comes from NC State's rating of harm to people, so it belongs to
   people only; animals are "toxic to pets", or to cats or dogs, unless the
   plant's own table or a source's grave wording about animals says more; and
   a food crop leads with the part that's eaten. Since 2026-10-30 three more
   hold: where people are named, the Poison Control line adds "or your local
   poison centre" (", your local poison centre or a vet" when pets are named
   too); a pet verdict a source settled says whose it is, such as "For
   pets, the source is NC State Extension."; and words from the code's own
   tables follow as "PlantAdvocate's own summary: ...", which on Pothos is
   the calcium oxalate wording. I'll give you the exact
   sentences from a scratch database built from the commit EAS reports, to
   compare word for word.
   - Pothos: toxic to cats, dogs and people, all parts (calcium oxalate
     crystals), "NC State Extension rates it medium severity", keep it out of
     reach, and the Poison Control line (US 1-800-222-1222). No severity
     word: medium has none.
   - Foxglove: a warning sign, seriously toxic to people, NC State's high
     rating and the Poison Control line. Pets are named as toxic; "seriously"
     reaches them only if a source's animal wording is grave.
   - Dumb Cane: a warning sign, "Seriously" for people, all parts (calcium
     oxalate crystals), "NC State Extension rates it high severity", and the
     Poison Control line. Cats and dogs get "seriously" only if the record's
     own animal wording is grave.
   - Potatoes: a warning sign, then a sentence that leads with the crop,
     like "The tubers are the crop; the leaves, stems and sprouts are
     seriously toxic to people and pets." (the potato's own table is what
     lets "seriously" cover pets), NC State's high rating, and a
     warning-coloured **Eating** row that sends you to the source before
     eating any of it.
   - Tomatoes: leads with the ripe fruit as the crop, then the leaves and
     stems. Nothing should read as if the fruit were poisonous. Its Eating
     row sends you to the source before eating any of it.

   If a search shows two rows with the same name, the one with a Sources
   card is the researched one. Tell me about the duplicate.

   Under each of those sentences there should be one line, word for word: "These notes repeat what the sources publish. They are
   not medical or veterinary advice." (2026-10-30). Look for it on Pothos's
   species page, in a plant's Care guide card, and in Add plant once you
   pick a species. At the foot of Pothos's Sources card, tap Report a fact:
   Mail should open a message to support@plantadvocate.ai naming Pothos and
   listing what the page shows. Don't send it. If the line or the link is
   missing, the build predates that day's changes: tell me before step 6,
   because the listing and the Notes now say the line is there.

   While you're in the Species tab, read the care notes too, which come
   from the server since step 2's deploy. Catnip, Parsley, Nasturtium,
   Gourds, Spider Plant and Boston Fern should say nothing about being
   pet-safe, harmless or safe for most pets; Sage, Thyme, Baby's Breath,
   Hollyhock, China Aster and Moonflower should say nothing about being
   toxic. Dumb Cane and Boston Fern should read cleanly, with real dashes
   and no "â€". Snake Plant's temperature should read "60–85°F", with a
   capital F.
6. **The Almanac.** Species tab > "What suits one of your spaces" > the
   Almanac. The list runs A to Z. Only gradable species carry a grade, and a
   line says how many "have nothing to grade yet and aren't in any grade".
   Picking a grade leaves those out. A hybrid is found whether you type x or
   ×.
7. **Candidates carry hazard lines.** Make an outdoor, full-sun area and look
   at Good candidates here. Any candidate with a recorded hazard shows a
   warning line, such as "Toxic to pets." or "Toxic to cats, dogs and
   people." Poison hemlock, belladonna, castor bean, poison ivy, mayapple,
   taro, wisteria, foxglove, English yew, monkshood and jimsonweed should
   never appear, whatever the area's goals. Potato, eggplant, peanut,
   tomatillo or butter bean may appear with their line: a food crop eaten
   without conditions stays a candidate. Lily of the valley may appear too
   (decision 6). Note any of the never-list you see.
8. **Hidden features stay hidden.** A plant's page has no photo check-up card
   and no box for typing symptoms. Ask the Gnome offers Get care advice.
   Settings > Privacy & data has no entry about photos or advice going to an
   outside service, and its location entry names Apple Weather, the U.S.
   National Weather Service and Open-Meteo.
9. **Settings shows 1.1.3.**
10. **Photo identification.** On an iPhone 15 Pro or newer, on iOS 26, with
    Apple Intelligence on, Add plant shows Take photo and Choose photo. The
    results say "Suggested from the photo. Tap the one that matches, and
    check it's right before you save." and nothing is pre-selected. On an
    older phone those buttons are absent, and that's the correct result, not
    a failure. Say which you saw. The same Apple Intelligence phones restyle
    the Gnome's advice: on Pothos, Get care advice should end with the
    toxicity warning word for word, before the sign-off.
11. **iPad**, if you have one: the app installs and runs in an iPhone-shaped
    window, with no iPad layout.
12. **Optional: deletion and Apple's revoke.** Only on an account whose
    garden you don't need, such as a second Apple ID on the simulator, never
    your own. Settings > Account > Delete account > Delete forever. Then, in
    that Apple ID's settings under Sign in with Apple, PlantAdvocate should
    disappear. `fly logs -a garden-gnome-api --no-tail` shouldn't show a
    revoke error.

If any sentence, label or prompt reads wrong, that can change what gets
pasted in step 4. Nothing is submitted until step 6, so tell me before going
on.

## E3. Step 6: Submit for review

Wake the server, so the reviewer's first request doesn't wait out a cold
start:

```bash
curl -s --max-time 30 https://garden-gnome-api.fly.dev/
```

Look for the catalog block with `"synced": true`. Then, in App Store Connect,
on the 1.1.3 version page: check that the build shows **the build number from
the top of this file**, then Add for Review, then Submit for Review. The
status should change to Waiting for Review.

After approval, three follow-ups: revert `min_machines_running` if decision 1
was yes; change the site's "in beta" and early-access copy to the App Store
link; and release the version, if you chose a manual release.
`docs/go-to-market/launch-day-runbook.md` takes it from approval day: when to
merge `claude/launch-day-site` (the morning you release, once it has been
reviewed), when to deploy the site, the waitlist email and the first week.
It suggests keeping the machine awake until a week after release.

If App Review rejects instead, the prepared replies are in
`docs/app-store/review-replies.md`, each with what to check before you paste
it.

---

## When the outcome isn't obvious

| Step | What you see | What it means | What next |
|---|---|---|---|
| 1 | Deploy to Fly is red on the merge run with `no access token available` | Expected. The secret doesn't exist yet, and nothing was deployed | Carry on with step 2 |
| 2 | The orphan check prints a list instead of `[]` | Rows point at missing areas, and 0017 would refuse at boot, leaving the API down | Don't deploy. Bring me the output |
| 2 | Re-run fails at Deploy with `no access token available` again | The secret isn't where the job reads it | `gh secret list --env production ...` and check the name and environment letter by letter. Nothing was deployed |
| 2 | Deploy fails while building the image (Docker or pip) | Nothing was released, so production is still the old code (the openapi check prints `29 False`) | Bring me the whole Deploy log. Don't patch anything live |
| 2 | Smoke check ends with `never returned 200 in 5 minutes` | The new machine isn't up, or is still migrating | `fly logs -a garden-gnome-api --no-tail`, and look for a traceback or a line starting `0017:`. Read the log before restoring anything |
| 2 | Smoke check says `The API is up but is not serving the catalog this build ships` | Migrations ran, but the claim sync was skipped or failed. The API serves the old care data | Find `claim sync skipped` and the traceback above it in the logs. No rollback needed. Bring it to me |
| 2 | Logs show `0017: N row(s) point at a missing environment ... Nothing was changed: the database is still at 0016` | 0017 refused cleanly. The API stays down until the rows are fixed | Stop and bring me the log and the snapshot ID. Don't hand-edit rows |
| 2 | Verify prints `29 False` after a green deploy | The old machine is still answering, or the release didn't take | `fly status -a garden-gnome-api` and `fly releases -a garden-gnome-api`. Bring both |
| 2 | `curl` returns nothing or HTTP 000 minutes later | The machine is asleep (`auto_stop`), which isn't broken | Run the curl again and wait for the cold start |
| 2 | Logs show `curated text refresh skipped` after a traceback | The boot carried on, but production kept its old care notes, garbled dashes and safety claims included | Copy the traceback for me. No rollback; the fix is a deploy |
| 2 | `curated text refreshed 0` on this first boot | Production's curated rows already matched the file, or the refresh found none of them as curated rows | Tell me. Step 5's care-note checks will show which |
| 3 | Some check lines still say FAIL after the deploy | Either the deploy went to a preview (a wrong or missing `--branch`), or Cloudflare served a cached page | `npx wrangler pages deployment list --project-name=PROJECT` and look at the newest Environment. If it's Production, wait a minute and re-run the checks |
| 4 | `eas submit` fails on Apple sign-in or credentials | Your Apple session, not the app | Run it again, let EAS walk you through sign-in, and send me the error text if it fails twice |
| 4 | App Store Connect asks the encryption questions | The plist key didn't reach the build | Answer as `export-compliance.md` says, and tell me it asked |
| 4 | Still "Processing" after two hours | Usually an Info.plist or asset check on Apple's side | Check your email, then developer.apple.com/system-status, before assuming it's ours |
| 5 | No Take photo button on a phone older than the 15 Pro, or with Apple Intelligence off | Correct. Photo identification needs Apple Intelligence | Note the phone. Search still works |
| 5 | Census tab shows an error card | Production isn't on the new backend, or it was asleep | Try again once. If it persists, re-run step 2's openapi check |
| 5 | Lily of the valley appears as a candidate | Expected (decision 6) | Keep it out of screenshots |
| 5 | Foxglove, English yew, monkshood, jimsonweed, mayapple, taro or wisteria appears as a candidate | The candidate rule from the 2026-10-20 fixes isn't in this build | Note which and the build number, keep it out of screenshots, and tell me |
| 5 | No "These notes repeat what the sources publish..." line under a hazard sentence | The build predates the 2026-10-30 changes | Don't submit it. Tell me the build number and the commit EAS reported |
| 5 | A care note still says "Pet-safe", or shows "â€" | Production's rows weren't refreshed (step 2's `curated text` line) | Bring me that log line. The fix is data and a deploy, not a build |

## What to report back

Roughly in the order that changes what happens next:

1. Your answers to the twelve decisions at the top. A one-word "yes" or
   "no" per item is plenty; for decision 10, which subtitle.
2. Whether PR #22 merged, and the RUN_ID.
3. The `fly secrets list` names, the orphan check's output, the snapshot ID,
   and the retention line from `fly volumes show`.
4. Whether you made the database copy, and its path.
5. How Deploy and Smoke check ended. The openapi line, the `GET /` JSON, the
   two status codes, and `fly scale show`'s memory. The `fly logs` lines from
   the first `Running upgrade` through the end of the claim sync block, the
   `curated text refreshed N` line among them, or the traceback.
6. Whether the waitlist export found a KV or D1 store, and what its check
   printed. Then whether every site check printed `ok`, and the project and
   production branch names.
7. That `eas submit` went through, the build number App Store Connect shows,
   and any `ITMS-91` email.
8. The phone's model, iOS version and Apple Intelligence state, then each of
   step 5's twelve items: as written, or what you saw instead. Screenshots of
   anything that reads wrong help most.
9. That the screenshots uploaded at both sizes, in the order 01, 04, 06,
   02, 03, 05, 07, 08, and which subtitle and keywords you pasted.
10. The App Store Connect status after you submit, and anything App Review
    sends.
11. Whether 1.1.2's Species tab and Census misbehaved in the window, if
    anyone was still on it.

## What this build has NOT proven

Nothing on the ship branch has run on a device yet. The mobile tests, the
typecheck and the leak scan check logic and copy. They can't show the new
Info.plist strings, the privacy manifest, iPhone-only on an iPad, the sign-in
button's busy state, the error boundaries, the not-advice line's place under
each hazard note, or the restyled Gnome voice. Only step 5 shows those. For iOS
27 the only evidence is an earlier PlantAdvocate build, made with the same
Xcode 26.6 and iOS 26.5 SDK as the EAS image, which launched on an iOS 27.0
simulator (`docs/2026-10-24-ios27-scene-lifecycle.md`).

The backend deploy is untested in production. CI has never deployed this
app. The 512 MB VM, the smoke check's `catalog.synced` test, the 5-minute
budget and twelve migrations at once have run only against scratch databases
on this Mac, never against Fly's throttled CPU or production's file.

The 0017 pre-check has run only on scratch data. It refuses cleanly in tests,
and the one-liner printed `[]` on a scratch database at 0009. Neither says
anything about production's rows. The orphan check, and the rehearsal if you
do it, are the first time real data meets it.

The claim sync has never met production's ~1,900 older species rows. Its
linking, collision and `species created` numbers on production are unknown
until the logs show them.

The curated-text refresh has run only in tests and on scratch databases. Its
count on production, and whether it finds all 129 curated rows there, are
unknown until step 2's logs show `curated text refreshed N`.

The site deploy from these commands is untested. By 23 October someone had
put `site/`'s October 16 rewrite live, but nothing in the repository says
how. Whether `wrangler pages deploy` with `--branch` lands on
plantadvocate.ai, and what dropping `/api/waitlist` breaks, is known only
from Cloudflare's documented behaviour.

App Review has never seen PlantAdvocate. The Sign-in required answer, the 4+
rating with its hazard notes, and a login wall with no demo account are all
judgement calls. Only the review itself settles them.
