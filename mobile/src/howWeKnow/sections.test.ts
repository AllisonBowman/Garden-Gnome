// Moving justification behind a tap must not lose any of it: every reason,
// source, confidence and note a face used to show is in the sheet.
import { allSourceLines, homeSections, landSections, seasonSections } from './sections';
import { Explained, SiteProfile, SiteValue, Vitals } from '../types/site';
import { setTempUnitForFormatting } from '../units/temperature';

const ex = (display: string, source: string): Explained => ({
  display, confidence: 'rough_estimate', confidence_label: 'Rough estimate', reason: `Because ${display}`,
  sources: [{ name: source }], provenance: 'public_map',
});
const sv = (field: SiteValue['field'], source: string): SiteValue => ({
  ...ex(field, source), field, title: field, value: null, zone_id: null, can_override: true,
  override_choices: [], override_kind: 'choice',
});

afterEach(() => setTempUnitForFormatting('F'));

test('Home’s sheet holds the weather credit, every card, land value, task, event and note', () => {
  const vitals = {
    generated_at: '', headline: 'Frost tonight. More.', cards: [], this_week: [], season_ahead: [], spaces: [],
    notes: ['Weather alerts use the last forecast.'],
    forecast: { provider: 'nws', provider_name: 'National Weather Service', fetched_at: '', days: [] },
  } as unknown as Vitals;
  const sections = homeSections({
    vitals,
    headline: { fromServer: true, full: 'Frost tonight. More.' },
    weatherCards: [{ key: 'frost', title: 'Frost', value_text: 'Possible tonight', detail: '', tone: 'act', explained: ex('x', 'NWS forecast') }],
    land: [{ title: 'Sun', explained: ex('About 7 hours', 'USGS 3DEP elevation') }],
    progress: 'Some public maps could not be reached. PlantAdvocate will try them again.',
    week: [{ kind: 'season', key: 'season:a', text: 'Cover tender plants', lowImpactNote: null, reason: 'Frost', sources: [{ name: 'Extension' }], eventKey: 'e', state: 'open' }],
    seasonAhead: [{ event_key: 'e', type: 'first_frost', title: 'First frost', status: 'forecast', window: { text: 'Thu' }, explained: ex('First frost', 'NOAA normals'), owner_actions: [] } as never],
    legacyCredit: null,
    forecastWhen: 'Tue 24 Nov, 2 pm',
  });
  const text = JSON.stringify(sections);
  expect(allSourceLines(sections)).toEqual(expect.arrayContaining(['NWS forecast', 'USGS 3DEP elevation', 'Extension', 'NOAA normals']));
  expect(text).toContain('Forecast from National Weather Service, fetched Tue 24 Nov, 2 pm.');
  expect(text).toContain('Today’s full note: Frost tonight. More.');
  expect(text).toContain('Some public maps could not be reached');
  expect(text).toContain('Weather alerts use the last forecast.');
  expect(text).toContain('September 1');
  expect(text).toContain('“est.”');
  expect(text).not.toContain('arrive in °F');
});

test('the °F note shows when temperatures are in °C', () => {
  setTempUnitForFormatting('C');
  const s = seasonSections({ events: [], forecastCredit: null });
  expect(JSON.stringify(s)).toContain('arrive in °F');
});

test('Your land’s sheet holds every value on the lot, the map layer, zones and notes', () => {
  const profile: SiteProfile = {
    property_id: 1, status: { fast: 'ready', background: 'ready' },
    values: [sv('sun', 'Lidar'), sv('soil_texture', 'NRCS SSURGO')],
    zones: [{ zone_id: 7, name: 'Bed', is_whole_lot: false, values: [sv('sun', 'Zone lidar')] } as never],
    notes: ['Buildings are not counted.'],
  };
  const sections = landSections({ profile, progress: null, layer: { title: 'Sun', explained: ex('Sun layer', 'NAIP imagery'), notes: ['Trees in leaf.'] } as never });
  expect(allSourceLines(sections)).toEqual(expect.arrayContaining(['Lidar', 'NRCS SSURGO', 'Zone lidar', 'NAIP imagery']));
  const text = JSON.stringify(sections);
  expect(text).toContain('Buildings are not counted.');
  expect(text).toContain('Trees in leaf.');
});
