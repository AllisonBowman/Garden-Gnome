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
  contact, and the notes for the reviewer.
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
   precise location. Deploy the corrected `site/` pages, then reload
   `https://plantadvocate.ai/support` and `https://plantadvocate.ai/privacy`
   to check.
3. **The build is made from `307930e` or later.** Every 1.1.3 change these
   files describe is on that branch: `ios.supportsTablet` false, so no iPad
   screenshots are asked for; plant hazards to people and pets stated
   plainly, with edibility shown only with its conditions; the census
   export and sync operator-only, export 4.1 with fresh identifiers and
   care counted by month, and no Sync now button in the app; the in-app
   privacy summary naming all 3 weather services; and a privacy manifest
   matching app-privacy.md. No line in these files is waiting on a change,
   so none needs cutting. A build from an older commit would make some of
   them untrue.
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
