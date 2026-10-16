# App Privacy answers for 1.1.3

These are the answers for App Store Connect > App Privacy, checked against
the code at `b083a90`. They describe the build as it ships, with photo
check-ups and free-text symptom reading switched off on the server.
Production's `GET /ai/status` answered `advisor_symptoms_backend: "stub"`
and `vision.ready: false` on 16 October, and the app shows neither feature
while it says so (`mobile/src/care/aiCapabilities.ts:29-39`).

App Privacy belongs to the app, not to a build. It can be changed at any
time and the change goes live without a review. That matters here, because
photo check-ups can be switched on from the server with no app update.
Update these answers first (see "Before switching on photo check-ups or
symptom reading" below).

Privacy Policy URL (asked on this page): `https://plantadvocate.ai/privacy`.
Leave the optional User Privacy Choices URL blank. The only choice in the
app is the census switch, which is in the app itself.

## The first question

**Do you or your third-party partners collect data from this app?** Yes.

Apple counts data as collected when it leaves the phone and is kept longer
than it takes to answer the request. PlantAdvocate's server keeps the
account, the plants and their records, so the answer is yes.

## Collected

None of the collected data is used for tracking. No data is combined with
other companies' data for advertising, and no data goes to a data broker.
So for every row below, **Used for tracking = No**.

Each type is linked to the user, because it is stored under the account.
For the 2 types the census can count (Coarse Location and Other User
Content), the export carries no account identifier. But Apple asks once per
type, and the same data is linked for app functionality.

| Apple category | Data type | Linked | Purposes | Where in the code |
|---|---|---|---|---|
| Contact Info | Name | Yes | App Functionality | Apple's full name, sent only at first sign-in, and Google's profile name are stored as `User.display_name` (`mobile/src/auth/signIn.ts:57-67`; `garden-gnome/app/routers/auth.py:139-146, 176-184`; `models.py:256`) |
| Contact Info | Email Address | Yes | App Functionality | The Apple or Google email, which may be an Apple relay address, is stored in `User.email` and `AuthIdentity.email_at_signup` and used to link a second sign-in method to the same account (`auth.py:74-80, 84`; `models.py:255, 288`) |
| Identifiers | User ID | Yes | App Functionality | The account's own ID and the Apple and Google subject IDs (`garden-gnome/app/models/models.py:254, 287`) |
| Location | Precise Location | Yes | App Functionality | A growing area's latitude and longitude, from "Use my location" or a geocoded address, are stored on the area and sent from the server to fetch its forecast (`mobile/src/location/lookup.ts:12-38`; `models.py:592-593`; `garden-gnome/app/services/weather.py:363-379`) |
| Location | Coarse Location | Yes | App Functionality, Analytics | A growing area's city, region and country are stored on the area (`models.py:589-591`). For people who join the census, they are the only location in the operator's census export (`garden-gnome/app/routers/census.py:162-168`) |
| User Content | Customer Support | Yes | App Functionality | "Report this result" and the support address in Settings open a prefilled email to support@plantadvocate.ai, carrying the result text, the plant and species, and the app version. The reply is kept in that mailbox (`mobile/src/support.ts:35-53`; `components/ReportResult.tsx:35`; `SettingsScreen.tsx:418-425`) |
| User Content | Other User Content | Yes | App Functionality, Analytics | Nicknames, spot notes, intake notes, counts, care logs and their outcomes, moves between areas, and each growing area's name, surface, measurements, conditions and goals (`models.py:574-703`; `mobile/src/api/plants.ts:19-71`; `api/growingAreas.ts:51-80`). For people who join the census, the operator's export counts plants, species, dates and care history, with no nickname, notes or account ID (`census.py:146-179`) |

Analytics, here, means only the community census. It is off unless the
person turns it on (`models.py:268`). It counts what people grow and how it
fares, so the care advice can improve. Nothing else in the app or the server
measures how the app is used.

## Not collected

| Apple category | Data type | Why it is not collected |
|---|---|---|
| Contact Info | Phone Number, Physical Address, Other User Contact Info | Never asked for. A typed address is geocoded on the phone, and only the city, region, country and coordinates are saved (`mobile/src/location/geocode.ts:21-28`) |
| Health & Fitness | Health, Fitness | Nothing in the app or server touches either |
| Financial Info | Payment Info, Credit Info, Other Financial Info | The app is free, with no purchases (`mobile/package.json` has no purchase library) |
| Location | (see above) | Both location types are declared above |
| Sensitive Info | Sensitive Info | Never asked for |
| Contacts | Contacts | No contacts access in the app |
| User Content | Emails or Text Messages | The app never reads the person's mail or messages. Support email is declared above as Customer Support |
| User Content | Photos or Videos | Not in 1.1.3 as shipped. Identifying a plant from a photo runs on the phone, and the picture is never uploaded (`mobile/src/photoId/identify.ts:52-120`; `modules/plant-id/ios/PlantIdModule.swift:39-56`). The photo check-up, the only upload, is hidden while the server reports vision off (`mobile/src/screens/PlantDetailScreen.tsx:339`) |
| User Content | Audio Data | Walk the garden turns speech into text through Apple's Speech framework, on the phone where it can and otherwise on Apple's servers (`mobile/modules/plant-speech/ios/PlantSpeechModule.swift:134, 180`). PlantAdvocate never receives the audio or the transcript, only the plants the person confirms (`mobile/src/screens/CaptureGardenScreen.tsx:185-191`; `api/plants.ts:50-54`) |
| User Content | Gameplay Content | No games |
| Browsing History | Browsing History | No in-app browser. Links open in Safari |
| Search History | Search History | Species search filters the list already on the phone. Search terms never reach the server (`mobile/src/api/species.ts:4-8`) |
| Identifiers | Device ID | No advertising ID, no vendor ID, no push token. Reminders are local notifications (`mobile/src/notifications/reminders.ts:197`) |
| Purchases | Purchase History | No purchases |
| Usage Data | Product Interaction, Advertising Data, Other Usage Data | No analytics or ad SDK in `mobile/package.json`, and no event endpoint on the server. Care logs are the person's own records, declared above as Other User Content |
| Diagnostics | Crash Data, Performance Data, Other Diagnostic Data | No crash or performance SDK. The only logs are the server's own operational logs, which aren't tied to an account or used to study anyone |
| Other Data | Other Data Types | Nothing else |

## What the label will show

"Data Linked to You": Contact Info, Identifiers, Location, User Content.

"Data Used to Track You": nothing.

"Data Not Linked to You": nothing.

## Where the server sends data onward

None of these is a third-party SDK in the app. They are services the
PlantAdvocate server calls to do its job, and their data is already declared
above.

- Sign-in: the phone talks to Apple or Google directly to sign in. The server
  checks the token with them, and on account deletion asks Apple to revoke
  the Sign in with Apple link (`garden-gnome/app/routers/auth.py:227-273`).
- Weather: a growing area's coordinates go to Apple WeatherKit, then the U.S.
  National Weather Service, then Open-Meteo, until one of them answers
  (`garden-gnome/app/services/weather.py:363-379`). The in-app privacy
  summary has to name all three. At `b083a90` it names only Apple Weather
  (`mobile/src/consent/copy.ts:99-110`), and that has to be fixed before 1.1.3 ships.

The Google Sign-In SDK is the one third-party SDK that handles personal
data, and it only signs in. Before submitting, open the archived build in
Xcode (Organizer > the archive > Generate Privacy Report) and check that it
lists nothing beyond the types above.

## The privacy manifest has to say the same

The app's privacy manifest (`expo.ios.privacyManifests` in
`mobile/app.json`) should declare these entries. Each has
`NSPrivacyCollectedDataTypeLinked = true` and
`NSPrivacyCollectedDataTypeTracking = false`.

