// The consent copy on a phone set to Spanish. The English tests (copy.test.ts)
// pin what each sentence claims; these pin that a Spanish phone gets Spanish,
// assembled the same way.

type Globals = { __TEST_LOCALES__?: string[] };

function loadInSpanish<T>(id: string): T {
  (globalThis as Globals).__TEST_LOCALES__ = ['es-US'];
  let mod: T | undefined;
  jest.isolateModules(() => { mod = require(id); });
  return mod!;
}

afterEach(() => { delete (globalThis as Globals).__TEST_LOCALES__; });

test('every flow, notice and label is in Spanish', () => {
  const copy = loadInSpanish<typeof import('./copy')>('./copy');
  expect(copy.DESTINATION_LABELS.device).toBe('Se queda en tu teléfono');
  expect(copy.CENSUS_CONSENT.label).toBe('Unirme al censo comunitario');
  expect(copy.PHOTO_DIAGNOSIS_NOTICE.cancelLabel).toBe('Ahora no');
  const census = copy.DATA_FLOWS.find((f) => f.id === 'census')!;
  expect(census.title).toBe('El censo comunitario');
  // The census detail and the switch's text carry the same Spanish list.
  for (const text of [census.detail, copy.CENSUS_CONSENT.on]) {
    expect(text).toContain(copy.CENSUS_FIELDS);
    expect(text).toContain(copy.CENSUS_LEFT_OUT);
    expect(text).toContain(copy.CENSUS_LINKING);
    expect(text).not.toMatch(/\{\{|\}\}/);
  }
  // The off text points at the census entry by its Spanish title.
  expect(copy.CENSUS_CONSENT.off).toContain(`«${census.title}»`);
  for (const f of copy.DATA_FLOWS) {
    expect(`${f.title} ${f.summary} ${f.detail}`).not.toMatch(/\b(the|your|and)\b/);
  }
});

test('the voice flow names the capture screen as the Spanish screens do', () => {
  const copy = loadInSpanish<typeof import('./copy')>('./copy');
  const voice = copy.DATA_FLOWS.find((f) => f.id === 'voice')!;
  expect(voice.detail).toMatch(/^Recorre el jardín/);
});

test('the error card and the report email speak Spanish', () => {
  const report = loadInSpanish<typeof import('../components/errorReport')>('../components/errorReport');
  const mailto = report.buildProblemMailto({
    supportEmail: 'support@example.com', appVersion: '1.2.0', platform: 'ios', where: 'Home', error: new Error('x'),
  });
  expect(decodeURIComponent(mailto)).toContain('Reportar un problema en PlantAdvocate');
  expect(decodeURIComponent(mailto)).toContain('Cuéntanos qué estabas haciendo');
});
