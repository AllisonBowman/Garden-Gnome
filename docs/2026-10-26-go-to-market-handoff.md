# PlantAdvocate go-to-market and 1.1.3 polish: where it stands

**Note, 2026-10-30.** This file is now history; read
`docs/2026-10-16-app-store-finish-line-handoff.md`, "Update, 2026-10-30",
for what to do next. Two things below are no longer true. Its branch,
`claude/go-to-market-strategy-cd07f3` (tip `2182e96`), and
`claude/launch-day-site` (`fa4076b`) were pushed on 2026-10-26, after this
was written. And on 2026-10-30 the branch was folded into
`care-advice-honesty` at `b6fee6b`, and pushed. The commits kept their
content and messages but have new IDs there: `cd5560e` is `7a6e67c`,
`d956364` is `fd6f66a`, `5b2c9a1` is `e1c4091`, `cad38a8` is `d9afd5e`,
`2fee66f` is `02f108f`, `e91d7f7` is `aa47bf0`, and this file's own commit
is `b6fee6b`.

A docs lane finished the document work under "What's unfinished" the same
day: the completeness critic's leftovers and a read of `docs/go-to-market/`
for contradictions between files, and the refresh of the finish-line
handoff, which now carries every stale spot listed below and replaces the
next steps here. Every item of "Found and not yet fixed" was settled that
day on the ship branch. Items 1 and 2: the curated care notes were
rewritten without safety claims. Item 3: a boot-time refresh of curated
prose replaces the one-off, which nobody needs to run. Item 4: all three
hazard-sentence changes landed, backend only, so they ship with the deploy;
the table clauses are labelled "PlantAdvocate's own summary" rather than
cited. Item 5: the not-advice line and the "Report a fact" link both went
into 1.1.3 rather than 1.1.4. The six site copy fixes ride with step 3, and
the two privacy changes the outreach lane asked for went with them. The launch-day site review and
`docs/go-to-market/launch-day-site.md` were finished on 2026-10-31; the
finish-line handoff's block of that date says where the branch stands.

Written 2026-10-26 on the Mac about branch `claude/go-to-market-strategy-cd07f3`
(worktree `.claude/worktrees/go-to-market-strategy-cd07f3`). The branch starts
at the ship tip `3f6d7da` on `care-advice-honesty` and adds the commits listed
below. Nothing has been pushed, no PR is open, nothing is merged and nothing is
deployed. Whether to push and where to open a PR is yours to decide.

This file sits beside `docs/2026-10-16-app-store-finish-line-handoff.md`, which
is still the runbook for the build, the deploys and App Review. Where the two
disagree, the section "Where the finish-line handoff is now stale" says which
wins. Commands follow that handoff's convention: zsh on this Mac, one command
per block, no `#` comments in blocks.

## Why this matters

Two of the fixes here change what 1.1.3 shows. The Care facts card printed
"60–85°f" because a style lowercased the F, and 25 em dashes in the curated
catalog read "â€”" on pages such as Dumb Cane and Boston Fern. Both are fixed on
this branch, and they reach 1.1.3 only if the branch is merged into
`care-advice-honesty` before you start the EAS build. The build hasn't been
started, so there is still time. Merging it changes app code, so PR #22's CI
runs again and you wait for green as before.

The rest is documents: App Store screenshots that pass their check, review notes
and prepared replies, a sourced answer on the iOS 27 crash, and a go-to-market
strategy with a launch kit. The strategy also found honesty problems in the
catalog's own care notes that the marketing can't paper over. They are in
"Found and not yet fixed" below, because they should be settled before you
press Submit.

## What's done

On `claude/go-to-market-strategy-cd07f3`, oldest first:

