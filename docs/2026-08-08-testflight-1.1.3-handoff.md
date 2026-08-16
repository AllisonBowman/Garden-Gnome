# TestFlight 1.1.3 — what only you can do

> Everything in this file needs your GitHub merge permission, your Fly
> credentials, your EAS login, or a phone in your hand. Nothing here can be
> done from a dev machine — that's why this exists instead of "now go ship
> it."

**State at time of writing:** `care-advice-honesty` tip is `ef0afbe` ("Bump to
1.1.3 for the check-verb TestFlight build"), pushed to origin, sitting on open
PR #19 into `master`. CI on that exact commit is green — Backend tests and
Mobile typecheck and tests both `SUCCESS` — and the PR reports
`mergeable: true`, `mergeStateStatus: CLEAN`. `git status` here is clean, the
leak scan is clean, and `bash .claude/bin/build-precheck.sh production` says
**clear to build** on `ef0afbe` (two informational warnings only — old Android
package name, and the standard TestFlight build-number reminder).

## Why this matters

PR #19 is the whole of Phase 1: the water reminder becomes a check with
"Watered" / "Still damp" outcomes, the repot reminder becomes a February-only
inspection with three outcomes, fabricated humidity is suppressed everywhere
including a real leak where the traits card was showing users raw pipeline
provenance text, and the shade-genera light values get corrected by a data
migration. None of that has ever run outside `jest`/`tsc`/`pytest` — the
schedule-window math, the outcome buttons, the February gate, all of it is
verified by test assertions against a fake clock, not by a person tapping the
app. The February inspection flow in particular **cannot** be verified live
right now under any circumstances, real or simulated — it's August, so the
honest and correct thing for a real device to show this month is *no* repot
task at all. That's not a gap in this handoff; it's a gap that won't close
until next February. Separately: an earlier attempt to merge PR #19 reportedly
did not land, and nothing in the PR's state explains why — no branch
protection rule exists on `master`, no review is required, and the checks were
already green when I looked. Worth a clean second attempt before assuming
anything changed.

**One drift found and already fixed while preparing this:**
`mobile/src/support.ts` hardcoded `APP_VERSION = '1.1.2'` separately from
`mobile/app.json`'s `version` — it labels Settings and every support-email
subject, so 1.1.3 would have misreported itself as 1.1.2 to support tickets
and testers. It is bumped to `'1.1.3'` in this branch (nothing catches the
drift automatically — a background-task chip exists to derive it from the app
config and add a CI guard, so this is the last hand-bump).

---

## Step 1 — Merge PR #19

Open <https://github.com/AllisonBowman/Garden-Gnome/pull/19>.

Confirm before clicking:
- Checks show green: **Backend tests**, **Mobile typecheck and tests**.
- The merge box says "This branch has no conflicts with the base branch."

Click **Merge pull request** (not Squash, not Rebase — every prior PR on this
repo, #8 through #18, merged this way, and a real merge commit is what the
handoff doc format below expects you to look for). Confirm the merge.

If you'd rather do it from a terminal instead of the browser:

```powershell
gh pr merge 19 --merge --repo AllisonBowman/Garden-Gnome
```

**Verify it actually landed:**

```powershell
Set-Location C:\Users\14439\Garden-Gnome
git fetch origin
git log origin/master --oneline -3
```

**Look for:** a new top commit reading `Merge pull request #19 from
AllisonBowman/care-advice-honesty`, with `ef0afbe` reachable underneath it.
Write down the merge commit hash — call it `$HEAD`. Steps 2 and 3 both check
against it.

If the Merge button is greyed out or the click silently does nothing again:
refresh the PR page first (stale state is the most boring explanation and
matches everything the API shows right now), then check
Settings → Branches for a protection rule that wasn't there when I checked,
then check whether someone force-pushed `master` out from under the PR since
`ef0afbe` was written. In that order.

---

## Step 2 — Deploy the backend to Fly

**This will trigger CI, and the Deploy job in it is expected to fail —
that's old news, not something this merge broke.** No `FLY_API_TOKEN` repo
secret has ever been created (confirmed via the GitHub API: zero repository
secrets exist), so every push to `master` runs backend + mobile tests
successfully and then the `Deploy to Fly` job fails for lack of credentials —
that's been true of every push to master checked, not just this one. Expect
to see two green checks and one red one on the merge commit in
<https://github.com/AllisonBowman/Garden-Gnome/actions>. Deploying is still a
manual, human step, exactly as `docs/deploys.md`'s opening banner says.

Production is currently on **v31**, deployed Aug 1 — before every migration in
this PR. This deploy carries four: `0007` (shade-genera light fix), `0008`
(adds `care_log.outcome`), `0009` (Aloe vera rename, guarded), and `0010`
(adds the `authority` and `claim` tables). All four are additive; none drop a
column or delete rows outright. They run automatically at container boot,
before `uvicorn` binds.

`0010` landed after this document was first written. It creates two empty
tables and touches nothing existing, so it changes nothing you will see in the
app — but it is in the chain, so a deploy that stops at `0009` is now behind.

```powershell
Set-Location C:\Users\14439\Garden-Gnome
git checkout master
git pull
git status
git log --oneline -3
```

**Look for:** working tree clean, and the same merge commit / `$HEAD` from
Step 1 at the top of the log. `fly deploy` builds the working directory, not
git — a dirty tree here is exactly how production ran an unversioned build for
four days in July (`docs/pre-deploy-checklist.md` has the full story). If this
isn't clean, stop and find out why before deploying.

**Back up the volume first** — the one part of this that can't be undone if
something goes wrong:

```powershell
Set-Location C:\Users\14439\Garden-Gnome\garden-gnome
fly ssh sftp get /data/garden_gnome.db backup-1.1.3-predeploy.db -a garden-gnome-api
```

**Look for:** a file with a real, non-zero size next to it.

**Deploy:**

```powershell
fly deploy -a garden-gnome-api
```

Watch it boot. A `WARNING The app is not listening on the expected address`
line during the first minute or so is normal (the window before `uvicorn`
binds), not a crash — see the "two things that look broken and aren't"
section of `docs/pre-deploy-checklist.md` if you want the full explanation.

**Confirm it landed:**

```powershell
fly releases -a garden-gnome-api
curl -s https://garden-gnome-api.fly.dev/ | python3 -m json.tool
```

**Look for:** a new release above v31, marked `complete`, and `/` answering
`{"status": "ok", ...}` with HTTP 200. If it never answers, a broken migration
is the first thing to suspect — check `fly logs -a garden-gnome-api` for a
boot loop rather than assuming the deploy itself failed.

**Known, unrelated issue you'll still see:** environment weather still returns
Apple's `401 NOT_ENABLED` for WeatherKit — that's an Apple-side provisioning
fault, fully diagnosed and not something this deploy touches or fixes. Full
account and the drafted support ticket are in
`docs/2026-07-30-weatherkit-401-closed.md`. The app falls back to the National
Weather Service automatically, so weather still works for users; this is only
relevant if you go looking for why WeatherKit specifically still fails.

---

## Step 3 — Build and submit, on the Windows box

Device builds need `eas-cli`, which lives on the Windows box, not this Mac.
All commands below are PowerShell, run from `C:\Users\14439\Garden-Gnome`.
PowerShell 5.1 has no `&&` — chain with `;` if you want one line.

**1. Pull and confirm you're building what you think you're building:**

```powershell
Set-Location C:\Users\14439\Garden-Gnome
git checkout master
git pull
git log --oneline -1
```

**Look for:** the same `$HEAD` merge commit you wrote down in Step 1. If it's
not there, the pull didn't land or you're not on `master` — stop and find out
which before building.

**2. Confirm the working tree is clean:**

```powershell
git status
```

**Look for:** `nothing to commit, working tree clean`. EAS builds committed
state only; anything uncommitted here is silently excluded and produces a
build that looks right but isn't.

**3. Confirm the EAS session and registered devices:**

```powershell
Set-Location C:\Users\14439\Garden-Gnome\mobile
eas whoami
eas device:list --apple-team-id FK6E9XBY6Y
```

**Look for:** `allisonbowman`, matching `owner` in `app.json`. Apple team is
`FK6E9XBY6Y`. If a phone you want to test on isn't listed and you also want an
ad-hoc/dev build later, register it now (`eas device:create
--apple-team-id FK6E9XBY6Y`) — a device added after a build won't be able to
install it. Not required for TestFlight itself; App Store Connect handles
device authorization differently.

**4. Sanity-check the production build profile:**

```powershell
eas config --platform ios --profile production --non-interactive
```

**Look for:** `"image": "macos-tahoe-26.5-xcode-26.6"` (the on-device
Foundation Models module needs the Xcode 26 SDK; a different image can
silently strip the feature) and `"autoIncrement": true`.

**5. Build:**

```powershell
eas build --profile production --platform ios
```

Run it in your own terminal — it may prompt about credentials; "yes, let EAS
manage it" is correct. Runs on Expo's macOS fleet, ~15–30 minutes. Don't touch
the working tree while it runs.

**6. Confirm the finished build came from the right commit:**

```powershell
eas build:list --platform ios --limit 1
```

**Look for:** the `Commit` field matching `$HEAD` exactly. If it doesn't, this
build was stale — stop, work out why, and rebuild before submitting. This
check matters more than step 1, because it's the last chance to catch it
before the binary reaches Apple.

**7. Submit:**

```powershell
eas submit --platform ios --latest
```

**Look for:** a success message with an App Store Connect build ID. Apple then
processes the binary for roughly 5–10 minutes (sometimes longer); you get an
email when it's done, and it appears at
<https://appstoreconnect.apple.com/apps/6792203800/testflight/ios>.

**8. Export compliance:** `ITSAppUsesNonExemptEncryption` is already `false`
in `app.json`, so App Store Connect should not prompt for this. If it prompts
anyway, answer "No" (standard HTTPS/TLS only) — and note that it prompted,
because it means the flag isn't being read the way we think it is.

**9. Identify the right build in App Store Connect.** Builds share the label
`1.1.3` the same way every prior version shared its label — the running build
number does not reset per version, so if there is more than one build listed
under `1.1.3`, confirm both the **build number** you noted from `eas
build:list` in step 6 and the **upload date/time** match this session, not a
stale or partial upload from earlier. This is the same trap that put an
un-fixed build 3 in front of testers back on 1.0.0 — it recurs every release,
not just that one.

---

## Step 4 — Tester notes for 1.1.3

Paste this into the build's **What to Test** field in App Store Connect, then
add testers.

```
PlantAdvocate 1.1.3 — what's new

1. Watering is now a check, not an instruction. The to-do list used to say
   "Water" on a fixed schedule. It now says "Check" — feel the soil, then
   tell it what you found. Two buttons: "Watered" if it needed it, "Still
   damp" if it didn't. Either one keeps your streak; the point was never
   "did you pour water on a schedule," it's "did you look."

2. Repotting is now a once-a-year February check-up, not an anniversary
   reminder. It will ask four simple questions (roots crowding the pot,
   growth stalled, that kind of thing) once a year, and offers three honest
   endings: Repotted, Top-dressed, or All fine. You will NOT see any repot
   reminders on this build in August — that's correct, not a bug. The
   window only opens in February.

3. "N days past due" is gone. A plant you watered ten days ago inside its
   own documented 7-10 day window used to read "3 days overdue," which was
   simply wrong — day 10 of a 7-10 day window is the plant behaving exactly
   as expected. It now reads "Last done 10 days ago," and nothing is called
   overdue until it's actually past its own window.

4. A species page no longer shows a humidity percentage or a "humidity
   source" line if that number was never real. A lot of imported species
   never had a humidity number at all — one was estimated from a watering
   category at import time, and the app was presenting it as measured fact.
   It's gone from anywhere that isn't clearly marked as an estimate. As a
   side effect, some species' Almanac care-difficulty tier may have shifted
   slightly, since it's no longer scoring against a fabricated number.

5. Settings: "Repot reminder" is renamed "Spring repot check," to match #2.

Worth trying, in order of how much it would help:
- Check off a couple of watering to-dos and try both "Watered" and "Still
  damp." Confirm the due date moves either way and the streak doesn't break.
- Open a plant whose repot reminder you remember from a past build. Confirm
  it's simply gone from the to-do list right now (August) — that's the
  correct new behavior, not a regression.
- Open a few imported (non-curated) species pages and confirm there's no
  humidity stat and no odd "derived from..." trait line.
- Glance at a few species' Almanac tiers if you remember what they used to
  be — a shift is expected for some, not a sign something broke.

Still expected, not bugs:
- No UV reading and no "hours of daylight" on the weather card — the U.S.
  National Weather Service doesn't publish those two; that's the tradeoff
  for weather working at all while Apple's WeatherKit stays disabled on
  their end.
- On a phone without Apple Intelligence, the photo-identify button in Add
  Plant simply isn't there. Manual species search works for everyone.
```

**What this build has NOT proven:**

- The February repot inspection has never fired in real life — only in tests
  against a fake clock. It's August. The first real person to see that screen
  will see it next February, and that will be the actual first test of it.
- The 40 species of freshly researched, cited care data gathered this session
  are in the repo but **not in the app's database** — they're review
  artifacts waiting on a Phase 2 schema that doesn't exist yet. Nothing a
  tester does on this build touches them either way.
- None of the check/outcome buttons, the humidity suppression, or the shade-
  genera light fix have been seen rendering on a real screen. Every one of
  them is verified by `jest`/`pytest` assertions, not by a person tapping the
  app.

---

## Results — every outcome, and what it means

| Step | What you see | What it means | What to do |
|---|---|---|---|
| 1. Merge | Merge button greyed out or click does nothing | Stale page, or a protection rule / force-push landed since this doc was written — neither is currently true | Refresh, re-check Settings → Branches, re-check `git log origin/master` for anything unexpected, then retry |
| 1. Merge | Merges cleanly, `$HEAD` shows up in `origin/master` | Working as expected — no explanation was ever found for the earlier failed attempt, but nothing here suggests one is needed | Continue to Step 2 |
| 2. Deploy | CI's `Deploy to Fly` job goes red on the merge commit | Expected — no `FLY_API_TOKEN` secret exists yet, every push to master has failed this job the same way | Ignore it, deploy by hand as written above |
| 2. Deploy | `fly deploy` fails during build (Docker/pip step) | A real backend problem, unrelated to whether tests passed — CI's Python is 3.12, matching the Dockerfile, so this would be a new finding | Send the full `fly deploy` log; don't attempt to patch it live |
| 2. Deploy | `fly deploy` completes, but `/` never returns 200 within a couple minutes | Migration boot loop — `0007` through `0010` run before `uvicorn` binds, so a broken one shows up exactly here | `fly logs -a garden-gnome-api`, look for the migration name in the traceback; do not roll back before reading the log, since rollback restores the image, not the schema |
| 2. Deploy | `/` returns 200, `fly releases` shows a new `complete` version | Deploy succeeded, migrations applied | Continue to Step 3 |
| 3. Build | Build succeeds, `Commit` in `eas build:list` matches `$HEAD` | The Phase 1 changes compiled clean on the exact commit that's now on master. Nothing here touched native code, so a compile regression was never expected — but "shouldn't regress" and "did build" are different claims | Continue to submit |
| 3. Build | Build fails in a Swift compile phase naming `PlantIdModule.swift` or `FoundationModels` | A real, new regression in the native photo-ID module, unrelated to anything in this PR | Send the full log URL, don't patch live — this is worth taking seriously precisely because that module has compiled clean before |
| 3. Build | Build fails on credentials/provisioning | Signing setup, not the app code. `appleTeamId` is pinned in `app.json` | Re-run and let EAS manage credentials when prompted; if it fails the same way twice, send the error text |
| 3. Submit | Submits fine, but ASC prompts for export compliance | The `ITSAppUsesNonExemptEncryption: false` flag isn't being honored, or a new dependency added undeclared encryption use | Answer "No" (still almost certainly correct), then note that it prompted — that's new information regardless of the answer |
| 3. Submit | Submits fine, but TestFlight processing sits at "Processing" for over an hour | Usually an asset/Info.plist validation issue or an ASC-side outage, rarely the app code | Check email from Apple first; if nothing after ~2 hours, check developer.apple.com/system-status before assuming it's ours |
| Device | On an iPhone 15 Pro / newer on iOS 26, the identify button doesn't appear | Either Apple Intelligence isn't toggled on in Settings, or `isAvailable()` has a real bug at the hardware floor | Check Settings → Apple Intelligence & Siri first; if it's on and the button still doesn't show, that's a real bug worth reporting |
| Device | On an older/non-qualifying phone, `isAvailable()` returns false and the button is simply absent | **This is the correct, expected result on that hardware — not a failure to report.** | Confirm manual species search still works; nothing else to do |
| Device | Repot inspection screen doesn't appear anywhere in August | Correct — the window only opens in February | Nothing to do; this is not testable again until then |

---

## What to report back

In roughly the order it changes what happens next:

1. **Did PR #19 merge cleanly this time?** If the button was greyed out or
   silently failed again, exactly what you saw and what Settings → Branches
   showed.
2. **Did the Fly deploy complete, and does `/` answer 200?** If not, the
   `fly deploy` or `fly logs` output.
3. **Did the EAS build succeed, and did the commit in `eas build:list` match
   the merge commit from Step 1?** If not, the full log URL.
4. **Did submit + TestFlight processing complete, and what build number did
   it land as** (needed so the next install picks the right one)?
5. **Which phone(s) did you test on** — exact model and iOS version from
   Settings → General → About — and did each qualify for Apple Intelligence?
6. **Watering:** did "Watered" and "Still damp" both behave as described, and
   did the streak survive "Still damp"?
7. **Repotting:** confirm there is no repot to-do visible anywhere right now
   (August) — this is the expected result, but worth stating explicitly
   rather than assuming no news is good news.
8. **Species pages:** did any imported species still show a humidity number
   or a stray "derived from..." line? That would mean the suppression missed
   a surface.
9. **Settings shows v1.1.3:** the `support.ts` version label was fixed on
   this branch — confirm Settings and a support-email subject both say 1.1.3.
10. **Anything else that looked wrong** that isn't covered above — trust your
    own eye on how the app is supposed to feel; you know that better than
    this handoff does.
