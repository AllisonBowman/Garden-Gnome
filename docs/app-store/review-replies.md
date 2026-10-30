# Prepared replies to App Review for 1.1.3

These are replies to paste into App Store Connect if App Review rejects 1.1.3
or asks a question. They cover the risks in the table in
`docs/go-to-market/research/review-risk.md` that a reply can answer: 2.1(a)
for sign-in and for a server that didn't answer, 5.1.1(v) for the login wall
and for account deletion, 2.3 with 2.5.19 inside it, 1.4.1 for the hazard
notes, and 4.8, which review-risk.md rates least likely but costs nothing to
have ready. Minimum functionality (4.2 and 4.3(b)) has no prepared reply.
Each one is true of 1.1.3 at `3f6d7da`, checked on 24 October 2026 against
the code and `docs/go-to-market/product-truth.md`, except that the 1.4.1
reply and the 2.3 quote were brought up to the 2026-10-30 changes (the
not-advice line in the app, and "temperature" in the description). Each section says what to
check first, because a reply that says something works has to be true when
the reviewer reads it.

Read App Review's message twice and answer what it actually says. A reply
that answers a different question costs another day. Replace every bracket,
and delete any bracketed sentence you can't make true. Never send a personal
Google login, and never offer a demo account, because there isn't one.

## Where to reply

