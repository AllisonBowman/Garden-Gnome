# Launch-day runbook for PlantAdvocate 1.1.3

Written 2026-10-24 for Allison, against the ship tip `3f6d7da` (branch `care-advice-honesty`, PR #22). It covers what you do from the moment App Review approves 1.1.3, with a manual release, through the seventh day after you release it, then what must already be true before that day, and the check-ins for the first 30 days and the winter. L is the day you press Release. Approval can come the same day or a few days earlier.

Nothing in this file has been done. Nothing was sent, posted, filed or submitted while writing it, and every outward step is yours to take, change or skip. It follows [strategy.md](strategy.md), which wins wherever the two disagree, and every line of public copy here was checked against [product-truth.md](product-truth.md). "The handoff" is [docs/2026-10-16-app-store-finish-line-handoff.md](../2026-10-16-app-store-finish-line-handoff.md), and its step and decision numbers are the ones meant here. The ready-to-edit drafts are in [launch-kit/](launch-kit/): the [waitlist email](launch-kit/waitlist-email.md), the [community posts](launch-kit/community-posts.md) with their reply bank, the [outreach emails](launch-kit/outreach-emails.md), the [press release](launch-kit/press-release.md), the [fact sheet](launch-kit/fact-sheet.md), the [listing proposals](launch-kit/listing-proposals.md) (the step zero fields and the promotional text) and the [social posts](launch-kit/social.md) (optional, with their own launch-week calendar). The site edits for launch day will be described in `launch-day-site.md`, which is written when branch `claude/launch-day-site` is reviewed and doesn't exist yet. The outlets and communities are in [targets.md](targets.md).

Commands are zsh on the Mac, one per block, with no `#` comments, as in the handoff. Words in capitals inside a command, such as `PROJECT` or `RUN_ID`, are placeholders you fill in. Every time estimate is mine and counts your hands-on time, not time spent waiting for Apple or CI.

If L is still ahead of you, start with [the pre-launch checklist](#the-pre-launch-checklist). If App Review rejects instead of approving, read the next section and stop there.

## The week at a glance

| When | What | Your time (my estimate) |
|---|---|---|
| Approval day | Check four things, decide on the always-on server, choose the release morning | About 70 minutes |
| L, first thing | Merge the launch-day site branch and let its CI run finish, then press Release in App Store Connect | About 20 minutes, plus up to 30 minutes on CI and up to 24 hours waiting for the page |
| L, once the product page answers | Confirm the store URL and app id, install from the store on a clean phone, deploy and check the launch-day site | About 2 hours |
| L+1 or L+2 | Make the campaign links, send the waitlist email, give the site's buttons the `site` token | 3 to 4 hours |
| L+1 to L+3 | Reply one by one to the people who emailed for early access | About 5 minutes each |
| Every day, L to L+7 | Reviews, the support inbox, the backend, App Analytics | 15 to 20 minutes, plus 5 to 10 minutes per review reply |
| L+7 | The first-week read and its decisions | About 45 minutes |

That is roughly 10 hours across the week. [strategy.md](strategy.md#timeline-2026-10-24-to-june-2027) gives about 3 hours for L itself and 2 to 3 hours a week after it, so launch week is the heaviest one, as it says. Nothing goes out in bulk on L.

## If App Review rejects

The prepared replies are in [docs/app-store/review-replies.md](../app-store/review-replies.md), one for each risk [review-risk.md](research/review-risk.md) rates, and each says what to check before you paste it. Read App Review's message twice and answer what it actually says.

Nothing outward has happened yet, so a rejection breaks no promise. Don't merge the launch-day site branch, and don't change the site. If the new approval date will fall after the start of the App Launch nomination's date range, edit the range in App Store Connect's Featuring section. A rejection that needs a new binary means a new build on EAS with the image `eas.json` pins, never one built on this Mac ([review-replies.md](../app-store/review-replies.md#if-the-rejection-is-a-crash), [docs/2026-10-24-ios27-scene-lifecycle.md](../2026-10-24-ios27-scene-lifecycle.md)). When approval does come, start at the next section.

## Approval day

Apple emails you when the status changes, and the 1.1.3 version page in App Store Connect then reads Pending Developer Release. Nothing is public yet. Apple sends a reminder if a version waits in that status for more than 30 days ([Apple, release options](https://developer.apple.com/help/app-store-connect/manage-your-apps-availability/select-an-app-store-version-release-option)), but [strategy.md](strategy.md#featuring-nominations) says not to hold an approved build for a featuring window, so plan to release within a day or two.

### Four things to check before you release

First, production is serving the 1.1.3 backend and is awake:

```bash
curl -s --max-time 30 https://garden-gnome-api.fly.dev/
```

Look for a `catalog` block with `"synced": true`. Both the old and the new server say version `0.2.0`, so the catalog block is what tells them apart.

```bash
curl -s https://garden-gnome-api.fly.dev/openapi.json | python3 -c "import json,sys; p=json.load(sys.stdin)['paths']; print(len(p), any(k.startswith('/growing-areas') for k in p))"
```

Look for `34 True`.

Second, the honesty fixes the store page depends on are live. On your phone, in the TestFlight build with the approved build number, open the Species tab and look up Spider Plant, Boston Fern, Sunflower, Parsley, Catnip, Nasturtium and Gourds. Gourds is the only note that said "safe for most pets", and Catnip the only one that said "harmless". Read each Care notes card. None may call the plant "Pet-safe", "harmless" or "safe for most pets". These seven are a sample. Before you release, look up the other 26 too, which takes about 20 minutes: Calathea, Parlor Palm, Wax Plant, Prayer Plant, Chinese Money Plant, Moth Orchid, Cast Iron Plant, Nerve Plant, Dill, Stevia, Sweet Alyssum, Bachelor's Button, Celosia, Cosmos, Impatiens, Pansy, Petunia, Annual Salvia, Zinnia, Black-Eyed Susan, Blanket Flower, Coneflower, Coreopsis, Penstemon / Beardtongue, Rudbeckia / Orange Coneflower and Viola / Horned Violet. This is the fix to the 33 curated care notes in [strategy.md](strategy.md#the-pet-safe-care-notes-before-release), and it has to be in production's rows, not only in the JSON, because the seed skips species that already exist.

The 33-note fix leaves other curated notes that make their own uncited hazard remarks, Dumb Cane's among them. Six of them disagree with the cited record. Sage, Thyme, Baby's Breath and Hollyhock say "mildly toxic" where NC State Extension records them as non-toxic to cats and dogs. China Aster's note says the same against a no-toxicity verdict, and Moonflower's says all parts are toxic where its source names only the seeds. Open those six as well, and compare each care note with the hazard sentence above it.

On the same pages, and on Dumb Cane, look for garbled characters, and check that Snake Plant's temperature reads "60–85°F" with a capital F. If any care note still makes a safety claim, or contradicts the hazard sentence above it, don't release. The fix is data and a deploy, with no new build, so bring it to Claude; the six are the same kind of fix as the 33.

Third, the pre-launch site from the handoff's step 3 is still what plantadvocate.ai serves. Run the check block in [site/README-SITE.md](../../site/README-SITE.md), as master has it before the launch-day merge, and look for `ok` on every line. The desktop generator must not have been run since.

Fourth, the store settings. In App Store Connect, Pricing and Availability should list the United States only, and the version's status of Pending Developer Release shows the manual release took. In Featuring, the App Launch nomination should be submitted with a date range that starts about two weeks after the release you now expect. If App Store Connect refused the nomination before approval, file it today from the drafts in [research/aso.md](research/aso.md#featuring-nominations), with the range starting at least three weeks out, as [strategy.md](strategy.md#featuring-nominations) says.

### Decide on the always-on server

If you said yes to decision 1, the machine has been kept awake through review, and the handoff says to put `min_machines_running` back to 0 after approval. My recommendation is to wait until L+7. The first people who aren't testers arrive on L, a first request after idle took 6.7 seconds on 15 October, and [strategy.md](strategy.md#in-the-store) names that wait as a first-impression risk for the ratings. The cost is one more week of the machine billing all day. If you'd rather save it, ask Claude for the one-line PR now; merging it deploys.

### Choose the release moment

Release on a morning when you can give the next two days to it, because the waitlist email and the first replies fall on L+1 and L+2. If L would land on a Friday, or in a week you're away, wait for the next good morning; a day or two in Pending Developer Release costs nothing. If L falls in Thanksgiving week (Thursday 26 November 2026), the published promise to reply "usually within 2 business days" still applies, so plan the days around it.

Once you've picked the morning, ask Claude to set the privacy policy's effective date on `claude/launch-day-site` to that day, and the matching check line in `site/README-SITE.md` with it. If L moves before you merge, change both again. The date has to be the day the policy goes live on plantadvocate.ai.

## L: release day

### Merge the launch-day site branch

The launch-day edits to the site are on a branch called `claude/launch-day-site`, apart from `site/` on the ship branch, because the step 3 deploy has to go out with no App Store links. The branch has been on GitHub since 2026-10-26 and holds one draft, `fa4076b`, which nobody has reviewed: the lane that made it stopped before its honesty, policy and voice reviews and its link check. Before L, ask Claude to review and finish the branch, write `docs/go-to-market/launch-day-site.md`, push the result and open the pull request. That file doesn't exist until the review writes it. It will list what the branch changes: the App Store badge, the Smart App Banner, Apple's credit line, the early-access and campaign-label clauses in the privacy policy with a new effective date and "What changed" line, and the updated check line in `site/README-SITE.md`. The review also settles two wordings the research files leave open: the draft's "Download from the App Store" buttons, against Apple's naming rules in [research/aso.md](research/aso.md), and the credit line, which aso.md, [research/launch-playbook.md](research/launch-playbook.md) and the draft each word differently.

Merge it on the morning of L, just before you press Release, so this section is the first thing you do that day. Merging deploys nothing to plantadvocate.ai, because the site goes up only when you run wrangler. It does redeploy the backend, because since step 2 every push to master deploys to Fly, and it is better for that restart to happen while nobody outside is using the app. Once it is merged, don't deploy `site/` from master until the App Store page answers, or the site will link to a page that returns 404; merging on the day keeps that window short.

Find the pull request. If Claude opened it for you, it is listed here:

```bash
gh pr list --repo AllisonBowman/Garden-Gnome --head claude/launch-day-site --state open
```

If nothing is listed, the pull request isn't open. Ask Claude to push the reviewed branch and open it. The unreviewed draft has been on GitHub since 2026-10-26, so don't open a pull request on it alone; once Claude has pushed the reviewed branch, and only the pull request is missing, you can open it yourself:

```bash
gh pr create --repo AllisonBowman/Garden-Gnome --base master --head claude/launch-day-site --fill
```

Below, its number is `LAUNCH_PR`. Check that it touches only the site and docs:

```bash
gh pr diff LAUNCH_PR --repo AllisonBowman/Garden-Gnome --name-only
```

Look for paths under `site/` and `docs/` and nothing under `garden-gnome/` or `mobile/`. If anything else is there, stop and bring the list to Claude.

```bash
gh pr checks LAUNCH_PR --repo AllisonBowman/Garden-Gnome
```

Look for Backend tests and Mobile typecheck and tests both reading `pass`. If either says `pending`, add `--watch` at the end and let it finish.

```bash
gh pr view LAUNCH_PR --repo AllisonBowman/Garden-Gnome --json headRefOid,mergeable,mergeStateStatus
```

Look for `MERGEABLE` and `CLEAN`. If it reports a conflict, stop and bring the output to Claude.

```bash
gh pr merge LAUNCH_PR --repo AllisonBowman/Garden-Gnome --merge
```

```bash
gh run list --repo AllisonBowman/Garden-Gnome --branch master --limit 1
```

Note the run's ID, then watch it:

```bash
gh run watch RUN_ID --repo AllisonBowman/Garden-Gnome
```

Expect the two test jobs, Deploy to Fly and the Smoke check all to go green. The backend code hasn't changed, so the boot logs `Species catalog already up to date.` and `claim sync: tranche unchanged, nothing to do`, and a low attempt count is normal this time. If the smoke check fails, don't release: follow the step 2 rows of the handoff's table "When the outcome isn't obvious", and bring the log to Claude.

If you don't press Release today for any reason, ask Claude for a pull request that reverts the launch-day merge, and merge it the same day, so master's `site/` is the pre-launch site again. Until it is, don't deploy `site/` from master or from any checkout of it, for any reason. The badge may appear only once the app is on the App Store, and the banner would point at a page that returns 404.

### Release

In App Store Connect, open Apps, then PlantAdvocate, select the 1.1.3 version whose status is Pending Developer Release, click Release This Version at the top right, then Confirm. Apple says the version may then take up to 24 hours to appear on the App Store, and that you can cancel from the message on the version page with Cancel This Release ([Apple, release options](https://developer.apple.com/help/app-store-connect/manage-your-apps-availability/select-an-app-store-version-release-option)). The status should move on to Ready for Distribution. If you cancel the release, ask Claude for a pull request that reverts the launch-day merge and merge it the same day, as above, and don't deploy `site/` from master until it is merged.

Do nothing outward until the product page answers. The site still says "in beta on iPhone", and that is true until the page loads.

### Confirm the store URL and the app id

Check every hour or so until these answer. Apple's search API and the product page can each lag behind the other.

```bash
curl -s "https://itunes.apple.com/lookup?id=6792203800&country=us" | python3 -c "import json,sys; r=json.load(sys.stdin); print(r['resultCount']); [print(x['trackId'], x['trackName'], x['version'], x['formattedPrice'], x['trackContentRating'], x['trackViewUrl']) for x in r['results']]"
```

Look for `1`, then a line with `6792203800`, the name App Store Connect accepted (`PlantAdvocate: Garden Care`, or `PlantAdvocate`), `1.1.3`, `Free`, `4+`, and a URL ending in `id6792203800?uo=4`. On 2026-10-24 this returned `0`.

```bash
curl -s -o /dev/null -w '%{http_code} %{url_effective}\n' -L https://apps.apple.com/app/id6792203800
```

Look for `200`, landing on a `/us/app/` address that ends in `id6792203800`. On 2026-10-24 it answered `404`. The short form, `https://apps.apple.com/app/id6792203800`, is the one the launch-day site and the later "Rate PlantAdvocate" row use.

```bash
curl -s "https://itunes.apple.com/lookup?id=6792203800&country=gb" | python3 -c "import json,sys; print(json.load(sys.stdin)['resultCount'])"
```

Look for `0`, which confirms the app isn't offered in the UK store, as the US-only setting intends. Also check that App Store Connect, under App Information, shows 6792203800 as the Apple ID. If any of these shows a different id, stop: the launch-day site and `mobile/eas.json` both carry 6792203800, so bring it to Claude before deploying anything.

Then open the product page in the App Store app on your phone and read it as a stranger would. Check the name and the subtitle, that the first three screenshots are 01, 04 and 06 (what doesn't suit a spot, checks not chores, hazards on Pothos), that it says Free with no In-App Purchases line, that the privacy section reads Data Linked to You (Contact Info, Identifiers, Location, User Content) with no Data Used to Track You section, and that the age rating is 4+. Searching the store for "PlantAdvocate" may not find it yet; the direct link is what counts today. Note anything wrong. Screenshots, subtitle and keywords can change only with a new version, but promotional text can change at any time.

### Install from the store on a clean phone

Delete the TestFlight build from the phone first, so you install exactly what a stranger gets. Then install PlantAdvocate from the App Store. If you have a second Apple ID that has never used PlantAdvocate, sign in with that, because it is the path a new person takes. Allow about 30 to 45 minutes.

Go through these and note what you see. Sign in with Apple, and expect My Home and the welcome cards. Make a growing area, add a plant, and check that the fit check shows before you save. Open the Species tab, the Almanac, and Pothos, whose hazard sentence names cats, dogs and people, NC State's rating and the Poison Control line. Open Settings and check that it shows 1.1.3. If you used a spare Apple ID, delete that account from Settings > Account > Delete account afterwards. Never do that on your own account.

If sign-in fails, a growing area won't save, or the app crashes, don't deploy the site and send nothing. Go to [If something breaks in launch week](#if-something-breaks-in-launch-week). The app being live and quiet is the soft launch working as intended.

### Deploy the launch-day site

This deploys exactly what master holds, from a temporary copy, so it needs no change to your main checkout's branch. Do it all in one terminal window, because one command below sets `D` for the ones after it. `PROJECT` and `PRODUCTION_BRANCH` are the names you found in the handoff's step 3.

```bash
npx wrangler whoami
```

If it says the token has expired, run `npx wrangler login` and come back.

```bash
git -C /Users/allisonbowman/Developer/Garden-Gnome fetch origin master
```

```bash
git -C /Users/allisonbowman/Developer/Garden-Gnome log -1 --format='%h %s' origin/master
```

Look for the merge of the launch-day pull request, or a later commit.

```bash
D=$(mktemp -d) && git -C /Users/allisonbowman/Developer/Garden-Gnome archive origin/master site | tar -x -C "$D" && rm "$D/site/README-SITE.md" && ls "$D/site"
```

Look for the 13 pages, plus any file the launch-day branch added, such as a press page or the badge artwork. Then check the links in that copy. This is the step 3 checker with one change: a link to a local file that isn't a page, such as a badge image, passes if the file is there. It must end `0 broken`:

```bash
python3 - "$D/site" <<'EOF'
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
        if t not in parsed:
            if not (site / t).is_file(): bad.append(f"{n}: {l} -> no such file")
        elif f and f not in parsed[t].ids: bad.append(f"{n}: {l} -> no id {f!r}")
print(f"{len(pages)} pages, {len(bad)} broken"); [print(" ", b) for b in bad]
EOF
```

It skips links that start with `https:`, so it doesn't test the App Store link; the checks after the deploy do that.

```bash
npx wrangler pages deploy "$D/site" --project-name=PROJECT --branch=PRODUCTION_BRANCH
```

`--branch` is required for the same reason as in step 3: without it the deploy goes to a preview, not to plantadvocate.ai.

### Check the site

The check block in `site/README-SITE.md` changes in the launch-day branch, because the privacy policy's effective date moves. Print the version on master:

```bash
git -C /Users/allisonbowman/Developer/Garden-Gnome show origin/master:site/README-SITE.md | sed -n '/^## Verifying the deploy/,/^## When the app changes/p'
```

Run that check block as printed, and look for `ok` on every line. Then run the lines `launch-day-site.md` gives for its own edits (the badge, the banner, the credit line and both privacy clauses). That file is written when the launch-day branch is reviewed, before L. Whatever it lists, the lines below show that three beta phrases and the pre-release lines are gone, that the banner and the store link are on the homepage, and that Apple's credit line and the campaign-label clause are up. If launch-day-site.md words the credit line or that clause differently, use its line instead. The early-access clause's wording is set there too, so its check comes only from that file; if the file doesn't exist yet or has no line for it, ask Claude for one before L.

If you ran the README block in this terminal, `check` is already defined and you can skip the next block.

```bash
check() { n=$(curl -sL "$1" | grep -c -- "$2"); if [ "$3" = present ]; then [ "$n" -gt 0 ]; else [ "$n" = 0 ]; fi && echo "ok   $1  $2" || echo "FAIL $1  $2 (on $n lines)"; }
```

```bash
for p in index how-it-works pricing nurseries community-garden faq about contact support privacy recommendations resources conservation; do check "https://plantadvocate.ai/$p.html" 'Get early access' absent; check "https://plantadvocate.ai/$p.html" 'Join the beta' absent; check "https://plantadvocate.ai/$p.html" 'in beta on iPhone' absent; done
```

```bash
check https://plantadvocate.ai/index.html 'Email us for early access' absent
```

```bash
check https://plantadvocate.ai/index.html 'write back when you can download' absent
```

```bash
check https://plantadvocate.ai/faq.html 'when you can download it' absent
```

```bash
check https://plantadvocate.ai/index.html 'apple-itunes-app' present
```

```bash
check https://plantadvocate.ai/index.html 'id6792203800' present
```

```bash
check https://plantadvocate.ai/index.html 'of Apple Inc' present
```

```bash
check https://plantadvocate.ai/privacy.html 'campaign label' present
```

The loop leaves out a press page, because `site/` has none today and Cloudflare answers a page that doesn't exist with the homepage, so an `absent` check on it would always pass. The draft on the launch-day branch, `fa4076b`, adds `press.html`. If the reviewed branch keeps it, add a `present` check for a line only that page has, from launch-day-site.md.

Run against the pre-launch site, some of these print FAIL, which is right for a site that still says "in beta". After the deploy every line should print `ok`. If a line says FAIL, list the deployments and look at the newest one's Environment, as the handoff's table says for step 3:

```bash
npx wrangler pages deployment list --project-name=PROJECT
```

If it reads Production, wait a minute for the cache and run the checks again. If the deploy itself is wrong, roll back while Claude fixes the branch: in the Cloudflare dashboard, open the project's Deployments, open the three-dot menu on the previous production deployment, and choose Rollback to this deployment ([Cloudflare, rollbacks](https://developers.cloudflare.com/pages/configuration/rollbacks/)).

Last, open https://plantadvocate.ai in Safari on your phone. The Smart App Banner should show at the top, offering Open if the app is installed. Apple's banner doesn't appear in the simulator and doesn't come back on a phone once dismissed, so use a private tab if you closed it before. Tap the App Store badge and check that it lands on the product page. Open https://plantadvocate.ai/privacy and read the top: the new date and the "What changed" line should both be there.

That finishes L. Send nothing in bulk today. The site's buttons carry the plain store link for now, because campaign links can't be made yet. The privacy clause about campaign labels goes up a day ahead of the labels themselves, which is the order `site/README-SITE.md` asks for: the policy changes before the thing it describes.

## L+1 and L+2

### Make the campaign links

In App Store Connect, open PlantAdvocate, click the Analytics tab, then Campaigns in the Acquisition section, then the add button (+) next to Campaigns. Apple says that button appears only once the app has analytics data, so keep checking once it has been live with downloads for at least 24 hours ([Apple, campaign links](https://developer.apple.com/help/app-store-connect-analytics/acquisition/campaign-links/)). The campaign name you type is the token. Make the five from [strategy.md](strategy.md#measurement-without-adding-trackers): `waitlist`, `site`, `outreach`, `ph` and `writeup`. `writeup` can wait until the piece exists, as [launch-kit/social.md](launch-kit/social.md) says. The first one also creates your provider token (`pt=`), which stays the same for all of them. Copy each link into a private note. Allow 15 to 20 minutes.

Apple shows a metric only once it reaches 5 in the chosen date range, and a campaign only after five people have downloaded through it for the first time, so most of these will show nothing for weeks. That is expected, and [strategy.md](strategy.md#measurement-without-adding-trackers) treats a token that never clears five as a channel that produced nothing.

If the button still hasn't appeared by L+3, send the waitlist email with the plain `https://apps.apple.com/app/id6792203800` rather than make the list wait any longer, as [launch-kit/waitlist-email.md](launch-kit/waitlist-email.md) says. That loses the measurement and keeps the promise.

### Send the waitlist email

This is the one launch email the July list can reasonably expect. The best record of what the July form promised is the homepage in commit `25f370f`, recovered from production on 19 July: "No spam. No card required. Just an update when the beta opens." The email is written as that update, and [launch-kit/waitlist-email.md](launch-kit/waitlist-email.md) says how to check the wording against a July deployment first. That file holds everything for it: the subject lines, the body, the footer, how to send, and how to handle removals. [strategy.md](strategy.md#at-launch) gives the reasons. Allow 2 to 3 hours the first time.

Six things have to be true before it goes, and waitlist-email.md lists them. In short: the July form's wording supports one update, as the git copy does, and no July deployment you could open says otherwise (the privacy policy's "only to tell you about PlantAdvocate" narrows what the list may be used for but doesn't widen what the form promised); there is a postal address that isn't your home, without which the email doesn't go; the privacy policy's early-access clause went live with the launch-day site deploy; the clean install passed and the care notes are fixed in production; you have the `waitlist` campaign link; and a test copy to yourself, opened on your iPhone, lands on the product page.

Send only to `send-list.txt` in `$HOME/PlantAdvocate-private`, which already leaves out the `.ca`, `.uk` and EU addresses the export check set aside in `set-aside.txt`. First run the fingerprint check in waitlist-email.md, which drops any address whose fingerprint is in `removed-hashes.txt`. Send from support@plantadvocate.ai as separate individual emails if there are a few dozen addresses. For more, use Buttondown or MailerLite with open and click tracking turned off, but only after the launch-day privacy edit names that service. The policy says it "names every company that receives any of your data", and its Data Sharing list has no mailing service. Ask Claude to add a line to that list on `claude/launch-day-site`, such as waitlist-email.md's "[SERVICE] sends our early-access email and holds that list's addresses only for that.", and to the early-access paragraph under This Website. A service the policy doesn't name gets none of the list. Never put the list in one To, CC or BCC line. Afterwards, every request to stop is a removal, honoured within 10 business days with the steps in waitlist-email.md's "Removals and replies": the address comes out of Cloudflare, the private folder and any mailing service, and only its fingerprint stays, in `removed-hashes.txt`. The reply address keeps working for at least 30 days, and nothing else in Cloudflare is deleted yet. Never add the address of anyone who signed in to the app to this list or any other, because the privacy policy says account information is used only to run the app.

### Reply to the people who emailed for early access

These are a separate group from the waitlist. The site told them "We'll write back when you can download PlantAdvocate", and the privacy policy uses an address from a message only to reply, so each gets an individual reply in their own thread and is never added to a list ([launch-playbook.md](research/launch-playbook.md)). Search the support inbox for the subject "Early access", which the site's mailto link filled in, and reply to each from L+1 to L+3. About 5 minutes each.

[launch-kit/waitlist-email.md](launch-kit/waitlist-email.md) says which paragraphs of the launch email make the reply. Leave out its list paragraph ("You're getting this email because..."), and use a short footer in place of the list's, because these people wrote to support and never joined the list. Use the `waitlist` link, because that token's question is how many of the people who asked went on to install, and these people asked too. Under your signature, put "If you'd rather not hear from PlantAdvocate again, reply and say so." and then "PlantAdvocate, [POSTAL ADDRESS]", as waitlist-email.md gives them. [launch-playbook.md](research/launch-playbook.md)'s safe reading is that a launch announcement is commercial email. CAN-SPAM then requires an opt-out notice and a postal address even when the person asked to hear from you; only the advertisement label can be dropped. Treat any request to stop as a removal, honoured within 10 business days: run waitlist-email.md's removal script on the address, so its fingerprint lands in `removed-hashes.txt` and it is never written to again.

### Give the site's buttons the `site` token

[strategy.md](strategy.md#channels) puts the `site` campaign link on every App Store button on plantadvocate.ai, while the Smart App Banner keeps only `app-id=6792203800`, because the syntax for tokens in a banner isn't confirmed. Give Claude the `site` link. It will make a small pull request that changes the buttons and nothing else. Then repeat the commands under [Merge the launch-day site branch](#merge-the-launch-day-site-branch), from `gh pr diff` to `gh run watch`, with the new pull request's number, and the deploy and checks under [Deploy the launch-day site](#deploy-the-launch-day-site) and [Check the site](#check-the-site). Add this line to the checks:

```bash
check https://plantadvocate.ai/index.html 'ct=site' present
```

Allow about 30 minutes. This merge also redeploys the backend with the same code, which restarts the machine for a minute or two. Do it outside the hours you expect people to arrive.

## What goes out, in the strategy's order

| When | What goes out | Link | Source |
|---|---|---|---|
| L | The launch-day site: badge, banner, credit line, both privacy clauses, and the press page with the [press release](launch-kit/press-release.md) and [fact sheet](launch-kit/fact-sheet.md) if the branch carries one | Plain store link | [strategy.md](strategy.md#channels); `launch-day-site.md`, written when `claude/launch-day-site` is reviewed |
| L+1 or L+2, L+3 at the latest | The waitlist email | `waitlist` | [launch-kit/waitlist-email.md](launch-kit/waitlist-email.md) |
| L+1 to L+3 | Individual replies to early-access emailers | `waitlist` | [launch-playbook.md](research/launch-playbook.md) |
| L+1 or L+2 | The site's buttons | `site` | [strategy.md](strategy.md#measurement-without-adding-trackers) |
| From L | A reply to every written review, within 2 business days | None | [strategy.md](strategy.md#what-113-can-do-without-a-prompt) |
| Once its gates are met | The pets custom product page, with the holiday line until the end of December | Its own plain URL | [strategy.md](strategy.md#the-pets-custom-product-page) |
| Late November | Promotional text: the feeding-rest line, through January | None | [strategy.md](strategy.md#the-promotional-text-calendar) |
| Optional, from L+2 | Personal-account posts P1 (L+2) and P2 (L+5) | `outreach`, or the plain store link until campaign links exist | [launch-kit/social.md](launch-kit/social.md) |
| Optional, first 30 days | One post in the r/iosapps monthly App Shelf megathread | `outreach` | [launch-kit/community-posts.md](launch-kit/community-posts.md) |
| Optional, decided by L+7 | Product Hunt, on a weekend between L+14 and L+21, or 9 and 10 January 2027 | `ph` | [launch-kit/community-posts.md](launch-kit/community-posts.md); [strategy.md](strategy.md#product-hunt-optionally) |

The first outreach wave is the people who asked: the waitlist and the early-access emailers. That is deliberate. [strategy.md](strategy.md#channels) holds the podcasts and editors in [targets.md](targets.md), whose drafts wait in [launch-kit/outreach-emails.md](launch-kit/outreach-emails.md), to March and April, when gardeners are listening, and after the three hazard-sentence changes due by the end of February have shipped; a note mentions ratings only as the store shows them on the day it is sent. It leaves the organizations out as a planned channel. It never uses Show HN for the app, and bans promotion in the plant, pet and home communities. So this runbook doesn't pull any of that into launch week. Two things can change it, both in [strategy.md](strategy.md#what-would-make-me-change-course). If the waitlist export was empty, or its consent can't support a launch note, Product Hunt and the r/iosapps post move from optional to worth doing, on L+7 to L+21. And if Apple features the app, the winter is no longer quiet, and the strategy says to ride it.

If you do post in r/iosapps, read the live sidebar first, because the rules in [channels.md](research/channels.md) come from archived copies. They require 10 karma earned in that community, one post per developer in 30 days, an App Store or TestFlight link only, and your relationship disclosed in the comments. The community bans generative-AI and AI-wrapped apps. PlantAdvocate's care advice comes from fixed rules, but on iPhone models with Apple Intelligence it uses Apple's on-device AI to suggest photo matches and to word the Gnome's lines. Say so plainly in the post, as the draft's last paragraph does. If the live rules or the moderators count that as a generative-AI app, don't post. If you're unsure, ask the moderators through modmail before posting. Karma can't honestly be rushed, so this is only for someone who already takes part there.

## Every day from L to L+7

About 15 to 20 minutes a day, plus the replies. Install Apple's App Store Connect app on your iPhone, which sends push notifications for new customer reviews and status changes and lets you reply from the phone ([Apple](https://developer.apple.com/help/app-store-connect/get-started/app-store-connect-for-iphone-and-ipad/)).

### Reviews, and Apple's rules for replying

[strategy.md](strategy.md#what-113-can-do-without-a-prompt) makes review replies the one ratings lever 1.1.3 has: reply to every written review within the published "usually within 2 business days". When you reply, Apple notifies the reviewer, who can then update the review ([Apple, ratings, reviews and responses](https://developer.apple.com/app-store/ratings-and-reviews/)).

Apple's rules, from the pages read on 2026-10-24:

1. Guideline 5.6.1 says to treat customers with respect when responding, to keep a response targeted to the person's comments, and to include no personal information, spam or marketing ([App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/)).
2. Apple's ratings page asks for a concise reply that clearly addresses the feedback, in a friendly tone consistent with the brand, personalized rather than one generic text for similar reviews ([Apple](https://developer.apple.com/app-store/ratings-and-reviews/)).
3. If a reviewer reports a downloading error or a billing issue, Apple says to direct them to Apple Support. PlantAdvocate sells nothing, so a billing complaint is most likely about another app.
4. A review with offensive material, spam or other content that breaks Apple's terms gets Report a Concern in App Store Connect, not a reply. The reviewer isn't told.
5. Only someone with the Account Holder, Admin or Customer Support role can reply. In App Store Connect, open Apps, then PlantAdvocate, then Ratings and Reviews in the sidebar, choose the platform, find the review and click Reply. A reply can take up to 24 hours to appear, and shows as pending until then. Each review shows one response. You can edit or delete it at any time; an edited reply is marked as edited, the reply stays public even if the reviewer changes the review, and several quick edits send the reviewer only one notification ([Apple, respond to reviews](https://developer.apple.com/help/app-store-connect/monitor-ratings-and-reviews/respond-to-reviews), [overview](https://developer.apple.com/help/app-store-connect/monitor-ratings-and-reviews/ratings-and-reviews-overview)).
6. Everything is public. Write every reply for the next reader as much as for the reviewer.
7. A rating may be quoted in marketing only while it is the app's current rating, and a review only with its writer's permission ([Apple](https://developer.apple.com/app-store/ratings-and-reviews/)). Until the store shows ratings, quote none ([product-truth.md](product-truth.md)).

The house rules come from [strategy.md](strategy.md#what-113-can-do-without-a-prompt) and [product-truth.md](product-truth.md). Use the caretaker voice. Thank the person, say what was fixed or what the app can't check, and stop. Never argue, promise a feature or a date, or soften a hazard. Never give medical or veterinary advice: where someone fears a person or pet has eaten a plant, point to Poison Control (US 1-800-222-1222) or a vet, as the app does. Don't ask anyone to raise their rating; telling them what changed is enough, and the notification does the rest. The reply bank in [launch-kit/community-posts.md](launch-kit/community-posts.md#reply-bank) answers the likeliest questions from the truth sheet, and its answers make good review replies once they're trimmed to what the review actually says.

The complaints to expect are known from [competitors.md](research/competitors.md) and [strategy.md](strategy.md#in-the-store). For the sign-in wall, say why there is an account (the garden follows you to a new phone), that it is Apple or Google with no password, and where deletion is. For a missing plant, say the catalog covers more than 990 researched species and that you've noted the request, with no date. For a plant with no reminders, say that reminders follow the check schedules PlantAdvocate wrote for 129 common plants, which are not cited, and that the Checks for today card says when a plant is left out. For "it wouldn't tell me if it's safe for my cat", explain that a missing record is never treated as safe, and suggest a vet. For no photo button, say Take photo and Choose photo appear only on iPhones where Apple Intelligence is available and turned on (iOS 26 or later on an iPhone that supports it), and that search works on every iPhone. For a slow first screen, say what happened and what changed, if anything did. For a wrong fact, thank them, check it against the source, and follow [If something breaks in launch week](#if-something-breaks-in-launch-week).

In App Store Connect, click your name at the top right, then Edit Profile, and under Notifications turn on Developer Response, which emails you when someone edits a review you've answered, along with App Status Reports, App Store Featuring and the App Analytics Weekly Email Summary ([Apple, user notifications](https://developer.apple.com/help/app-store-connect/reference/account-management/user-notifications)).

### The support inbox

Reply to everything at support@plantadvocate.ai within the same "usually within 2 business days", and never promise faster. Keep a private tally of messages by theme, which feeds the L+7 read. A request to delete an account gets the in-app path, Settings > Account > Delete account, which erases the account with its plants, care logs and growing areas and, for an account made with Sign in with Apple, also asks Apple to revoke the sign-in. As the privacy policy and the support page promise, it also gets the offer to do it for them. If they would rather you did it, or can't sign in, first make sure the request comes from the account's owner. An account may hold only a private relay address from Apple, or no address at all, so work out with Claude how to confirm that, and the operator steps, since the backend has no tool for it yet. Don't paste their address into the session. Reply when it's done. A request for a copy of their data, or for a correction, is a right the policy gives wherever they live; acknowledge it within the same 2 business days and handle it the same way. A request to leave the waitlist is a removal, done as above. A question about whether a plant is safe gets the same answer as in a review: the app repeats what its sources publish, it isn't medical or veterinary advice, and Poison Control or a vet is who to call. A report of a wrong fact is a correction, below.

Watch, too, for an email from Apple's featuring team asking for artwork. [strategy.md](strategy.md#what-would-make-me-change-course) says to drop everything else and supply it. Keep the icon's source file and both screenshot sets where you can find them within a day.

### The backend

```bash
curl -s --max-time 30 https://garden-gnome-api.fly.dev/
```

Look for `"synced": true`.

```bash
fly logs -a garden-gnome-api --no-tail | grep -c Traceback
```

Look for `0`. Any other number means something raised an error in the buffered log. Print just the tracebacks:

```bash
fly logs -a garden-gnome-api --no-tail | grep -A 40 Traceback
```

Before you bring one to Claude, replace any network address, plant nickname or place name in it with a placeholder. The privacy policy says these logs can hold them, and it names Anthropic as a recipient only once photo check-ups or questions are switched on. Production's database is not mined for marketing numbers, such as sign-up counts, because the policy says account information is used only to run the app ([strategy.md](strategy.md#measurement-without-adding-trackers)). App Analytics is where the numbers come from.

### App Analytics

Open App Store Connect's Analytics tab and look at impressions, product page views, downloads, conversion and downloads by source (App Store Search, Browse, web referrers). In the first days the figures will be tiny or empty, and every campaign token will sit under Apple's floor of 5. Don't act on any of it this week. Usage, retention and crash figures count only the people who agreed to share diagnostics with developers, and the peer group benchmarks, crash rate among them, come in weekly intervals ([Apple, App Analytics](https://developer.apple.com/app-store/app-analytics/)). The first checkpoint that decides anything is L+14. From the first Monday after L, switch to the 15-minute weekly read in [strategy.md](strategy.md#the-weekly-read-and-the-checkpoints).

## If something breaks in launch week

If sign-in fails for new accounts, growing areas won't load, or a screen says it couldn't reach the server, check the backend first with the commands above, then `fly status -a garden-gnome-api`. Hold the waitlist email if it hasn't gone, and bring the output to Claude. A fix on the server ships through a pull request to master, which deploys on its own, with no new build.

A fix inside the app needs a new build on EAS with the pinned image, never a build from this Mac ([docs/2026-10-24-ios27-scene-lifecycle.md](../2026-10-24-ios27-scene-lifecycle.md)), and a new version number above 1.1.3. If that build happens, it effectively becomes the December build in [strategy.md](strategy.md#the-one-move-a-ratings-prompt-in-the-build-apple-already-requires), and the scene-adopted build moves up one version, as the strategy already allows. For a critical bug, Apple accepts a request for an expedited review that includes the steps to reproduce it on the current version ([Apple, App Review](https://developer.apple.com/distribute/app-review/)).

If anyone reports a wrong or overstated hazard statement, follow [strategy.md](strategy.md#accuracy-and-hazards): pause every hazard-led line and the pets page, fix the value in the catalog and in production, re-check other values that rest on the same source page, and log the correction before resuming. The public corrections log the strategy describes starts with the first confirmed correction.

If something is badly wrong and can't wait for a fix, Pricing and Availability in App Store Connect has Remove App From Sale at the bottom of the page, and Apple removes the app within 24 hours. It is a last resort; talk it through with Claude first.

## L+7: the first-week read

Allow about 45 minutes. Write down the first-time downloads and their sources, the US ratings count and average, the written reviews and whether each has a reply, the support tally by theme, any backend tracebacks, and anything the clean install or the first users hit.

Then decide five things. Put `min_machines_running` back to 0 if you kept it at 1, with a one-line PR Claude writes. Decide whether to do Product Hunt at all, and if so schedule it now for a weekend between L+14 and L+21 at 12:01 am Pacific, or for 9 and 10 January 2027 if L+14 falls after Sunday 13 December ([strategy.md](strategy.md#product-hunt-optionally)). Decide whether to post in r/iosapps this month. Note where the pets page's three gates stand. And note whether anything the first users hit needs a fix build, which feeds the L+14 decision below.

## The pre-launch checklist

Everything in this table has to be true before you press Release. Most of it comes before you press Submit, because the subtitle, keywords and screenshots can change only with a new version.

| What must be true | How you can tell | Where it is set out |
|---|---|---|
| The nine decisions at the top of the handoff are answered | You've told Claude yes or no to each | [Handoff, "Decide these first"](../2026-10-16-app-store-finish-line-handoff.md#decide-these-first) |
| The waitlist is exported, before the step 3 deploy | The export, `send-list.txt`, `set-aside.txt`, `check-by-eye.txt` and the two empty files `removed-hashes.txt` and `later-releases.txt` sit in `$HOME/PlantAdvocate-private`, outside the repository, and the export check has run | [launch-kit/waitlist-email.md](launch-kit/waitlist-email.md); [strategy.md](strategy.md#before-the-site-deploy) |
| The July form's wording is checked | You've read the git copy in commit `25f370f` ("Just an update when the beta opens") and compared it with a July deployment if one could be opened, and it supports one update | [launch-kit/waitlist-email.md](launch-kit/waitlist-email.md) |
| PR #22 merged, and the backend deployed to Fly | Step 2's checks pass, among them `34 True` and a catalog block with `"synced": true` | Handoff, steps 1 and 2 |
| The 33 care notes are rewritten, and the six that contradict their cited record corrected, in the JSON and in production's rows | No species page calls a plant "Pet-safe", "harmless" or "safe for most pets", and no care note states a hazard its cited record contradicts (Sage, Thyme, Baby's Breath, Hollyhock, China Aster, Moonflower) | [strategy.md](strategy.md#the-pet-safe-care-notes-before-release); this file, [Approval day](#four-things-to-check-before-you-release) |
| The encoding fix is in production's rows, and the °F fix is in the build | Boston Fern and Dumb Cane read cleanly; Snake Plant reads "60–85°F" | [strategy.md](strategy.md#the-pet-safe-care-notes-before-release) |
| The pre-launch site is deployed, with the five copy fixes | The step 3 check block prints `ok` on every line | Handoff, step 3; [strategy.md](strategy.md#the-site-riding-along-with-step-3) |
| The desktop site generator has not been run | Nobody has run `build.py` | [site/README-SITE.md](../../site/README-SITE.md) |
| The App Launch nomination is filed in the week of 26 October. If App Store Connect refused it before approval, it is ready to file on approval day, with the range starting at least three weeks out | It shows as submitted in Featuring, with a range starting about two weeks after the expected release | [strategy.md](strategy.md#featuring-nominations) |
| Step zero is pasted: subtitle "Plants that suit each spot" and the 97-character keyword field, or the fallback field if the long name was refused | The version page shows them before Submit | [strategy.md](strategy.md#step-zero-the-product-page-before-you-press-submit) |
| Screenshots uploaded at both sizes, in the order 01, 04, 06, 02, 03, 05, 07, 08 | The version page shows that order, and [CHECK.md](../screenshots/1.1.3/CHECK.md) reports every file passing on the day you upload | [strategy.md](strategy.md#step-zero-the-product-page-before-you-press-submit); [docs/screenshots/1.1.3/](../screenshots/1.1.3/README.md) |
| Availability is the United States only, release is manual, and there is no pre-order | Pricing and Availability, and the version page's release section | [strategy.md](strategy.md#step-zero-the-product-page-before-you-press-submit) |
| TestFlight phone checks done | Each of step 5's twelve items noted | Handoff, step 5 |
| A postal address that isn't your home | A USPS box, or a private mailbox registered with a commercial mail receiving agency | [strategy.md](strategy.md#before-the-site-deploy) |
| The launch-day site branch is reviewed, ready and unmerged | Claude has reviewed and finished `claude/launch-day-site` (its draft, `fa4076b`, is unreviewed), written `launch-day-site.md`, pushed the branch and opened its pull request; the diff holds the badge, banner, credit line, both privacy clauses with one new effective date and "What changed" line, and the updated check line; its links check clean; nothing from it is deployed | `launch-day-site.md`, written in that review |
| The campaign tokens are chosen, not made | You know the five tokens and where each goes. Apple won't let a link be made until the app has been live with downloads for about 24 hours, so the links themselves are an L+1 job | [strategy.md](strategy.md#measurement-without-adding-trackers) |
| The waitlist email is ready to send | A subject is picked, the body is filled in except the link, and the sending route is chosen: individual emails, or a service with tracking off, plantadvocate.ai verified, and its name in the launch-day privacy edit | [launch-kit/waitlist-email.md](launch-kit/waitlist-email.md) |
| The early-access emailers are found | An inbox label or folder holding the messages with the subject "Early access", and at most a count of them in a note in `$HOME/PlantAdvocate-private`. No address from them goes into the repository, a doc or a Claude session | [launch-playbook.md](research/launch-playbook.md) |
| The inboxes are watched | App Store Connect notifications are on, the App Store Connect app is on your phone, and whoever holds the Admin, App Manager or Marketing role reads that email for featuring requests | [strategy.md](strategy.md#featuring-nominations) |
| A clean-install phone is ready | You can delete the TestFlight build, and ideally you have a spare Apple ID that has never used PlantAdvocate | This file, L |
| The replies to App Review are at hand | You know where [review-replies.md](../app-store/review-replies.md) is | [docs/app-store/review-replies.md](../app-store/review-replies.md) |
| The days are blocked | Release morning, L+1 and L+2, and 15 to 20 minutes on each day to L+7 | This file |

## The first 30 days

| When | What | Your time (my estimate) | Source |
|---|---|---|---|
| Every Monday | The weekly read: impressions, conversion against the peer group's median, first-time downloads, sources and campaigns; the US ratings count and average; reply to anything new; one private line of numbers and the support tally | About 15 minutes | [strategy.md](strategy.md#the-weekly-read-and-the-checkpoints) |
| From L, within 2 business days | A reply to every written review | 5 to 10 minutes each | [strategy.md](strategy.md#what-113-can-do-without-a-prompt) |
| Once its gates are met | The pets custom product page: shots 06, 03 and 04 first, the holiday line, and the keywords "toxic", "pets", "cat", "dog" and "poison". The gates are the care notes fixed in production, the poinsettia, English and American holly and American mistletoe pages read against their sources (and none resting on a Missouri Botanical Garden-only harm-capable value), and the Pothos sentence read against NC State's page. No lilies in its copy. It needs its own App Review | 1 to 2 hours, plus the reading | [strategy.md](strategy.md#the-pets-custom-product-page) |
| Late November | Promotional text on the default page changes to the feeding-rest line, which stays through January | 5 minutes | [strategy.md](strategy.md#the-promotional-text-calendar) |
| L+14 | The first real checkpoint: crash rate against the peer benchmark, support themes, and whether sign-in and growing areas work for real people. It decides whether a December build is worth it. The test is that L came by about 15 November and the first two weeks were clean; if so, the build carries the ratings prompt, the Settings row and fixes, and goes in by Friday 11 December | About 30 minutes | [strategy.md](strategy.md#the-one-move-a-ratings-prompt-in-the-build-apple-already-requires) |
| L+14 to L+21, if chosen | Product Hunt, once, from your personal maker account, asking for feedback only, with the fields and maker's comment in [launch-kit/community-posts.md](launch-kit/community-posts.md) | About 6 hours around the day | [strategy.md](strategy.md#product-hunt-optionally) |
| Within the first 30 days, if chosen | One post in the r/iosapps App Shelf megathread | About 30 minutes | [channels.md](research/channels.md) |
| L+30 | Read every campaign token and App Analytics source for the month, and decide what to repeat. Every removal from the waitlist should be done by now, each leaving only its fingerprint in `removed-hashes.txt`. The list itself is kept for at most one spring note, and whether to delete it is decided by 30 June 2027 | About 30 minutes | [launch-playbook.md](research/launch-playbook.md); [launch-kit/waitlist-email.md](launch-kit/waitlist-email.md) |

## The winter

| When | What | Your time (my estimate) | Source |
|---|---|---|---|
| Fri 11 December 2026 | The last day to submit a December build, if L+14 said yes | About 4 to 6 hours of builds and phone checks | [strategy.md](strategy.md#the-one-move-a-ratings-prompt-in-the-build-apple-already-requires) |
| About 20 December to 3 January | Hands off. The last holiday notice found, Apple's from December 2024, said reviews may take longer from 20 to 26 December. No 2026 notice had been found by 24 October, so check Apple's developer news in early December before you plan around it | Replies only | [strategy.md](strategy.md#timeline-2026-10-24-to-june-2027); [aso.md](research/aso.md) |
| End of December | The pets page's holiday line gives way to the January line | 5 minutes | [strategy.md](strategy.md#the-promotional-text-calendar) |
| January | The scene-adopted 1.1.4 (1.1.5 if a December build shipped) is built: scene life cycle, the Xcode 27 image, the ratings prompt and Settings row, the not-advice line under hazard sentences, and a "Report a fact" link. Optionally, the lily of the valley proposal to The American Gardener | About a day of phone checks, plus 3 to 4 hours for the proposal | [strategy.md](strategy.md#in-the-app-with-114), [the ratings plan](strategy.md#the-prompt-in-114-and-the-rules) |
| Fri 15 January 2027 | The spring nomination, only if a build or the catalog brings something new; otherwise skip it | About an hour | [strategy.md](strategy.md#featuring-nominations) |
| 31 January | The winter checkpoint: ratings count and average, downloads from December into January. If downloads are only a few dozen, the strategy pulls the optional outreach and the Apple Ads test forward | About 30 minutes | [strategy.md](strategy.md#the-weekly-read-and-the-checkpoints) |
| About 1 February | Submit the scene-adopted build. The end of March is the latest safe approval date, because from April 2027 every upload has to be built with the iOS 27 SDK | Builds and phone checks | [docs/2026-10-24-ios27-scene-lifecycle.md](../2026-10-24-ios27-scene-lifecycle.md) |
| February | Promotional text moves to the repot line. Check the 2027 dates of Poison Prevention Week | 15 minutes | [strategy.md](strategy.md#the-promotional-text-calendar) |
| By the end of February | The three backend changes to the hazard sentences ship: "or your local poison centre", the pet verdict's source named in the sentence, and the table clauses cited or labelled. Then decide on the Apple Ads test, a second custom page, and whether spring gets about 2 hours a week or the store-only version | About an hour for the decisions | [strategy.md](strategy.md#the-hazard-sentences-before-the-spring-hazard-lines), [checkpoints](strategy.md#the-weekly-read-and-the-checkpoints) |

Through all of it, three thresholds from [strategy.md](strategy.md#the-weekly-read-and-the-checkpoints) can change what happens next. If conversion sits below the peer group's median for four weeks in a row, change the screenshots or the promotional text before spending anything or pushing anywhere. If the US average is below 4.0 after the first 20 ratings, stop every push, read the reviews, and fix what they say in the next version. And if a featuring email arrives, drop everything else and supply the artwork.

## Pages read for this file

Beyond the repository and the files linked above, these Apple pages were read on 2026-10-24, raw where they allowed it: [ratings, reviews and responses](https://developer.apple.com/app-store/ratings-and-reviews/); the [App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/), for 5.6.1; App Store Connect help on [selecting a release option and releasing manually](https://developer.apple.com/help/app-store-connect/manage-your-apps-availability/select-an-app-store-version-release-option), [responding to reviews](https://developer.apple.com/help/app-store-connect/monitor-ratings-and-reviews/respond-to-reviews), the [ratings and reviews overview](https://developer.apple.com/help/app-store-connect/monitor-ratings-and-reviews/ratings-and-reviews-overview), [viewing reviews and reporting a concern](https://developer.apple.com/help/app-store-connect/monitor-ratings-and-reviews/view-ratings-and-reviews), [user notifications](https://developer.apple.com/help/app-store-connect/reference/account-management/user-notifications) and [the App Store Connect app](https://developer.apple.com/help/app-store-connect/get-started/app-store-connect-for-iphone-and-ipad/); [campaign links](https://developer.apple.com/help/app-store-connect-analytics/acquisition/campaign-links/); [App Analytics](https://developer.apple.com/app-store/app-analytics/); and [App Review](https://developer.apple.com/distribute/app-review/), for expedited reviews. Cloudflare's [rollbacks page](https://developers.cloudflare.com/pages/configuration/rollbacks/) was read through a summarising fetch. Remove App From Sale was confirmed only through a search summary of Apple's [availability help page](https://developer.apple.com/help/app-store-connect/manage-your-apps-availability/manage-availability-for-your-app-on-the-app-store/), not read raw. The iTunes Lookup API was called for 6792203800 (no result, in the US) and for a live app, to confirm the fields the lookup command prints, and both store URLs for 6792203800 answered 404.
