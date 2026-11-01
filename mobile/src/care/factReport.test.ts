// "Report a fact" is a prefilled email, so what that email says is the whole
// feature. This pins it: the species named, the page's facts as shown, the
// question asked, and the existing result reports left as they were. It also
// checks that the species page offers the link with its sources.
//
// support.ts and the components import React Native, which this jest setup
// can't load (see jest.config.js), so the modules they touch are stood in
// for by name and the components are called directly, as
// ErrorBoundary.test.ts does.
jest.mock('react-native', () => ({
  Platform: { OS: 'ios' },
  Alert: { alert: jest.fn() },
  Linking: { openURL: jest.fn() },
  StyleSheet: { create: (s: unknown) => s },
}));
jest.mock('react-native-paper', () => ({ Button: 'Button' }));
jest.mock('../theme/ThemeProvider', () => ({ useAppTheme: jest.fn() }));

import { reportedFacts } from './factReport';
import { Species } from '../types';
import { APP_VERSION, SUPPORT_EMAIL, buildReportMailto } from '../support';
import ReportFact from '../components/ReportFact';
import ReportResult, { reportLinkLabel } from '../components/ReportResult';

declare const require: (id: string) => any;
declare const __dirname: string;

// Pothos as App Store shot 6 shows it.
const POTHOS_HAZARD = 'Toxic to cats, dogs and people: all parts (calcium oxalate crystals) — '
  + 'mouth irritation, drooling and swelling if chewed. NC State Extension rates its poison '
  + 'severity for people medium. Keep it out of reach of pets and children. If you suspect '
  + 'poisoning, call Poison Control (US 1-800-222-1222) or a vet right away.';
const POTHOS_NOTES = 'Forgiving vining plant. Let top 1-2 inches dry out. Leaves curl when thirsty.';

function pothos(over: Partial<Species> = {}): Species {
  return {
    id: 7, common_name: 'Pothos', scientific_name: 'Epipremnum aureum',
    toxicity_description: POTHOS_HAZARD, toxic_to_pets: true,
    water_regime: 'dry_thoroughly_between',
    light_fc_min: 100, light_fc_good: 200,
    humidity_need: 'average',
    day_f_min: 70, day_f_max: 85, night_f_min: 60, night_f_max: 70,
    soil_drainage: 'moderate',
    fertilize_interval_days: 60,
    climbs: true,
    care_data_status: 'sourced',
    care_provenance: {},
    care_notes: POTHOS_NOTES,
    ...over,
  } as Species;
}

/** A mailto URL taken apart the way a mail app reads it. */
function opened(url: string) {
  const [to, query] = url.replace(/^mailto:/, '').split('?');
  const fields: Record<string, string> = {};
  for (const pair of query.split('&')) {
    const [key, value] = pair.split('=');
    fields[key] = decodeURIComponent(value);
  }
  return { to, subject: fields.subject, body: fields.body.split('\n') };
}

const ASK = 'Which fact looks wrong, and why? A link to where you read otherwise helps us check it.';

test('the report carries the page’s facts, hazard first, in the page’s words', () => {
  expect(reportedFacts(pothos()).split('\n')).toEqual([
    POTHOS_HAZARD,
    'Watering: Let the medium dry thoroughly between waterings',
    'Light: At least 100 footcandles; 200 footcandles is comfortable',
    'Humidity: Average room humidity',
    'Temperature: Days 70–85°F; nights 60–70°F',
    'Soil: Moderately draining',
    'Fertilize: Every 60 days',
    'Where it lives: A climber that needs a support',
    `Care notes: ${POTHOS_NOTES}`,
  ]);
});

test('a borrowed value and an uncited one say so, as they do on the page', () => {
  const lines = reportedFacts(pothos({
    care_provenance: { humidity_need: 'genus_inferred' },
    day_f_min: null, day_f_max: null, night_f_min: null, night_f_max: null,
    temp_f_min: 60, temp_f_max: 85,
  })).split('\n');
  expect(lines).toContain('Humidity (genus-inferred): Average room humidity');
  expect(lines).toContain('Temp (from the catalog — not yet cited): 60–85°F');
  expect(lines.some((l) => l.startsWith('Temperature:'))).toBe(false);
});

