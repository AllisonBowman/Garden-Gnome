# App Privacy answers for 1.2.0 (build 26)

These are the answers for App Store Connect > App Privacy, checked on
2026-11-16 against `master` at `8379754`, the commit build 26 is made from,
against the privacy manifest in `mobile/app.json`, and against the published
policy text in `site/privacy.html` (effective November 16, 2026 in the copy read
on 2026-11-16; another change was editing it at the same time). They describe the build as it ships: identifying a
plant from a photo is hidden (`mobile/src/photoId/entry.ts`), and photo
check-ups and free-text questions are switched off on the server, so the app
hides them (`mobile/src/care/aiCapabilities.ts`).

## Does anything in App Store Connect need changing from 1.1.3?

**No answer changes.** 1.2.0 collects more data, but every new item falls
inside a data type and purpose the 1.1.3 answers already declared:

- the land pin, the zone boxes and the spot sent to fetch the aerial image
  are **Precise Location** (already declared, App Functionality);
- the land's town, state, country and time zone are **Coarse Location**
  (already declared, App Functionality and Analytics);
- the land's name, what is on the lot, the frost-earlier-or-later answer,
  each zone's description, every correction and every seasonal answer are
  **Other User Content** (already declared, App Functionality and
  Analytics);
- reporting a land result is an email to support, **Customer Support**
  (already declared).

No new type is added: no push token (alerts are local notifications), no
photos, no audio, no street address, no search history. The privacy
manifest in `mobile/app.json` already lists exactly the 7 types below with
the same purposes, so it needs no change either.

What does need doing: App Privacy was answered on paper for 1.1.3, and
nothing in the repository records that the answers were saved and
published in App Store Connect. Open App Privacy, check each type against
the table below, and press Publish if it offers to. App Privacy belongs to
the app, not to a build, and a change goes live without a review.

Privacy Policy URL (asked on this page): `https://plantadvocate.ai/privacy`.
Leave the optional User Privacy Choices URL blank. The only choice in the
app is the census switch in Settings.

## The first question

**Do you or your third-party partners collect data from this app?** Yes.
The server keeps the account, plants, growing spaces and land.

## Collected

None of the collected data is used for tracking, combined with other
companies' data for advertising, or sold. So for every row,
**Used for tracking = No**. Each type is **linked to the user**, because it
is stored under the account.

| Apple category | Data type | Linked | Purposes | Where in the code |
|---|---|---|---|---|
| Contact Info | Name | Yes | App Functionality | Apple's full name at first sign-in, or Google's profile name, stored as `User.display_name` (`garden-gnome/app/models/models.py:326`; `mobile/src/auth/signIn.ts`) |
| Contact Info | Email Address | Yes | App Functionality | The Apple or Google email, possibly an Apple relay address, in `User.email` and `AuthIdentity.email_at_signup` (`models.py:325, 358`) |
| Identifiers | User ID | Yes | App Functionality | The account ID and the Apple and Google subject IDs (`models.py:324, 352-358`) |
| Location | Precise Location | Yes | App Functionality | New in 1.2.0: the land pin as exact coordinates, with whether it came from the phone's location or from placing it (`models.py:726-752`, `Property.pin_lat`, `pin_lng`, `pin_source`); each zone's box as a GeoJSON polygon and its copy of the pin (`models.py:711-720`, `boundary_geojson`; `garden-gnome/app/routers/properties.py:217-224`); the outline each site reading was worked out for (`models.py:757-782`, `SiteReading`; `site/privacy.html`, "Your land"). The spot the app sends before the pin is placed is used to fetch the aerial image and is not kept (`mobile/src/api/properties.ts:200-203`; `site/privacy.html`, "Your land's pin"). As in 1.1.3: a growing space's coordinates, for its forecast (`models.py:684-685`) |
| Location | Coarse Location | Yes | App Functionality, Analytics | New in 1.2.0: the land's town, state, country and time zone, filled on the server from the National Weather Service answer (`models.py:743-746`; `site/privacy.html`, "Your land"), and copied to each zone (`properties.py:217-224`). As in 1.1.3: a growing space's city, region and country. For people who join the census, a zone's or space's city, region and country are the only location in the operator's export (`garden-gnome/app/routers/census.py:265-272`) |
| User Content | Customer Support | Yes | App Functionality | Report a fact, Report this result and the support address open a prefilled email to support (`mobile/src/support.ts:35-63`; `mobile/src/components/ReportResult.tsx`, `ReportFact.tsx`). A land result is reported by email too (`site/privacy.html`, "AI Processing") |
| User Content | Other User Content | Yes | App Functionality, Analytics | New in 1.2.0: the land's name, lot contents and frost bias (`models.py:739, 747-749`); each zone's name, what grows there and leaf habit (`models.py:711-720`); every correction, including ones taken back (`models.py:875-889`, `SiteOverride`); every seasonal answer, such as a frost that happened and its date, or a task done (`models.py:818-838`, `SeasonEventState`). As in 1.1.3: nicknames, notes, care logs and each space's description. The census counts plantings only; none of the new land data is in its export (`census.py:216-283`) |

Analytics, here, means only the community census, off unless the person
turns it on (`models.py:338`). Nothing else measures how the app is used.

## Not collected

