# App Store Connect paperwork for 1.2.0 (build 26)

Everything App Store Connect asks for before PlantAdvocate 1.2.0 build 26
can go to App Review. These files were checked against `master` at `8379754`. Build 26 is made from the
commit after it, which adds: onboarding rewritten for 1.2.0 (its last button opens Home), zone names on the
zone map no longer broken mid-word, and a server fix for "database is locked" errors when Home loads. Each file
was checked against that commit on 2026-11-16, without live requests to
production or the website. 1.2.0 is the first version Apple reviews: 1.1.3
was uploaded and never submitted
(`docs/design/2026-11-15-overhaul-build-spec.md`, A15).

`mobile/store.config.json` was pulled from App Store Connect on 2026-11-16
with `eas metadata:pull` and now carries the 1.2.0 version, listing text,
URLs and review notes from these files. Push it with `eas metadata:push`
from `mobile/` once the checklist below is done.

- [listing.md](listing.md): name, subtitle, promotional text,
  description, keywords, categories, copyright, URLs, price and content
  rights, and why What's New does not apply.
- [review-notes.md](review-notes.md): App Review Information: sign-in, the
  Notes, a path through the app, each permission prompt, and what is
  switched off.
- [app-privacy.md](app-privacy.md): the App Privacy answers, type by type.
  No answer changes from 1.1.3.
- [age-rating.md](age-rating.md): every age-rating question. Still 4+.
- [export-compliance.md](export-compliance.md): no non-exempt encryption.
- [screenshots.md](screenshots.md): the 8-shot list for 1.2.0, the sizes,
  and how to capture them on the simulator.
- [review-replies.md](review-replies.md): replies prepared for 1.1.3.
  Check each against 1.2.0 before using it.

## Before you submit

Each line says what is known today. "Not checked" means nobody has looked
in this pass; it is not a failure.

- [ ] **Production runs `master` with both flags on.** Reported, not
  checked here. Check that `/openapi.json` lists `/properties`, `/vitals`
  and `/properties/{id}/layers`, and that a new account's Home shows the
  "Have a yard or garden beds?" card (it shows only when the server says
  land can be added, `mobile/src/home/form.ts`, `offersAddLand`). With
  either flag off those routes answer 404 and the land steps in the Notes
  fail. The reviewer signs in with a new account,
  so the flags must be on for everyone, not an allowlist (PLAN.md section 9,
  "What App Review will see").
- [ ] **Photo check-ups and free-text questions are off.** Reported, not
  checked here. `GET /ai/status` should answer `vision.ready: false` and the
  symptoms backend `stub`. The listing and Notes depend on it.
- [ ] **Build 26 works on the simulator.** In progress (the lead
  engineer). Walk the 9 steps in review-notes.md's Notes with the Arboretum
  address, against production. If it passes, optionally add the TESTED ON
  line (review-notes.md).
- [ ] **A brand-new Apple ID signs in.** Not checked. Sign in once with an
  Apple ID that has never used PlantAdvocate, check that Home appears, then
  delete the account (Settings > Account > Delete account).
- [ ] **Sign in with Google works for an outside account.** Not checked.
  If the Google project's consent screen is still in testing, publish it or
  cut Google from the SIGN-IN block of the Notes.
- [ ] **The website says what 1.2.0 does.** `site/privacy.html` in the
  repository is the 1.2.0 policy (effective November 16, 2026) that covers the land features
  (`site/privacy.html`, "What changed"). Not checked: that it is deployed, and that
  `/support` describes 1.2.0 with no subscriptions or Restore Purchases.
  Reload `https://plantadvocate.ai/privacy` and
  `https://plantadvocate.ai/support` before submitting.
- [ ] **App Privacy is saved and published.** Not recorded anywhere. The
  answers in app-privacy.md are the same as 1.1.3's; check them in App
  Store Connect and publish.
- [ ] **Screenshots for 1.2.0 are uploaded.** Not done. The pulled config
  lists the 1.1.3 files. Shoot the list in screenshots.md, then replace the
  `screenshots` list in `mobile/store.config.json` or upload by hand.
- [ ] **Sign-in required.** The pulled config has `demoRequired: true`
  with no user name or password, left as it is. If Add for Review asks for
  them, see review-notes.md, "The Sign-in required box".
- [ ] **The server is up when review starts.** `garden-gnome/fly.toml` on
  `master` sets `min_machines_running = 1`, but production was reported to
  sleep when idle; check `fly scale show` or `fly machine list` before
  submitting. Open the app once just before you press Submit anyway, since
  any deploy or flag change restarts it.
- [ ] **Build number.** EAS sets it remotely (`mobile/eas.json`,
  `appVersionSource: "remote"`, `autoIncrement`). Pick build 26 by its
  number on the version page, not by the version string.

## Order of work in App Store Connect

1. `eas metadata:push` from `mobile/`, or paste by hand: App Information
   (name, subtitle, categories, age rating) and the 1.2.0 version page
   (promotional text, description, keywords, URLs, copyright, App Review
   Information).
2. Pricing and Availability: Free, United States.
3. App Privacy: check against app-privacy.md and publish.
4. Screenshots, from screenshots.md.
5. Pick build 26.
6. Export compliance only if it is asked (export-compliance.md).
7. Add for Review, then Submit.