| `NSPrivacyCollectedDataType` | `NSPrivacyCollectedDataTypePurposes` |
|---|---|
| `NSPrivacyCollectedDataTypeName` | `NSPrivacyCollectedDataTypePurposeAppFunctionality` |
| `NSPrivacyCollectedDataTypeEmailAddress` | `NSPrivacyCollectedDataTypePurposeAppFunctionality` |
| `NSPrivacyCollectedDataTypeUserID` | `NSPrivacyCollectedDataTypePurposeAppFunctionality` |
| `NSPrivacyCollectedDataTypePreciseLocation` | `NSPrivacyCollectedDataTypePurposeAppFunctionality` |
| `NSPrivacyCollectedDataTypeCoarseLocation` | `NSPrivacyCollectedDataTypePurposeAppFunctionality`, `NSPrivacyCollectedDataTypePurposeAnalytics` |
| `NSPrivacyCollectedDataTypeCustomerSupport` | `NSPrivacyCollectedDataTypePurposeAppFunctionality` |
| `NSPrivacyCollectedDataTypeOtherUserContent` | `NSPrivacyCollectedDataTypePurposeAppFunctionality`, `NSPrivacyCollectedDataTypePurposeAnalytics` |

Also `NSPrivacyTracking = false`, with no tracking domains. There is no
`PhotosorVideos` entry and no `AudioData` entry.

Coarse Location and Customer Support are on this list because the code
collects them. A growing area keeps its city, region and country, and the
census export carries them. Reports and support mail arrive in PlantAdvocate's
inbox. If the manifest leaves either out, add them there rather than
dropping them here.

## Before switching on photo check-ups or symptom reading

Switching either on is a server setting, and the app shows it the next time
it asks `GET /ai/status`. Do these first, in this order:

1. Ship the in-app consent for sending a photo, or the question text, to
   another company, and update the privacy policy to name that company.
2. Here, add **User Content > Photos or Videos**: linked, App Functionality,
   not tracking. A photo check-up uploads the photo under the person's
   account (`mobile/src/api/plants.ts:106-130`), and the model that reads
   it belongs to another company. Typed symptoms are already covered by
   Other User Content (App Functionality), so symptom reading changes
   nothing here, but the policy has to name the company that reads them.
3. Add the `PhotosorVideos` entry to the privacy manifest in the next build.
4. Only then change the server setting.

## If the census changes

The census answers assume what 1.1.3 does. Joining is a switch in the app,
off by default. Exporting is an operator job, with identifiers made fresh
for each export. The export has no name, email, nickname, notes,
coordinates or account ID. At `b083a90` 2 of those aren't true yet: any
signed-in account can call `/census/export`, and each record's
`plant_uuid` is the same in every export
(`garden-gnome/app/routers/census.py:96-147`). The operator-only census
change for 1.1.3 has to land before these answers are true.

If the export ever goes to another organization, say who in the privacy
policy. If it ever carries a stable identifier, change Coarse Location and
Other User Content here, and the consent copy in Settings.