In App Store Connect, open Apps > PlantAdvocate and click the link at the top
of the page that says there are unresolved issues. Click Resolve next to the
submission, then Reply to App Review. Paste the reply, add a screenshot with
Attach File if it helps, and click Reply ([Apple's
steps](https://developer.apple.com/help/app-store-connect/manage-submissions-to-app-review/reply-to-app-review-messages)).
Older forum posts call this page the Resolution Center.

Reply first, and resubmit only when the fix needs it. When the status reads
Metadata Rejected, Apple says to edit the metadata and reply ([status
reference](https://developer.apple.com/help/app-store-connect/reference/app-and-submission-statuses)),
and that the same build can be resubmitted once a metadata issue is resolved
(the reply page above). A crash or other fault in the build itself needs a
new build. If a reply doesn't settle it, Apple allows one appeal per rejected
app to the [App Review
Board](https://developer.apple.com/help/app-review/after-submitting-for-review/appeal-to-the-app-review-board/).
Keep that for a disagreement about a rule, not a misunderstanding a reply can
clear up.

## 2.1(a): the reviewer couldn't get in, or asked for a demo account

The message may be headed Guideline 2.1 - Information Needed and ask for demo
account credentials, or Guideline 2.1(a) and say sign-in failed. Either way,
first make sure the way in works today.

Check that production is serving 1.1.3:

```bash
curl -s --max-time 30 https://garden-gnome-api.fly.dev/
```

Look for a `catalog` block with `"synced": true`. If there is no catalog
block, production is still the old code, every step in the notes fails, and
the server has to be deployed (handoff step 2) before any reply. Both the old
and the new server say version `0.2.0`, so the version doesn't tell them
apart.

```bash
curl -s https://garden-gnome-api.fly.dev/openapi.json | python3 -c "import json,sys; p=json.load(sys.stdin)['paths']; print(len(p), any(k.startswith('/growing-areas') for k in p))"
```

Look for `34 True`.

Then, on the 1.1.3 version page under App Review Information, check that
Sign-in required is ticked and the Notes are pasted whole: they start with
ABOUT THE APP and end with the CONTACT line. Then, on the TestFlight build
with the same build number, sign in with Sign in with Apple, ideally with an
Apple ID that has never used PlantAdvocate, since that is the reviewer's
path. If App Review's screenshot shows Apple's own sign-in sheet failing,
before PlantAdvocate says anything, look at
https://developer.apple.com/system-status/ and say in the reply what you
found. review-risk.md records two 2026 rejections where Sign in with Apple
failed on Apple's side.

```text
Hello, and thank you for reviewing PlantAdvocate.

PlantAdvocate has no username or password, so there is no demo account to give. Sign in with Apple makes an account for whoever taps it, so please use your own Apple ID:

1. Open the app. The first screen is the sign-in screen, which says that signing in creates your account.
2. Tap Sign in with Apple and confirm with your Apple ID.
3. The app creates a new account at once, with one empty indoor growing area called My Home, and shows 4 short welcome cards. Tap Skip to close them.
4. You land on the Plants tab, which says "Your garden's empty". The Notes for Review give a one-minute path through each feature, starting with Growing areas > New growing area.

Sign in with Google works too. To remove the account afterwards: Settings tab > Account > Delete account > Delete forever.

[Keep this sentence only if you did it.] We signed in with Sign in with Apple and went through each step in the Notes on [DATE] with build [NUMBER]. If sign-in still fails, a screenshot of the message would help us find the cause quickly, and we're glad to take a call at +1 [PHONE].

Thank you,
Allison Bowman
```

Every line of that is in the code: the login sentence in
`mobile/src/auth/loginCopy.ts`, the account and My Home in
`garden-gnome/app/routers/auth.py` (`_sign_in`), the four cards with Skip in
`mobile/src/onboarding/`, shown once to an account with no plants
(`mobile/App.tsx:222-241`), and the empty Plants tab in
`mobile/src/screens/PlantsScreen.tsx:133`.

## 5.1.1(v): sign-in before features that aren't account-based

The message is likely to say the app requires people to register or log in
to reach features that are not account-based, and the likeliest target is
the Species tab and its Almanac. That point has some truth in it: the
catalog doesn't need an account to be read. Every species route wants a
signed-in caller as a default, so that a new route can't ship open
(`garden-gnome/app/routers/species.py:21-30`), not because a read needs one.
So the reply says what is account-based and how the catalog uses the account,
and never says the catalog can't be shown without sign-in.

Decide one thing before replying: whether to offer the signed-out catalog.
review-risk.md costs it at about half a day on the backend (open `GET
/species/` and `GET /species/{id}`, with rate limits) and one to three days in
the app (a signed-out screen stack and a Browse door on the sign-in screen),
then a new build. Nothing in App Store Connect needs changing for this reply.
If App Review repeats the rejection after it, that work is the fix, unless you
would rather spend the one appeal.

```text
Hello, and thank you for reviewing PlantAdvocate.

PlantAdvocate is built around each person's own account. What someone records in the app is kept with their account on our server, so it follows them to a new phone, and the sign-in screen says so before anyone signs in. The account-based features are the growing areas (each place the person grows, with its size, light, shelter and location), the plants in each area and their care log, the checks that come due from that log and the reminders that follow them, Walk the garden (which adds a typed or spoken list of plants to the account), care advice built from a species' facts and that plant's own care log, the opt-in community census, and deleting the account.

The Species tab and its Almanac are the reference catalog those features draw on, and the Almanac works from the account: it marks the species the person already keeps, and narrows the catalog to what fits one of their own growing areas, using the fit our server works out for that area. A species opened from a growing area shows how it suits that area. Add plant and Walk the garden search the same catalog to add plants to the account.

[Keep this paragraph only if you are ready to build it.] If you would like the plain species list to be readable before sign-in, we will add that in a new build, with a way to browse the catalog from the sign-in screen.

Thank you,
Allison Bowman
```

The Almanac's reads are in `mobile/src/screens/AlmanacScreen.tsx:116-126`
(the person's plants and growing areas) and `:149` (the server's candidates
for one area), and a species page reads the area it was opened from
(`SpeciesDetailScreen.tsx:44-52`). If you do build the door, write that reply
then, against what the new build actually does: which build, what changed,
and where the reviewer finds it.

If the 5.1.1(v) message is about account deletion instead, this is the reply.
Nothing needs changing first; the path is in the build
(`mobile/src/screens/SettingsScreen.tsx:94-101, 220`;
`garden-gnome/app/routers/auth.py`, `delete_me`).

```text
Hello, and thank you for reviewing PlantAdvocate.

Account deletion is in the app: Settings tab > Account > Delete account, then Delete forever in the confirmation. It permanently deletes the account and its plants, care history and growing areas from our server, and asks Apple to revoke the Sign in with Apple grant. If Apple doesn't answer at once, our server retries the revoke later. Deleting needs no website, email or call.

Thank you,
Allison Bowman
```

## 4.8: login services

This would say the app uses a third-party login such as Google Sign-In
without an equivalent option. PlantAdvocate offers Sign in with Apple first,
above Sign in with Google, on its only sign-in screen
(`mobile/src/auth/LoginScreen.tsx:67-100`), and asks Apple only for the
person's name and email (`mobile/src/auth/signIn.ts:45-49`). So the likeliest
cause is a reviewer who didn't see the Apple button.

Before replying, open the TestFlight build with the submitted build number,
sign out if you need to, and take a screenshot of the sign-in screen showing
both buttons. If the Apple button is missing on your phone, don't reply: the
build has a bug, and the fix is a new build. Nothing in App Store Connect
needs changing.

```text
Hello, and thank you for reviewing PlantAdvocate.

PlantAdvocate's only sign-in screen offers Sign in with Apple first, above Sign in with Google, and there is no other way to sign in. With Sign in with Apple the app asks only for the person's name and email address, and the person can hide their email address as Sign in with Apple allows. PlantAdvocate has no ads and no tracking, and collects nothing for advertising. A screenshot of the sign-in screen from build [NUMBER] is attached.

Thank you,
Allison Bowman
```

## 2.3: metadata that doesn't match the app

Guideline 2.3 covers the description, screenshots, privacy answers and age
rating, so the reply depends on what the message names. Open the field it
names, compare it with the app on the TestFlight build and with its file in
`docs/app-store/`, and decide which one is wrong. If the metadata is wrong,
edit it in App Store Connect, reply saying what you changed, and resubmit the
same build. If the metadata is right and the reviewer couldn't find
something, change nothing and reply with the path. These paragraphs answer
the likeliest questions; paste the one that fits between a greeting and your
name.

If the reviewer couldn't find photo matching. First check that the
description in App Store Connect is the `listing.md` text, which limits the
feature to iPhones with Apple Intelligence.

```text
Add plant shows Take photo and Choose photo only on iPhones where Apple Intelligence is available and turned on, which needs iOS 26 or later on an iPhone that supports it. The description says so: "On iPhones with Apple Intelligence, Add plant can also suggest likely matches from a photo." On other iPhones the two buttons are absent by design, and species search works on every iPhone. The photo is read on the phone and never uploaded.
```

If the reviewer couldn't see the Checks for today card from screenshot 4. It
can't appear on a brand-new account the same day, so this is a timing
question, not a fault.

```text
The Checks for today card on the Plants tab lists a plant when its care window comes due, counted from the last time that care was logged, or from the day the plant was added. So on a new account it can appear the next day at the earliest, and only for species that have a check schedule. Step 3 of the Notes shows it: log Watered on Basil, whose window is 1 to 2 days, and its check appears on the card the next day, with Watered and Still damp to tap.
```

If the question is about the claim that facts are cited. The description
says "Each species page shows facts such as light, water, soil, temperature
and size, and lists where they came from" and "Anything not yet cited says
so" (`listing.md:101`).

```text
Care facts that come from a source are cited on each species page, in a Sources card whose rows open the source's own page. Older imported values that no source backs yet are grouped under "From the catalog — not yet cited", and the description says that anything not yet cited says so. The check schedules for 129 common plants were written by PlantAdvocate, and the description says those are not cited either.
```

If the message points at features in the build that the app doesn't show,
under the hidden-features rule (2.5.19, which moved there from 2.3.1 on
October 16). Keep the last sentence only as a promise you mean to keep;
review-risk.md recommends it as a rule anyway.

```text
Photo check-ups of an ailing plant and reading typed symptoms are in the build but switched off. The app asks our server which of these are ready and shows neither while the server says no, as it does now. The Notes for Review say so. We will not switch either on without first submitting an update that describes it.
```

If the question is about the privacy answers or the age rating, there is no
prepared paragraph, because the answer depends on the question. Compare what
App Store Connect shows with `app-privacy.md` or `age-rating.md`, fix
whichever is wrong, and say in the reply what you changed.

## 1.4.1: the hazard notes read as medical content

Guideline 1.4.1 is written for medical apps that could give inaccurate data
or be used to diagnose or treat, and asks them to remind users to check with
a doctor. PlantAdvocate isn't one, but a species page says what a source
records a plant can do to people or pets, so a reviewer could ask about it.
Know one thing first. When review-risk.md was written, the listing and the
Notes said the hazard notes are not medical or veterinary advice, but no
screen in the app did. Since the 2026-10-30 changes, 1.1.3 shows "These
notes repeat what the sources publish. They are not medical or veterinary
advice." under each hazard note, on species pages, plant pages and Add plant
(`mobile/src/care/notAdvice.ts`). Before you send the reply below, open
Pothos in the build under review and check that the line is there. If it
isn't, the build predates those changes: cut ", and the app shows that same
line under each hazard note" from the reply, and bring the message to
Claude.

```text
Hello, and thank you for reviewing PlantAdvocate.

PlantAdvocate is a plant-care app, not a medical one. It doesn't diagnose, triage or suggest treatment for people or animals. Where a published source records a plant as harmful to people or pets, the species page repeats what that source says, and the page lists its sources. Where people are at risk, the note ends by telling the reader to call Poison Control (US 1-800-222-1222) right away if they suspect poisoning, or a vet where the source names animals. Where no source has a record, the page says so and says that is not a guarantee of safety; it never calls a plant safe. The App Store description says these notes repeat what the sources publish and are not medical or veterinary advice, and the app shows that same line under each hazard note.

Thank you,
Allison Bowman
```

The wording is in `garden-gnome/app/services/toxicity.py`: the Poison
Control line at `:73` and `:800-803`, the no-record sentences at
`:843-860`. The app's line is `NOT_ADVICE_LINE` in
`mobile/src/care/notAdvice.ts`, and the description's sentence is in the
HAZARDS, STATED PLAINLY paragraph of `docs/app-store/listing.md`.
If the question is the 4+ rating instead, compare App Store Connect with
`docs/app-store/age-rating.md`, which answers Medical or Treatment
Information with None, and reply with what you changed, if anything.

## 2.1: the app showed an error, or the server didn't answer

The message would quote or show an error, most likely "PlantAdvocate couldn't
reach the server just now." (`mobile/src/care/loadFailed.ts:23`) on a screen,
or "Sign-in didn't complete. Please try again." on the sign-in screen
(`mobile/src/auth/LoginScreen.tsx:42`). Both mean the app got no answer in
time: it waits 15 seconds for a screen and 20 for sign-in
(`mobile/src/api/client.ts:122`, `mobile/src/auth/signIn.ts:23`). Find out
why before replying.

```bash
curl -s --max-time 30 https://garden-gnome-api.fly.dev/
```

Look for `"synced": true`. No catalog block at all means the 1.1.3 server
was never deployed: deploy it (handoff step 2) first.

```bash
fly status -a garden-gnome-api
```

```bash
fly logs -a garden-gnome-api --no-tail
```

Find the time of the review in the logs. A machine starting up just then
means it had stopped while idle and was too slow to wake. In that case take
decision 1 now, `min_machines_running = 1` in `garden-gnome/fly.toml`, which
ships through a PR and a deploy as the handoff describes. A traceback means
something broke: don't reply yet, and bring the log to Claude. Once the
server is right, sign in on the TestFlight build with the same build number
and go through steps 1 to 3 of the Notes. Then reply and ask for another
review. Apple's help says a metadata rejection can go back with the same
build; for this one, follow what App Review asks.

```text
Hello, and thank you for reviewing PlantAdvocate. Sorry for the trouble.

The message in your screenshot means the app didn't get an answer from our server in time. [Our server had stopped while idle and took longer to start than the app waits. It is now kept running for the review.] [The server version this build needs had not been deployed yet. It is now.] [Keep this sentence only if you did it.] We signed in with Sign in with Apple and went through the steps in the Notes for Review on [DATE] with build [NUMBER], and each one worked.

Could you try again? If it happens again, the time it happened would help us find it in our logs.

Thank you,
Allison Bowman
```

## If the rejection is a crash

No reply fixes a crash. App Review usually attaches the crash log and the
device and iOS version it saw. Bring those to Claude. Note whether the crash
was at launch and on iOS 27. A local 1.1.3 build made with Xcode 27.1 crashed
at launch on the iOS 27.0 simulator, inside UIKit's scene-lifecycle check,
and `docs/2026-10-24-ios27-scene-lifecycle.md` explains why the EAS build,
made with Xcode 26.6 and the iOS 26.5 SDK, shouldn't. A launch crash on iOS
27 would most likely mean the build came from a different image, so look at
the image named on the EAS build's page first. The fix is a new build. Once
it has processed, choose it under Build on the 1.1.3 version page, resubmit,
and reply with one sentence on what changed and in which build.
