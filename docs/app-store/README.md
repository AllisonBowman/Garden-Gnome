# App Store Connect paperwork for 1.1.3

Everything App Store Connect asks for before PlantAdvocate 1.1.3 can go to
App Review, ready to paste field by field. Each file was checked against the
code at `b083a90` on `care-advice-honesty`, and against production and the
live website on 16 October 2026.

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
3. **The build has the 1.1.3 changes these files describe.** That means
   `ios.supportsTablet` set to false, so no iPad screenshots are asked for.
   Plant hazards to people and pets stated plainly, with edibility shown
   only with its conditions. The census export and sync made operator-only,
   with identifiers made fresh for each export and no Sync now button in
   the app. The in-app privacy summary naming all 3 weather services. A
   privacy manifest matching app-privacy.md. listing.md and review-notes.md
   mark which lines to cut if one of these misses the build.
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
