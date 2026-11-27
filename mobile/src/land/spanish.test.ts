// The land and zone words in Spanish, on a phone set to es-MX.
type G = { __TEST_LOCALES__?: string[] };

afterEach(() => { delete (globalThis as G).__TEST_LOCALES__; });

function inSpanish<T>(path: string): T {
  (globalThis as G).__TEST_LOCALES__ = ['es-MX'];
  let mod: T | undefined;
  jest.isolateModules(() => { mod = require(path); });
  return mod!;
}

test('setup, the property page and the reading tiles speak Spanish', () => {
  const setup = inSpanish<typeof import('./setup')>('./setup');
  expect(setup.LOT_CONTENT_LABELS.lawn).toBe('Césped');
  const rows = inSpanish<typeof import('./profileRows')>('./profileRows');
  expect(rows.USE_ESTIMATE_LABEL).toBe('Usar la lectura de datos públicos');
  // The server's English confidence label is shown in Spanish.
  expect(rows.publicLine({ public: { display: 'Arcilla', confidence_label: 'Rough estimate' } } as never))
    .toBe('Lectura de datos públicos: Arcilla (Estimación aproximada).');
  const tiles = inSpanish<typeof import('./readingTiles')>('./readingTiles');
  expect(tiles.SUN_GAUGE_LABELS.end).toBe('12 horas');
  expect(tiles.HARDINESS_GAUGE_LABELS.start).toBe('Zona 1, la más fría');
});

test('the map description and layers speak Spanish', () => {
  const layers = inSpanish<typeof import('./mapLayers')>('./mapLayers');
  expect(layers.AERIAL_LABEL).toBe('Aérea');
  expect(layers.mapA11yLabel({ zoneNames: ['Huerto', 'Césped'], hasPin: true }))
    .toBe('Imagen aérea vista desde arriba de tu terreno. 2 zonas marcadas: Huerto, Césped. Tu marcador está señalado.');
});

test('zones speak Spanish, with plurals', () => {
  const d = inSpanish<typeof import('../zones/describe')>('../zones/describe');
  expect(d.DEFAULT_YARD_MAP_NAME).toBe('Tu patio');
  expect(d.deleteBlockedReason({ is_whole_lot: false, plant_count: 1 }))
    .toBe('Esta zona tiene 1 planta, así que no se puede eliminar. Primero muévela a otro espacio.');
  expect(d.deleteBlockedReason({ is_whole_lot: false, plant_count: 3 }))
    .toBe('Esta zona tiene 3 plantas, así que no se puede eliminar. Primero muévelas a otro espacio.');
  expect(d.defaultZoneName('tree', ['Árboles'])).toBe('Árboles 2');
});
