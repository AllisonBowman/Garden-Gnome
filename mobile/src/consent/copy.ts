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
import { t } from '../i18n';

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
  device: t('consent.destination.device'),
  server: t('consent.destination.server'),
  partner: t('consent.destination.partner'),
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
export const CENSUS_FIELDS = t('consent.census.fields');

/** What a census record never carries. */
export const CENSUS_LEFT_OUT = t('consent.census.leftOut');

/** How far the census promises exports can't be put together, and no
 *  further: the identifiers are new every time, but a planting's monthly
 *  care counts are its own and could look alike from one export to the
 *  next. */
export const CENSUS_LINKING = t('consent.census.linking');

export const DATA_FLOWS: DataFlow[] = [
  {
    id: 'identify',
    title: t('consent.flows.identify.title'),
    destination: 'device',
    summary: t('consent.flows.identify.summary'),
    detail: t('consent.flows.identify.detail'),
  },
  {
    id: 'diagnose',
    title: t('consent.flows.diagnose.title'),
    destination: 'partner',
    requires: 'photoDiagnosis',
    summary: t('consent.flows.diagnose.summary'),
    detail: t('consent.flows.diagnose.detail'),
  },
  {
    id: 'care',
    title: t('consent.flows.care.title'),
    destination: 'server',
    summary: t('consent.flows.care.summary'),
    detail: t('consent.flows.care.detail'),
  },
  {
    id: 'advice',
    title: t('consent.flows.advice.title'),
    destination: 'partner',
    requires: 'symptoms',
    summary: t('consent.flows.advice.summary'),
    detail: t('consent.flows.advice.detail'),
  },
  {
    id: 'voice',
    title: t('consent.flows.voice.title'),
    destination: 'partner',
    summary: t('consent.flows.voice.summary'),
    detail: t('consent.flows.voice.detail'),
  },
  {
    id: 'location',
    title: t('consent.flows.location.title'),
    destination: 'partner',
    summary: t('consent.flows.location.summary'),
    detail: t('consent.flows.location.detail'),
  },
  {
    id: 'census',
    title: t('consent.flows.census.title'),
    destination: 'partner',
    summary: t('consent.flows.census.summary'),
    optIn: true,
    detail: t('consent.flows.census.detail', {
      fields: CENSUS_FIELDS, leftOut: CENSUS_LEFT_OUT, linking: CENSUS_LINKING,
    }),
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
  title: t('consent.photoNotice.title'),
  body: t('consent.photoNotice.body'),
  confirmLabel: t('consent.photoNotice.confirm'),
  cancelLabel: t('consent.photoNotice.cancel'),
} as const;

/** Before the first question in the caretaker's own words is sent
 *  (consent/questionUpload.ts). Shown only while the box is offered. */
export const QUESTION_NOTICE = {
  title: t('consent.questionNotice.title'),
  body: t('consent.questionNotice.body'),
  confirmLabel: t('consent.questionNotice.confirm'),
  cancelLabel: t('consent.questionNotice.cancel'),
} as const;

export const CENSUS_CONSENT = {
  label: t('consent.censusConsent.label'),
  on: t('consent.censusConsent.on', {
    fields: CENSUS_FIELDS, leftOut: CENSUS_LEFT_OUT, linking: CENSUS_LINKING,
  }),
  off: t('consent.censusConsent.off'),
} as const;

/** Shown above the flow list. Sets the honest frame: this is a plain summary,
 *  and the policy is the binding document. */
export const PRIVACY_INTRO = t('consent.privacyIntro');
