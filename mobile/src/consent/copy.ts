// What PlantAdvocate does with your data, in the app's own words.
//
// This module is the single source of truth for the consent copy, and it is
// deliberately DATA rather than JSX so it can be tested and so the same
// sentences can appear in Settings, at the point of use, and in the App Store
// privacy answers without drifting apart.
//
// The rule this file exists to enforce: every sentence here must be true of
// the code as it stands today, not of the code as we mean it to be. Each flow
// therefore names the module that implements it — modules, not line numbers,
// which went stale within weeks last time. If you change where data goes,
// this file is part of the change — not a follow-up.
//
// Verified against the implementation on 2026-10-16:
//   * identify  → src/photoId/identify.ts calls the on-device module only.
//                 src/api/species.ts has no identify function; the photo is
//                 never uploaded.
//   * diagnose  → src/api/plants.ts diagnosePlantPhoto POSTs the image and
//                 note to /plants/{id}/diagnose-photo; app/services/vision.py
//                 passes it to the configured vision service, and
//                 app/routers/plants.py saves only the reading's text to the
//                 timeline. Offered — and listed in Settings — only while
//                 GET /ai/status says a photo would be read
//                 (src/care/aiCapabilities.ts).
//   * advice    → app/services/advisor.py sends a free-text question to the
//                 symptoms backend with the plant's nickname, species facts,
//                 recent logs, growing area conditions and forecast. Offered
//                 and listed only while that backend is not the rule engine.
//                 src/consent/questionUpload.ts asks before the first
//                 question is sent (PlantDetailScreen, mayAskWith).
//   * voice     → modules/plant-speech sets requiresOnDeviceRecognition
//                 whenever the device supports it; otherwise iOS sends audio
//                 to Apple. The transcript is split on the phone
//                 (src/capture/) and only the confirmed plants reach
//                 POST /plants/bulk (src/api/plants.ts createPlantsBulk).
//   * location  → src/location/lookup.ts geocodes with the phone's own
//                 geocoder; app/services/weather.py asks WeatherKit, then
//                 api.weather.gov, then Open-Meteo, first answer wins;
//                 app/routers/census.py exports city/region/country only.
//   * census    → User.census_opt_in defaults to False (app/models/models.py);
//                 app/routers/census.py exports opted-in users only, to the
//                 operator only, with every identifier made fresh per export
//                 and the records shuffled (export version 4.1; the fields
//                 are listed above CENSUS_FIELDS below).

import type { AiCapabilities, AiCapability } from '../care/aiCapabilities';

/** Where a piece of data physically ends up. */
export type Destination =
  /** Never leaves the phone. */
  | 'device'
  /** Sent to PlantAdvocate's own server. */
  | 'server'
  /** Sent onward to a service that is not PlantAdvocate. */
  | 'partner';

export interface DataFlow {
  id: string;
  /** What the caretaker did, in their words — not the feature's codename. */
  title: string;
  destination: Destination;
  /** One line, plain. Shown in the Settings list. */
  summary: string;
  /** The honest detail, including who else sees it. */
  detail: string;
  /** True when nothing happens unless the caretaker turns it on. */
  optIn?: boolean;
  /** The feature this flow describes is offered only while the server can
   *  serve it, so the flow is listed only then too. A disclosure for a
   *  feature nobody can find sends a reader looking for it. */
  requires?: AiCapability;
}

export const DESTINATION_LABELS: Record<Destination, string> = {
  device: 'Stays on your phone',
  server: 'Sent to our server',
  partner: 'Shared with another service',
};

// ── What the census counts ────────────────────────────────────────────────────
// One list, read in both places the census is described (the Settings entry
// and the text under the switch), so the two can't drift apart. It is every
// field of a census record (app/routers/census.py build_export, export
// version 4.1), in the caretaker's words:
//   species_id, quantity, maturity_stage   → its species, how many, its stage
//   acquired_month, initial_condition      → the month you got it, how it looked
//   care_history (counts per type a month) → how many times each kind of care…
//   stewardship_count, stewardship_chain   → how many areas, the months it moved
//     (started_month / ended_month only)
//   split_from_ref                         → which planting it was split from
//   growing_area {type, city, region, country}
//   plant_ref, growing_area.ref            → labels made fresh for every export
// Records are shuffled, so a record's place in the file says nothing either.