| Apple category | Data type | Why it is not collected |
|---|---|---|
| Contact Info | Physical Address, Phone Number, Other User Contact Info | A typed address goes to the phone's own geocoder (`mobile/src/location/lookup.ts:16-19`) and is never sent to the server: the land setup sends only the pin (`mobile/src/land/setup.ts:7-9`; `Property` has no address column, `models.py:726-752`) |
| Health & Fitness | Health, Fitness | Nothing touches either. The motion string in `mobile/app.json` says the app never asks |
| Financial Info | All | Free, with no purchases (`mobile/package.json`) |
| Sensitive Info | Sensitive Info | Never asked for |
| Contacts | Contacts | No contacts access |
| User Content | Emails or Text Messages | The app never reads mail or messages. Support email is declared as Customer Support |
| User Content | Photos or Videos | Nothing is uploaded in build 26. Photo identification is hidden, and the photo check-up, the only upload, is hidden while the server reports vision off. The aerial image is public map data the server fetches, not the person's photo. The Walk the garden camera is a live backdrop that is not recorded (`mobile/app.json`, `expo-camera` string) |
| User Content | Audio Data | Speech becomes text through Apple's Speech framework. PlantAdvocate never receives the audio or the transcript, only the plants confirmed (`mobile/modules/plant-speech/ios/PlantSpeechModule.swift`; `mobile/src/consent/copy.ts`, the `voice` flow) |
| User Content | Gameplay Content | No games |
| Browsing History | Browsing History | No in-app browser. Links open in Safari |
| Search History | Search History | Species search filters the list on the phone (`mobile/src/api/species.ts:7-11`, no search parameter). Address search runs on the phone |
| Identifiers | Device ID | No advertising ID, vendor ID or push token. Care reminders and frost alerts are local notifications (`mobile/src/notifications/reminders.ts:323`); `site/privacy.html`, "Plants and growing areas" says no notification token is kept |
| Purchases | Purchase History | No purchases |
| Usage Data | All | No analytics or ad SDK in `mobile/package.json`, and no event endpoint |
| Diagnostics | All | No crash or performance SDK. Server logs are operational, not tied to studying anyone (`site/privacy.html`, "Technical data") |
| Other Data | Other Data Types | Nothing else. Site readings worked out from public maps describe the land, and are covered by Precise Location (their outline) and Other User Content (the corrections beside them) |

## What the label will show

"Data Linked to You": Contact Info, Identifiers, Location, User Content.
"Data Used to Track You": nothing. "Data Not Linked to You": nothing.
The same as 1.1.3.

## Where the server sends data onward

None of these is a third-party SDK in the app. They are services the
server calls, and their data is already declared above.

- Sign-in: Apple or Google, and on account deletion a request to Apple to
  revoke the sign-in (`garden-gnome/app/routers/auth.py:374-430`).
- Public map services, asked about a block about 1,600 feet (500 meters)
  across that contains the pin, never the pin: the U.S. Department of
  Agriculture soil survey (`garden-gnome/app/services/site/sources/soil.py:35`),
  the U.S. Geological Survey for elevation, land cover and aerial images
  (`elevation.py:47`, `landcover.py:36`, `imagery.py:48`), and Amazon Web
  Services for the canopy height map (`canopy.py:52`). The hardiness zone and
  frost normals are read from files on the server.
- The Sun, Trees and Water layer pictures are drawn on the server only from
  copies of elevation and canopy data it already holds, and are stored with
  the block's other copies and deleted with them
  (`garden-gnome/app/services/site/layers.py`; provider `site_layers` in
  `geodata_tile`). They send nothing anywhere.
- Weather: coordinates rounded to about two-thirds of a mile go to the National
  Weather Service, Apple Weather or Open-Meteo, in the order
  `site/privacy.html`, "Weather" sets out.

The policy names each of these (`site/privacy.html`, "What changed", "Public maps for your land", "Weather" and the list of who receives what).
The Google Sign-In SDK is the one third-party SDK that handles personal
data, and it only signs in. Before submitting, open the archived build in
Xcode (Organizer > the archive > Generate Privacy Report) and check that it
lists nothing beyond the types above.

## Deletion

Delete account removes the land with everything else: properties, site
readings, corrections and seasonal answers
(`garden-gnome/app/routers/properties.py:278-305`, called from `auth.py`,
`delete_me`), and zones go with the growing areas. Map copies are filed by
block with no user identifier, and a block's copies are pruned when no land
in the records uses it (`garden-gnome/app/models/models.py:851-873`;
`properties.py:300-301`).

## The privacy manifest says the same

`expo.ios.privacyManifests` in `mobile/app.json` declares Name, Email
Address, User ID, Precise Location, Coarse Location (App Functionality and
Analytics), Customer Support and Other User Content (App Functionality and
Analytics), each linked and not tracking, with `NSPrivacyTracking` false and
no tracking domains. No Photos or Videos, Audio Data or Device ID entry. It
matches the table above and needs no change for 1.2.0.

## Before switching on photo check-ups or symptom reading

Either is a server setting, and the app shows it the next time it asks
`GET /ai/status`. First: ship in-app consent for sending a photo or a
question to another company and name that company in the policy; add
**User Content > Photos or Videos** here (linked, App Functionality, not
tracking) for photo check-ups; add the `PhotosorVideos` entry to the
manifest in the next build; only then change the server setting.

## If the census changes

The census answers assume what 1.2.0 does: joining is a switch, off by
default; export and sync answer only the operator
(`garden-gnome/app/routers/census.py`, `require_operator`); the export has
no name, email, nickname, notes, coordinates, account ID, land pin, zone box,
correction or seasonal answer. If it ever goes to another organization, or
carries a stable identifier, change Coarse Location and Other User Content
here, the policy, and the consent copy in Settings.