test('nothing is added that the page does not show', () => {
  const bare = { id: 1, common_name: 'Fern', scientific_name: 'Polypodium', care_notes: '' } as Species;
  expect(reportedFacts(bare)).toBe('');
  // An older server's bare flag is shown as a chip; the report says the same.
  expect(reportedFacts({ ...bare, toxic_to_pets: true })).toBe('⚠️ Toxic to pets');
  expect(reportedFacts({ ...bare, toxic_to_pets: false })).toBe('');
});

test('the species page’s link opens a mail naming the species, with its facts', () => {
  const link = ReportFact({ species: pothos() });
  expect(link.type).toBe(ReportResult);
  const { surfaceLabel, result, context } = link.props;
  expect(reportLinkLabel(surfaceLabel)).toBe('Report a fact');

  const mail = opened(buildReportMailto(surfaceLabel, result, context));
  expect(mail.to).toBe(SUPPORT_EMAIL);
  expect(mail.subject).toBe('Report a fact');
  expect(mail.body[0]).toBe(ASK);
  const shown = mail.body.indexOf('——— What the page says ———');
  expect(shown).toBeGreaterThan(0);
  expect(mail.body.slice(shown + 1, shown + 3))
    .toEqual(['Species: Pothos (Epipremnum aureum)', POTHOS_HAZARD]);
  expect(mail.body).toContain(`Care notes: ${POTHOS_NOTES}`);
  expect(mail.body.slice(-2)).toEqual(['———', `App: PlantAdvocate ${APP_VERSION} (ios)`]);
});

test('a long page is cut at the end, so the species and the hazard always arrive', () => {
  const species = pothos({ care_notes: 'Long. '.repeat(400) });
  const link = ReportFact({ species });
  const mail = opened(buildReportMailto(link.props.surfaceLabel, link.props.result, link.props.context));
  expect(mail.body).toContain('Species: Pothos (Epipremnum aureum)');
  expect(mail.body).toContain(POTHOS_HAZARD);
  expect(mail.body[mail.body.length - 3].endsWith('…')).toBe(true);
});

test.each([
  ['diagnosis', 'Report a diagnosis result'],
  ['care advice', 'Report a care advice result'],
] as const)('a %s report reads as it did before', (surface, subject) => {
  const mail = opened(buildReportMailto(surface, 'Brown spots on two leaves.', ['Plant: Fern']));
  expect(mail.subject).toBe(subject);
  expect(mail.body.slice(0, 5)).toEqual([
    'Tell us what was wrong or inappropriate about this result:', '', '',
    '——— Reported result ———', 'Plant: Fern',
  ]);
  expect(reportLinkLabel(surface)).toBe('Report this result');
});

test('the species page offers the link under its sources, or alone without them', () => {
  const src: string = require('fs').readFileSync(
    require('path').join(__dirname, '../screens/SpeciesDetailScreen.tsx'), 'utf8');
  expect(src).toMatch(/import ReportFact from '\.\.\/components\/ReportFact'/);
  const rows = src.indexOf('<CareSourceRows');
  const cardEnd = src.indexOf('</Card>', rows);
  const schedule = src.indexOf('Recommended schedule');
  expect(rows).toBeGreaterThan(-1);
  expect(schedule).toBeGreaterThan(cardEnd);
  const links = [...src.matchAll(/<ReportFact\b/g)].map((m) => m.index!);
  // At the foot of the Sources card, after the source rows...
  expect(links.some((at) => at > rows && at < cardEnd)).toBe(true);
  // ...and in the same spot for a species with no sources yet, whose
  // values are the likeliest to be wrong. Never down by the schedule.
  expect(links.some((at) => at > cardEnd && at < schedule)).toBe(true);
  for (const at of links) expect(at).toBeLessThan(schedule);
});