/** Every field a census record carries, as one clause. */
export const CENSUS_FIELDS =
  'its species, how many there are, its growth stage, the month you got it and '
  + 'how it looked then (soil, leaves, any pests), how many times each kind of '
  + 'care was logged in each month, how many growing areas it has been in and '
  + 'the months it moved between them, which planting it was split from if it '
  + 'was, and its growing area’s type, city, region and country';

/** What a census record never carries. */
export const CENSUS_LEFT_OUT =
  'There is no name, no email, no nicknames, no notes, no exact dates and no '
  + 'coordinates.';

/** How far the census promises exports can't be put together, and no
 *  further: the identifiers are new every time, but a planting's monthly
 *  care counts are its own and could look alike from one export to the
 *  next. */
export const CENSUS_LINKING =
  'Each planting and growing area gets a new label in every export, and the '
  + 'records are shuffled, so no identifier links one export to another. That '
  + 'is the promise, and no more: a planting’s monthly care counts could still '
  + 'look alike from one export to the next.';

export const DATA_FLOWS: DataFlow[] = [
  {
    id: 'identify',
    title: 'Identifying a plant from a photo',
    destination: 'device',
    summary: 'The photo is read on your phone and never uploaded.',
    detail:
      'Your phone’s own AI looks at the picture and suggests a name — Apple '
      + 'Intelligence on iPhone, Gemini Nano on Android. The image is not sent '
      + 'to us, and it is not sent to anyone else. If your phone can’t do this, '
      + 'the feature simply says so rather than falling back to uploading.',
  },
  {
    id: 'diagnose',
    title: 'Asking the Gnome to look at an ailing plant',
    destination: 'partner',
    requires: 'photoDiagnosis',
    summary: 'This one does upload the photo. It is not kept.',
    detail:
      'Photo check-ups work differently from identification. The picture, and '
      + 'any note you add, goes to our server, which passes it to an outside AI '
      + 'service to be read. The photo is not saved to your account, and '
      + 'PlantAdvocate does not use it to train anything. Only the reading, as '
      + 'text, is saved to your plant’s timeline. The app asks before the first '
      + 'photo is sent.',
  },
  {
    id: 'care',
    title: 'Your plants and care log',
    destination: 'server',
    summary: 'Nicknames, species, and what you did when.',
    detail:
      'Stored so your schedule survives a new phone, and so advice can account '
      + 'for what you have actually been doing rather than what the label says. '
      + 'This is your record; you can delete the whole account, and everything '
      + 'in it, from this screen.',
  },
  {
    id: 'advice',
    title: 'Free-text questions to the Gnome',
    destination: 'partner',
    requires: 'symptoms',
    summary: 'Your question goes to an outside AI service. Your photos don’t.',
    detail:
      'Care advice is built from the curated species database. When you add a '
      + 'question in your own words, our server sends it to an outside AI '
      + 'service to be answered. The plant’s nickname, species facts and recent '
      + 'care log go with it, and so do its growing area’s name, conditions and '
      + 'forecast. Your name, email and coordinates are not included. The app '
      + 'asks before the first question is sent.',
  },
  {
    id: 'voice',
    title: 'Walking the garden out loud',
    destination: 'partner',
    summary: 'Your speech becomes text on your phone, or at Apple. We never get the audio.',
    detail:
      'Walk the garden uses the microphone only while it says Listening. It '
      + 'stops when you tap stop or leave the screen. Your iPhone turns speech '
      + 'into text on the phone where it can. Where it can’t, iOS sends the '
      + 'audio to Apple’s speech service to transcribe, and the screen tells you '
      + 'which is happening. PlantAdvocate never receives the audio. Only the '
      + 'plants you confirm — species, how many, and any spot you named — reach '
      + 'your account, as text.',
  },
  {
    id: 'location',
    title: 'A growing area’s location',
    destination: 'partner',
    summary: 'Coordinates go to weather services. They never reach the census.',
    detail:
      'When you give a growing area an address or use your current location, '
      + 'your phone’s own map service turns it into a place. We store its city, '
      + 'region, country and coordinates. To get that spot’s forecast, our '
      + 'server asks weather services in turn and stops at the first that '
      + 'answers: Apple Weather, then the U.S. National Weather Service, then '
      + 'Open-Meteo, which also covers places outside the U.S. Each one asked '
      + 'gets the coordinates rounded to about a kilometer, and nothing else '
      + 'about you, and the forecast card names whichever one answered. '
      + 'Coordinates are left out of the community census by construction, not '
      + 'by policy.',
  },
  {
    id: 'census',
    title: 'The community census',
    destination: 'partner',
    summary: 'Off unless you turn it on.',
    optIn: true,
    detail:
      'The census asks what the whole community is growing and how it is '
      + 'faring, so care advice can improve for everyone. If you join, each of '
      + `your plantings is counted: ${CENSUS_FIELDS}. ${CENSUS_LEFT_OUT} `
      + `${CENSUS_LINKING} If you don’t join, none of your data is counted at all.`,
  },
];

