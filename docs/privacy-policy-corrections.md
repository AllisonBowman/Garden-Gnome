# Privacy policy corrections — three statements that don't match the code

> **STATUS: AWAITING YOUR APPROVAL (2026-07-25).** This is a draft of legal
> copy for a published page. I have **not** edited `site/privacy.html` — that
> page is the binding document and changing it is publishing, which is your
> call, not mine. The replacement text below is ready to paste.

Found while building the in-app consent copy. Each item was checked against
the implementation, not inferred from the feature list.

The in-app work (the `Privacy & data` card, the photo-upload notice, the census
switch) is already done and describes the app **as it actually behaves**. That
means the app and the website currently disagree in three places, and the
website is the one that is wrong.

---

## 1. Photo diagnosis already uploads photos — the policy says it doesn't

**Severity: highest.** This is a factual misstatement about a shipping feature,
in the document App Review reads.

The policy currently says:

> Species identification runs entirely on your device — the photo is analyzed
> locally and is not transmitted to our servers or to any third party. **If we
> introduce server-based photo diagnosis in the future**, photos submitted to
> that feature would be transmitted for processing, and we will update this
> policy before doing so.

The first half is true and verified: `src/photoId/identify.ts` calls the
on-device module only, and `src/api/species.ts` contains no identify function
at all, so there is no upload path for identification.

The second half describes as hypothetical something the app ships today.
`src/api/plants.ts:67` builds a `FormData` with the image and POSTs it to
`/plants/{plant_id}/diagnose-photo`. It is reachable from Plant detail →
photo check-up. **The photo leaves the device.**

The nuance worth keeping: `VISION_BACKEND` defaults to `stub`, so nothing
currently *analyzes* the photo — the bytes are received and discarded. That
makes the current behavior harmless, but "we received your photo and threw it
away" is still transmission, and the policy denies transmission outright.

### Replacement text

> **Photos.** PlantAdvocate uses photos in two different ways, and the
> difference matters.
>
> *Identifying a plant* runs entirely on your device. The image is analyzed by
> your phone's own AI and is not transmitted to us or to anyone else.
>
> *Photo check-ups*, where you ask about an ailing plant, work differently: the
> image is uploaded to our server to be examined. It is held only for as long
> as that reading takes, is never written to storage, is never added to your
> plant's photos, and is never used to train any model. Only the resulting text
> is saved, to that plant's own care timeline. The App tells you this before
> the first photo is uploaded and asks you to confirm.

If a hosted vision backend is later enabled (`VISION_BACKEND=anthropic`), the
photo would additionally be sent to a third-party AI provider. **Update this
policy before flipping that variable, not after** — that is the change that
turns the paragraph above into an understatement.

---

## 2. Location is not mentioned anywhere in the policy

**Severity: high.** Not a misstatement — an omission, in the category
reviewers scrutinize most.

The app collects **precise coordinates**. `src/location/` fills `lat`/`lng` on
a growing environment, the server stores them, and `app/services/weather.py`
sends them to **Apple WeatherKit** to fetch that spot's forecast. Apple is a
third party receiving location data. The policy says nothing about any of it.

The good news is that the engineering is already defensible and the copy can
simply say so: coordinates are excluded from the census export by construction
(`app/routers/census.py:10` — "lat/lng never leave the server"), not by a
promise to be careful.

### Replacement text — new section, after "Plant and Care Data"

> **Location.** You can give a growing environment an address so the App knows
> the weather where your plants actually are. If you do, we store that place's
> coordinates and send them to Apple's weather service to retrieve the local
> forecast — that is how advice for outdoor plants can tell you rain is coming
> or a heat spike is due. Location is optional: environments work without it,
> and you are asked for device location only if you choose to use it.
>
> Precise coordinates are never included in the anonymized community census.
> Shared data describes a region — city, state, country — and never a point on
> a map.

This also needs an **App Store privacy label** entry: *Location → Precise
Location → App Functionality*, not linked to identity, not used for tracking.

---

## 3. The census opt-in was promised before the control existed

**Severity: resolved in code — noted so the record is honest.**

The policy says:

> Anonymized community data sharing is off by default and happens only if you
> opt in within the App.

Both halves were half-true. The backend was correct — `census_opt_in` defaults
to `False` and the export includes only opted-in users. But **there was no
control anywhere in the app**. `AuthUser.census_opt_in` existed as a type,
`PATCH /me` accepted the field, and nothing called it. A user could not opt in
if they wanted to.

The practical effect was conservative rather than harmful: nobody was counted.
But the sentence described a choice the app did not offer.

**Fixed in this branch** — Settings → Privacy & data now carries the switch,
wired to `PATCH /me` via `src/api/me.ts`. No policy edit needed; the sentence
is now simply true. It should stay accurate: if the census ever counts a user
who has not opted in, this sentence becomes the problem.

---

## Also fixed in this branch (no policy impact)

**The app asked for microphone access it never uses.** `expo-camera`'s config
plugin adds `RECORD_AUDIO` on Android by default, and its iOS half writes an
`NSMicrophoneUsageDescription` string whenever one isn't explicitly disabled
(verified in `node_modules/expo-camera/plugin/build/withCamera.js` and
`@expo/config-plugins/build/ios/Permissions.js:32` — the default is used when
no value is passed). `app.json` also listed `RECORD_AUDIO` a second time by
hand.

The app never records audio or video. Now set to
`"microphonePermission": false, "recordAudioAndroid": false`, and the manual
Android entry is removed. "Why does a plant app want my microphone?" is a
question worth never being asked.

**This needs a native rebuild to take effect** — it changes `app.json`, so the
next `npm run sim` will run a full prebuild (a few minutes) rather than the
usual fast path.

---

## Suggested order

1. Paste §1 and §2 into `site/privacy.html`, bump the effective date.
2. Add the Location entry to the App Store privacy labels.
3. Rebuild so the microphone strings actually leave the binary.
4. Ship the in-app consent card with it, so the app and the page agree on the
   day someone reads both.