| Commit | What it is |
|---|---|
| `cd5560e` | The 16 App Store screenshots in `docs/screenshots/1.1.3/` (8 for the iPhone 17 Pro Max, 8 for the 17 Pro), with `README.md` mapping each to its shot and `CHECK.md`, the 2026-10-24 check: all 16 pass. |
| `d956364` | `docs/2026-10-24-ios27-scene-lifecycle.md`: the iOS 27 launch crash can't reach an EAS build of 1.1.3. |
| `5b2c9a1` | `docs/app-store/review-notes.md` rewritten (Notes block 3,710 bytes of 4,000) and `docs/app-store/review-replies.md`, replies to paste if App Review raises 2.1(a), 5.1.1(v), 4.8, 2.3 or a server error. |
| `cad38a8` | `docs/go-to-market/`: the product truth sheet, five fact-checked research files, `strategy.md`, `targets.md`, `launch-day-runbook.md` and `launch-kit/` (press release, fact sheet, outreach emails, community posts, social calendar, waitlist email, listing proposals). |
| `2fee66f` | The °F fix: the Care facts stat row and the species page's trait keys no longer change case with a style, and a jest test keeps it that way. |
| `e91d7f7` | The catalog encoding fix: 25 garbled em dashes mended byte for byte in `species_catalog.json`, and `garden-gnome/tests/test_catalog_encoding.py` checks every data file. |
| (the last commit) | This handoff. |

The code commits came last, after the gates. On the code: backend suite
7,039 passed with none failing or skipped, mobile jest 543 of 543 in 48
suites, `npm run typecheck` clean, leak scan clean, all run on 2026-10-26 in
this worktree (the backend with the main checkout's venv, since the worktree
has none). The workflow's
own adversarial code review never ran (see "What's unfinished"), so the code
diff has had one read, by the session that wrote this file.

On a separate branch, `claude/launch-day-site`, in the worktree
`.claude/worktrees/wf_d353fa50-028-41`, commit `fa4076b` holds a draft of the
launch-day site: App Store links in place of every early-access call to
action, the Smart App Banner, description, Open Graph and Twitter tags on every
page, a new `site/press.html` and a Press footer link. It is unreviewed, and
it must not go out before launch day (see the next section).

The strategy in one paragraph, from "The plan in brief" in `strategy.md`: let
the App Store do most of the work, because it keeps working in the weeks you're
on other projects. Release quietly to the United States only, in November. Put
Apple's ratings prompt in the scene-adopted 1.1.4 that Apple's April 2027 SDK
rule forces anyway. Push for spring with the fit engine. It runs at $0 in about
70 hours over eight months, by the strategy's own estimate. Its decisions table
has 26 rows, each with a recommendation and a date.

## What must not ship on the pre-launch site deploy

The finish-line handoff's step 3 deploys `site/` from the ship branch before
App Review. That deploy must carry nothing that says the app is available.

Don't merge `claude/launch-day-site` into `care-advice-honesty` or `master`
before launch day, and don't deploy from it. Everything on it (App Store links,
"On the App Store" buttons, the Smart App Banner, `press.html`) is true only
once the app is live. `docs/go-to-market/launch-day-runbook.md` says when it
merges: the morning of L, before you press Release, because every push to
`master` now redeploys Fly.

Two things should happen before step 3, and neither is done:

1. Export the July waitlist. Step 3's deploy drops `/api/waitlist`; the
   addresses stay in Cloudflare until you export them.
   `docs/go-to-market/launch-kit/waitlist-email.md` has the steps. Keeping the
   list is your decision (finish-line handoff, decision 9).
2. The five site copy fixes in `strategy.md`, "The site, riding along with step
   3": the independence line on four pages, two over-reaching lines on
   `about.html`, the Pothos "safe bet" on `recommendations.html`, and the "NO
   GUESSWORK" strip on `index.html`. Add a sixth:
   `site/recommendations.html:248` promises "no more guessing whether that
   fiddle leaf fig stood a chance in your bathroom", and the fit engine can't
   judge indoor light (`garden-gnome/app/services/fit.py`, `_sun` returns
   unknown for every indoor area). These are copy edits on the ship branch, so
   they ride with step 3.

## Found and not yet fixed

Each needs a yes or no from you. None needs a new app build. The first three
need a data change on the branch and a one-off on production after step 2.

1. **33 curated care notes call a plant "Pet-safe", "harmless" or "safe for
   most pets".** They are in `garden-gnome/app/data/species_catalog.json` and
   show in the Care notes card on species and plant pages. On Parsley, Catnip,
   Nasturtium and Gourds, the hazard sentence on the same page says the
   opposite. They break the listing's "A missing record is never treated as
   safe". The strategy recommends rewriting all 33 without the safety claim,
   keeping the care advice, before Submit if possible and before Release at
   the latest.