/** The flows shown in Settings, most surprising first. A caretaker who reads
 *  only the first two should learn the things they would not have guessed. */
export const SETTINGS_FLOW_ORDER = [
  'diagnose', 'identify', 'voice', 'location', 'census', 'advice', 'care',
];

export function orderedFlows(): DataFlow[] {
  const byId = new Map(DATA_FLOWS.map((f) => [f.id, f]));
  return SETTINGS_FLOW_ORDER.map((id) => byId.get(id)!).filter(Boolean);
}

/** The flows Settings lists right now: every flow that is always true, and
 *  each feature-bound one only while its feature is offered. */
export function visibleFlows(capabilities: AiCapabilities): DataFlow[] {
  return orderedFlows().filter((f) => !f.requires || capabilities[f.requires]);
}

/** Flows that send data anywhere — what a privacy-minded reader is looking for. */
export function leavingDevice(): DataFlow[] {
  return DATA_FLOWS.filter((f) => f.destination !== 'device');
}

// ── Point-of-use notices ─────────────────────────────────────────────────────
// Consent at the moment it matters. A policy read once at signup is not
// meaningful consent for an upload happening six weeks later.

export const PHOTO_DIAGNOSIS_NOTICE = {
  title: 'This sends your photo off your phone',
  body:
    'A photo check-up is the one feature that uploads a picture. It goes to our '
    + 'server with any note you add, and on to an outside AI service that reads '
    + 'it. The photo isn’t saved, and PlantAdvocate doesn’t use it to train '
    + 'anything. Only the reading is kept, on your plant’s timeline.\n\n'
    + 'Identifying a plant is different — that happens entirely on your phone.',
  confirmLabel: 'Send the photo',
  cancelLabel: 'Not now',
} as const;

/** Before the first question in the caretaker's own words is sent
 *  (consent/questionUpload.ts). Shown only while the box is offered. */
export const QUESTION_NOTICE = {
  title: 'This sends your question off your phone',
  body:
    'A question in your own words goes to our server and on to an outside AI '
    + 'service to be answered. Your plant’s nickname, species facts and recent '
    + 'care log go with it, and so do its growing area’s name, conditions and '
    + 'forecast. Your name, email and coordinates are not included.\n\n'
    + '“Not now” sends nothing, and your question stays in the box.',
  confirmLabel: 'Send my question',
  cancelLabel: 'Not now',
} as const;

export const CENSUS_CONSENT = {
  label: 'Join the community census',
  on:
    `Each of your plantings is counted: ${CENSUS_FIELDS}. ${CENSUS_LEFT_OUT} `
    + CENSUS_LINKING,
  off:
    'Your data is not counted. If you turn this on, each of your plantings is '
    + 'counted as “The community census” below lists it, with no name, email, '
    + 'notes, exact dates or coordinates. It helps the care advice get better '
    + 'for plants like yours; turning it back off stops it immediately. Counts '
    + 'already taken aren’t recalled.',
} as const;

/** Shown above the flow list. Sets the honest frame: this is a plain summary,
 *  and the policy is the binding document. */
export const PRIVACY_INTRO =
  'Plainly: what this app does with what you give it. The full policy is '
  + 'linked at the bottom and is the binding version.';
