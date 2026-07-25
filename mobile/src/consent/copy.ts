// What PlantAdvocate does with your data, in the app's own words.
//
// This module is the single source of truth for the consent copy, and it is
// deliberately DATA rather than JSX so it can be tested and so the same
// sentences can appear in Settings, at the point of use, and in the App Store
// privacy answers without drifting apart.
//
// The rule this file exists to enforce: every sentence here must be true of
// the code as it stands today, not of the code as we mean it to be. Each flow
// therefore names the module that implements it. If you change where data
// goes, this file is part of the change — not a follow-up.
//
// Verified against the implementation on 2026-07-25:
//   * identify  → src/photoId/identify.ts calls the on-device module only.
//                 src/api/species.ts has no identify function; the photo is
//                 never uploaded.
//   * diagnose  → src/api/plants.ts:67 POSTs the image to
//                 /plants/{id}/diagnose-photo. The photo DOES leave the device.
//   * location  → src/location/* fills lat/lng; the server sends coordinates to
//                 Apple WeatherKit and keeps them out of the census export
//                 (app/routers/census.py:10).
//   * census    → app/models/models.py:120, census_opt_in defaults to False.

/** Where a piece of data physically ends up. */
export type Destination =
  /** Never leaves the phone. */
  | 'device'
  /** Sent to PlantAdvocate's own server. */
  | 'server'
  /** Sent onward to a named company that is not PlantAdvocate. */
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
}

export const DESTINATION_LABELS: Record<Destination, string> = {
  device: 'Stays on your phone',
  server: 'Sent to our server',
  partner: 'Shared with a named company',
};

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
    destination: 'server',
    summary: 'This one does upload the photo. It is not kept.',
    detail:
      'Photo check-ups work differently from identification: the picture is '
      + 'sent to our server to be examined. It is held in memory only for as '
      + 'long as the reading takes and is never written to disk, never added '
      + 'to your plant’s photos, and never used to train anything. Only the '
      + 'resulting text is saved, to your plant’s own timeline.',
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
    summary: 'Your question text — never your photos — goes to an AI provider.',
    detail:
      'Care advice is built from the curated species database. When you add a '
      + 'question in your own words, that text is sent to a third-party AI '
      + 'service to be answered, along with the plant’s species facts and '
      + 'recent care history. Your name, email, and exact location are not '
      + 'included. The provider may not use it for advertising.',
  },
  {
    id: 'location',
    title: 'A growing environment’s location',
    destination: 'partner',
    summary: 'Coordinates reach Apple Weather. They never reach the census.',
    detail:
      'If you give an environment an address, its coordinates are stored and '
      + 'sent to Apple Weather to fetch that spot’s forecast — that is how '
      + 'outdoor advice knows rain is coming. Precise coordinates stay on the '
      + 'server: they are excluded from every shared view by construction, not '
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
      + 'faring, so care advice can improve for everyone. If you join, your '
      + 'plants and care intervals are counted — with no name, no email, no '
      + 'notes, no coordinates, and no identifier that could link one export '
      + 'to the next. If you do not, none of your data is counted at all.',
  },
];

/** The flows shown in Settings, most surprising first. A caretaker who reads
 *  only the first two should learn the things they would not have guessed. */
export const SETTINGS_FLOW_ORDER = [
  'diagnose', 'identify', 'location', 'census', 'advice', 'care',
];

export function orderedFlows(): DataFlow[] {
  const byId = new Map(DATA_FLOWS.map((f) => [f.id, f]));
  return SETTINGS_FLOW_ORDER.map((id) => byId.get(id)!).filter(Boolean);
}

/** Flows that send data anywhere — what a privacy-minded reader is looking for. */
export function leavingDevice(): DataFlow[] {
  return DATA_FLOWS.filter((f) => f.destination !== 'device');
}

// ── Point-of-use notices ─────────────────────────────────────────────────────
// Consent at the moment it matters. A policy read once at signup is not
// meaningful consent for an upload happening six weeks later.

export const PHOTO_DIAGNOSIS_NOTICE = {
  title: 'This sends your photo to us',
  body:
    'A photo check-up is the one feature that uploads a picture. It is examined '
    + 'on our server, kept only for as long as the reading takes, and never '
    + 'stored or used to train anything.\n\n'
    + 'Identifying a plant is different — that happens entirely on your phone.',
  confirmLabel: 'Send the photo',
  cancelLabel: 'Not now',
} as const;

export const CENSUS_CONSENT = {
  label: 'Join the community census',
  on:
    'Your plants are counted. No name, no email, no notes, no coordinates — and '
    + 'the identifiers are rotated on every export, so two counts can’t be '
    + 'linked back to one garden.',
  off:
    'Your data is not counted. Turning this on helps the care advice get better '
    + 'for plants like yours; turning it back off stops it immediately.',
} as const;

/** Shown above the flow list. Sets the honest frame: this is a plain summary,
 *  and the policy is the binding document. */
export const PRIVACY_INTRO =
  'Plainly: what this app does with what you give it. The full policy is '
  + 'linked at the bottom and is the binding version.';