2. **Six care notes contradict their cited records.** Sage, Thyme, Baby's
   Breath and Hollyhock say "mildly toxic" where NC State Extension records
   them as non-toxic to cats and dogs. China Aster's note says the same,
   against a no-toxicity verdict. Moonflower's says all parts are toxic, where
   its source names only the seeds. Recommend fixing them in the same pass as
   the 33.
3. **Production keeps the garbled dashes after the deploy.** The container
   runs `python -m app.data.seed` on boot, and `seed()` skips any species
   already in the table (`garden-gnome/app/data/seed.py`, around line 344), so
   it never rewrites a row. The claim sync never touches care notes, soil types
   or schedule notes. The text has been there since the first commit, before
   the Fly app existed. Recommend a one-off after step 2's deploy, which also
   comes after step 2's volume snapshot. It was practised on 2026-10-24 on a
   scratch database seeded from the old file and printed 25, `fixed 25`, then
   0; it has never run on production. The fix goes through the app's models,
   which stamps a new catalog generation, so phones get clean text on their
   next fetch without a restart. If you say yes to items 1 and 2, the same
   route carries those rewrites, and the commands will need extending to
   match.

   Open a shell on the machine:

   ```bash
   fly ssh console -a garden-gnome-api
   ```

   At the machine's prompt, one at a time. First move to the app:

   ```bash
   cd /app
   ```

   Count the garbled values; expect 25:

   ```bash
   DATABASE_URL=sqlite:////data/garden_gnome.db python -c "from sqlmodel import Session,select;from app.db.database import engine;from app.models.models import Species,CareSchedule;B,G='â€”','—';s=Session(engine);hits=[(r,f) for m,fs in ((Species,('care_notes','soil_type')),(CareSchedule,('notes',))) for r in s.exec(select(m)).all() for f in fs if B in (getattr(r,f) or '')];print(len(hits))"
   ```

   Fix them; expect `fixed 25`:

   ```bash
   DATABASE_URL=sqlite:////data/garden_gnome.db python -c "from sqlmodel import Session,select;from app.db.database import engine;from app.models.models import Species,CareSchedule;B,G='â€”','—';s=Session(engine);hits=[(r,f) for m,fs in ((Species,('care_notes','soil_type')),(CareSchedule,('notes',))) for r in s.exec(select(m)).all() for f in fs if B in (getattr(r,f) or '')];[setattr(r,f,getattr(r,f).replace(B,G)) for r,f in hits];s.commit();print('fixed',len(hits))"
   ```

   Run the count once more and expect 0, then type `exit`. Leave the `\u`
   escapes as they are; Python turns them into the real characters. The
   `DATABASE_URL` is set on purpose: without it the code falls back to a
   database in the working folder instead of `/data`. A count above 25 would
   mean older imported rows carry the same flaw; the fix covers them too.

4. **The hazard sentences, by the end of February.** Three backend-only
   changes: "or your local poison centre" after the US number; the pet
   verdict's source named in the sentence; and the lily, daylily and arum
   effect clauses in `garden-gnome/app/services/toxicity.py`, which come from
   code tables rather than a cited page, either cited or labelled as
   PlantAdvocate's summary. Until then, store copy names no lily, daylily or
   aroid. Details are in `strategy.md`, "The hazard sentences".
5. **In 1.1.4, with the ratings prompt.** The line "These notes repeat what the
   sources publish. They are not medical or veterinary advice." appears in the
   listing, the review notes and the site but on no app screen. Add it under
   the hazard sentence, and add a "Report a fact" link on species pages.

## What's unfinished

The workflow that wrote most of this (`wf_d353fa50-028`) stopped on 2026-10-24
at 12:01, with 41 of its 44 agents done, when the session ended. Three agents
never finished, and the verification after them never started:

- **The launch-day site lane** made its edits and stopped before its honesty,
  policy and voice reviews and its link check, and before it wrote
  `docs/go-to-market/launch-day-site.md`. Its edits are the unreviewed draft
  `fa4076b` described above. Six lines of `launch-day-runbook.md` and one of
  the folder's `README.md` point at `launch-day-site.md`, which doesn't exist.
  Before using the draft, check its "Download from the App Store" wording
  against Apple's text-link rules in `docs/go-to-market/research/aso.md`.
