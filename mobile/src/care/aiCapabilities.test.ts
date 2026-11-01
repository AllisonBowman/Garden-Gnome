import { AiStatus, photoDiagnosisOffered, symptomsOffered } from './aiCapabilities';

// The server's own source is read to pin the keys, the way census.keys.test.ts
// does. Declared locally rather than pulling in @types/node, which conflicts
// with React Native's timer typings.
declare const require: (id: string) => any;
declare const __dirname: string;
const fs = require('fs');
const path = require('path');

const readSrc = (rel: string): string =>
  fs.readFileSync(path.join(__dirname, rel), 'utf8');

// What production answers today: rule-based advice only.
const production: AiStatus = {
  advisor_symptoms_backend: 'stub',
  vision: { backend: 'stub', model: null, ready: false },
};

const switchedOn: AiStatus = {
  advisor_symptoms_backend: 'anthropic',
  vision: { backend: 'anthropic', model: 'a-model', ready: true },
};

// --- what production offers today ------------------------------------------

test('with every backend on stub, neither photo check-ups nor symptoms are offered', () => {
  expect(photoDiagnosisOffered(production)).toBe(false);
  expect(symptomsOffered(production)).toBe(false);
});

test('once the server has a model, both are offered without an app update', () => {
  expect(photoDiagnosisOffered(switchedOn)).toBe(true);
  expect(symptomsOffered(switchedOn)).toBe(true);
});

test('a vision backend that is configured but not ready still hides the photo check-up', () => {
  const notReady: AiStatus = {
    ...switchedOn,
    vision: { backend: 'anthropic', model: 'a-model', ready: false },
  };
  expect(photoDiagnosisOffered(notReady)).toBe(false);
});

test('symptom reading and photo check-ups switch on independently', () => {
  const symptomsOnly: AiStatus = { ...production, advisor_symptoms_backend: 'anthropic' };
  expect(symptomsOffered(symptomsOnly)).toBe(true);
  expect(photoDiagnosisOffered(symptomsOnly)).toBe(false);

  const photosOnly: AiStatus = { ...production, vision: { ...production.vision, ready: true } };
  expect(photoDiagnosisOffered(photosOnly)).toBe(true);
  expect(symptomsOffered(photosOnly)).toBe(false);
});

// --- unknown is no, never yes -----------------------------------------------
// While the status is loading, or when the call fails, a card must not flash
// up and then vanish, and a reviewer must never find a button that cannot work.

test('an unknown status offers nothing', () => {
  expect(photoDiagnosisOffered(undefined)).toBe(false);
  expect(symptomsOffered(undefined)).toBe(false);
});

test('a malformed status offers nothing rather than throwing', () => {
  const partial = {} as unknown as AiStatus;
  expect(photoDiagnosisOffered(partial)).toBe(false);
  expect(symptomsOffered(partial)).toBe(false);
  const emptyName: AiStatus = { ...production, advisor_symptoms_backend: '' };
  expect(symptomsOffered(emptyName)).toBe(false);
});

// --- the keys are the server's ---------------------------------------------
// GET /ai/status is spelled in garden-gnome/app/routers/ai.py and its vision
// block in garden-gnome/app/services/vision.py. A rename on either side must
// fail here, not on a phone as a feature that silently never appears.

test('the status keys the client reads are the ones the server sends', () => {
  const route = readSrc('../../../garden-gnome/app/routers/ai.py');
  expect(route).toContain('"advisor_symptoms_backend":');
  expect(route).toContain('"vision":');

  const vision = readSrc('../../../garden-gnome/app/services/vision.py');
  expect(vision).toContain('"ready":');
  expect(vision).toContain('"backend":');
});

test('the client asks the route the server serves', () => {
  const api = readSrc('../api/aiStatus.ts');
  expect(api).toContain("'/ai/status'");
  const route = readSrc('../../../garden-gnome/app/routers/ai.py');
  expect(route).toContain('prefix="/ai"');
  expect(route).toContain('@router.get("/status")');
});
