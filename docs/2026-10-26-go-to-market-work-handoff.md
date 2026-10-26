# Go to market work: where this session left things

Written 2026-10-26 from the worktree `.claude/worktrees/go-to-market-work-f30550`.
This session ran on 2026-10-17. Its work is already on the ship branch, so this
file only says where that work went and what is still open. The runbook for
everything that needs your logins is `docs/2026-10-16-app-store-finish-line-handoff.md`
on `care-advice-honesty`, and it is newer than anything here.

## What this session did

It found that the 1.1.3 production build had never been started on 16 October:
EAS still listed 1.1.2 build 15 as the newest iOS build. The pre-flight passed on
`62d3a66`. The tree was clean, the Xcode 26 image was pinned, and EAS resolved
version 1.1.3 as an iPhone-only app. Starting the build from the sandbox was
refused. A later session found the real blocker: EAS needs your interactive Apple
sign-in to check the certificate. The top of the finish-line handoff now gives the
command to run yourself.

It settled decision 6 of the finish-line handoff for four of the five named
poisons. Foxglove, English yew, monkshood and jimsonweed now cite NC State's
Poisonous to Humans block, which rates each of them Poison Severity: High. The
pages were re-read live on 17 October, and every quote was checked against them.
Twelve verifier agents then tried to refute the records, three lenses per species.
One refutation stood: foxglove's restated text said "the source of the drug
digitalis" where Missouri Botanical Garden says "a source". That sentence now
leans only on NC State and RHS, because the record's own notes say the Clemson and
Missouri Botanical Garden pages were never read by the researcher. A stale
monkshood note that said NC State's page was never read is marked superseded. A
regression test pins all four records to NC State's high rating. The catalog went
from 10,679 to 10,681 claims.

It also updated the harm-capable entry in `CONTEXT.md` to ADR 0008's wording, and
it brought the finish-line handoff up to date for 17 October.

## Where it went

All of it is one commit, `cdc4965`, on branch `claude/gtm-ship-1.1.3`, which is on
GitHub. The same change landed on `care-advice-honesty` as `307930e`, and `git
cherry` confirms the two are the same patch. So it is in PR #22
(https://github.com/AllisonBowman/Garden-Gnome/pull/22) already, and
`claude/gtm-ship-1.1.3` needs no PR of its own. You can delete that branch once PR
#22 merges. This worktree's own branch, `claude/go-to-market-work-f30550`, carries
only this file.

## What is still open

Lily of the valley is still your call. NC State's live page rates it Poison
Severity: Low ("toxic only if large quantities eaten"), while Missouri Botanical
Garden calls all parts very poisonous. It was left as it was, so it can still
appear as a growing-area candidate. Decision 6 in the finish-line handoff
describes the trade-off. Making it never a candidate is a one-record change and a
deploy, with no app build.

Add plant should say that a species has no check schedule before you add it. The
species list that screen reads carries no schedules, so this needs a per-species
fetch and a new build. It is listed for 1.1.4 in the finish-line handoff.

The quote checker found 8 misses in the batch files this session touched. None of
them is on a line this session changed. They are castor bean (3 quotes), lily of
the valley's older NC State quote, American mistletoe, avocado, and southern live
oak (2 quotes). They look like the pages changing since the research, not invented
quotes, but nobody has re-read them. They are worth a re-verification pass in the
catalog loop.

The screenshot session this one proposed is no longer needed. The 1.1.3
screenshots were shot in the go-to-market-strategy-56bf52 session, and the
go-to-market-strategy-cd07f3 worktree carries them now, with the rest of the
launch kit.

## Next steps

1. Work through `docs/2026-10-16-app-store-finish-line-handoff.md` on
   `care-advice-honesty`, top to bottom. It covers the EAS build with your Apple
   sign-in, merging PR #22 once CI is green, the Fly token and deploy, and the
   Cloudflare site deploy. On 17 October, `npx wrangler whoami` on this Mac said
   the token had expired, so the site step starts with `npx wrangler login`. The
   App Store Connect paperwork comes after those.
2. Decide lily of the valley: leave it as a possible candidate, or never put it
   forward.
3. For the go-to-market work itself, resume the go-to-market-strategy-cd07f3
   session. Its workflow `wf_d353fa50-028` stopped on 24 October with the site
   lane, the critic and its handoff unfinished.
