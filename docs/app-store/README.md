# App Store Connect paperwork for 1.1.3

Everything App Store Connect asks for before PlantAdvocate 1.1.3 can go to
App Review, ready to paste field by field. Each file was checked against the
code at `307930e` on `care-advice-honesty`, the ship branch, with the
review fixes made alongside it, and against production and the live website
on 16 and 17 October 2026.

- [listing.md](listing.md): name, subtitle, promotional text,
  description, keywords, What's New, categories, copyright, URLs, price and
  content rights.
- [app-privacy.md](app-privacy.md): the App Privacy questionnaire, type by
  type, and the privacy manifest entries that have to match it.
- [review-notes.md](review-notes.md): App Review Information: sign-in,
  contact, and the notes for the reviewer, rewritten on 24 October against
  `3f6d7da` from what `docs/go-to-market/research/review-risk.md` found,
  with the HAZARDS block brought up to the 2026-10-30 changes.
- [review-replies.md](review-replies.md): replies to paste into App Store
  Connect if App Review raises 2.1(a), 5.1.1(v), 4.8, 2.3 or a server
  error, with what to check before each one.
- [age-rating.md](age-rating.md): every age-rating question. The result
  is 4+.
- [screenshots.md](screenshots.md): the shot list, the sizes Apple
  accepts, and how to capture them on the simulator.
- [export-compliance.md](export-compliance.md): no non-exempt encryption,
  and why.

## Before you submit

These have to be true first, or some of the text in these files is not.

1. **Production runs the 1.1.3 backend.** On 16 October,
   `https://garden-gnome-api.fly.dev/openapi.json` still listed only
   `/environments/` routes. The app calls `/growing-areas/`, so the Growing
   areas tab, Add plant's area list and the Almanac's area filter would all
   fail for the reviewer. After deploying, check that `/openapi.json` lists
   `/growing-areas/`. Check that a new Sign in with Apple account shows My
   Home. Check that `/ai/status` still reports `advisor_symptoms_backend:
   "stub"` and `vision.ready: false`.
2. **The website says what the app does.** On 16 October the live support
   page still described subscriptions and Restore Purchases. The live
   privacy page was the July 17 policy, which says the app doesn't collect
   precise location. By 23 October someone had deployed the October 16
   rewrite, so the live privacy page is dated October 16 and lacks the
   October 20 text (`docs/go-to-market/product-truth.md`, section 6).
   Redeploy the corrected `site/` pages, then reload
   `https://plantadvocate.ai/support` and `https://plantadvocate.ai/privacy`
   to check.
3. **The build is made from a tip that carries the 2026-10-30 changes.**
   Every 1.1.3 change these files describe is on `care-advice-honesty`
   once they land: `ios.supportsTablet` false, so no iPad screenshots are
   asked for; plant hazards to people and pets stated plainly, with
   edibility shown only with its conditions, and the not-advice line under
   each hazard note and the Report a fact link (2026-10-30); the census
   export and sync operator-only,
   export 4.1 with fresh identifiers and care counted by month, and no Sync
   now button in the app; the in-app privacy summary naming all 3 weather
   services; and a privacy manifest matching app-privacy.md. No line in
   these files is waiting on a later change, so none needs cutting. A build
   from an older commit would make some of them untrue: one from `307930e`
   to `b6fee6b` lacks the not-advice line that the description, the Notes
   and the 1.4.1 reply now say the app shows. The hazard sentences' 2026-10-30
   wording (the local poison centre, the pets' source, the summary label)
   comes from the server, so it reaches every build once the backend
   deploy (item 1) is live.
4. **The server is awake when review starts.** It stops when idle
   (`garden-gnome/fly.toml`, `min_machines_running = 0`), and a first
   request after idle took 6.7 s on 15 October. Open the app once just
   before you press Submit. Consider `min_machines_running = 1` until the
   review is done.

## Order of work in App Store Connect

1. App Information: name, subtitle, categories, content rights and age
   rating, from listing.md and age-rating.md.
2. Pricing and Availability: Free.
3. App Privacy: privacy policy URL and the questionnaire, from
   app-privacy.md. Publish it.
4. The 1.1.3 version page: screenshots, promotional text, description,
   keywords, support and marketing URLs, copyright, then App Review
   Information from review-notes.md. Pick the build by its build number,
   not the version string.
5. Export compliance only if it's asked (export-compliance.md).
6. Add for Review, then Submit.