- **The completeness critic** never ran over `docs/go-to-market/`. The lanes
  that fixed review findings reported these leftovers for it: `strategy.md`
  (around lines 376 and 382) and `research/aso.md` (around line 171) still
  carry the older winter and mid-April promotional lines that
  `launch-kit/listing-proposals.md` replaced; `launch-day-runbook.md` still
  mentions `removed.txt`, "the privacy policy's promise is enough" and "without
  the list footer", which `waitlist-email.md` changed;
  `research/launch-playbook.md` says the July form's wording couldn't be
  recovered, but `waitlist-email.md` found it in commit `25f370f`;
  `outreach-emails.md` calls the magazine "American Gardener", where
  `strategy.md` and `channels.md` say "The American Gardener"; and the outreach
  lane asked for two `site/privacy.html` changes before any waitlist send
  (narrow "we don't send marketing email", and say a removed address is kept
  only to avoid writing to it again), which nobody has made.
- **The handoff lane** never updated the finish-line handoff. This file takes
  its place; the stale spots are listed below.
- **The verification phase** (gates, an adversarial code review and a leak scan)
  never started. This session ran the gates and the leak scan itself and read
  the code diff (the results are under "What's done").

Resuming the workflow as it stands would re-run the site lane from the start in
a fresh worktree, and the draft would be lost. A short new run is the better
way to finish: review and complete `claude/launch-day-site`, write
`launch-day-site.md`, run the critic over `docs/go-to-market/`, and fold the
stale spots below into the finish-line handoff. The journal with every agent's
result is under
`~/.claude/projects/-Users-allisonbowman-Developer-Garden-Gnome--claude-worktrees-go-to-market-strategy-cd07f3/b737605c-ac93-493c-b5dd-2f1c39e6d0ab/subagents/workflows/wf_d353fa50-028/`.

## Where the finish-line handoff is now stale

- Step 4 says the Notes block is 3,987 of 4,000 characters and asks for a
  phone number "with its country code". The rewritten block is 3,710 bytes,
  and the phone goes in plus-sign format (`+1 …`).
  `docs/app-store/review-notes.md` wins.
- It says the sandbox can't capture screenshots. They exist in
  `docs/screenshots/1.1.3/` and all 16 pass `CHECK.md`. `strategy.md`
  recommends uploading them in the order 01, 04, 06, 02, 03, 05, 07, 08.
- It has no step for exporting the waitlist before step 3, and no step for the
  production one-off in item 3 above. Both belong between steps 2 and 3.
- It doesn't mention iOS 27. Don't change the EAS image for 1.1.3
  (`macos-tahoe-26.5-xcode-26.6` links against the iOS 26.5 SDK, which
  Apple's scene rule doesn't touch), and don't upload a 1.1.3 built on this
  Mac, whose only Xcode is 27.1.

## Next steps, in order

1. Read "The plan in brief" at the top of `docs/go-to-market/strategy.md`
   (about ten minutes).
2. Decide whether to push this branch, and where to open its PR. The
   recommendation is a PR into `care-advice-honesty`, merged before the EAS
   build so the two code fixes reach 1.1.3.
3. Answer items 1 to 3 of "Found and not yet fixed". With a yes, the note
   rewrites are a data change on this branch with a test, and the production
   one-off extends to cover them.
4. Export the July waitlist, before step 3.
5. Say yes or no to the six site copy fixes so they can ride with step 3.
6. File the App Launch featuring nomination this week, with a date range that
   starts about two weeks after the release you expect (`strategy.md`,
   "Featuring Nominations").
7. In step 4, paste the subtitle and keywords from
   `docs/go-to-market/launch-kit/listing-proposals.md`, upload the screenshots
   in the order above, set availability to the United States only, and choose
   manual release.
8. Have the unfinished pieces finished: the launch-day site review, the critic
   and the finish-line handoff refresh.

## What to report back

Your answers to items 1, 2 and 3 of "Found and not yet fixed" and to the six
site fixes; whether to push and where the PR goes; and, once you've run it,
whether the production count printed 25.
