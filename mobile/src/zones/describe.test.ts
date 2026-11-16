import {
  correctionBodies, correctionQuestions, defaultZoneBox, defaultZoneName, deleteBlockedReason,
  DEFAULT_SUN_CHOICES, draftProblem, emptyDraft, leafHabitApplies, squareAround, VEGETATION_CHOICES,
  LEAF_HABIT_CHOICES, mapZoneLabel, zoneCreateBody, zoneLabel, zonePatchBody, zoneShownValues, zoneValuesPending,
} from './describe';
import { SiteValue, Zone } from '../types/site';

function value(field: SiteValue['field'], extra: Partial<SiteValue> = {}): SiteValue {
  return {
    field, title: field, display: `${field} display`, confidence: 'area_estimate',
    confidence_label: 'Area estimate', reason: 'r', sources: [{ name: 's' }], provenance: 'modelled',
    can_override: true, override_kind: 'choice',
    override_choices: [{ value: 'a', label: 'A' }], ...extra,
  };
}

const ZONE: Zone = {
  id: 7, growing_area_id: 7, property_id: 1, name: 'Front bed', vegetation_type: 'garden_bed',
  is_whole_lot: false, box: { west: -76.968, south: 38.912, east: -76.9679, north: 38.9121 },
  boundary_source: 'owner', leaf_habit: null, plant_count: 0, values: [],
};

describe('tap choices', () => {
  it('offers the five vegetation types in plain words', () => {
    expect(VEGETATION_CHOICES.map((c) => c.value).sort()).toEqual(['bare_hardscape', 'garden_bed', 'grass', 'shrub', 'tree']);
    for (const c of [...VEGETATION_CHOICES, ...LEAF_HABIT_CHOICES, ...DEFAULT_SUN_CHOICES]) {
      expect(c.label).not.toMatch(/_|—/);
    }
  });
  it('asks leaf habit only for trees and shrubs', () => {
    expect(leafHabitApplies('tree')).toBe(true);
    expect(leafHabitApplies('shrub')).toBe(true);
    expect(leafHabitApplies('grass')).toBe(false);
    expect(leafHabitApplies(null)).toBe(false);
  });
  it('asks sun always and soil only where the server allows a correction', () => {
    const qs = correctionQuestions([], [value('water_collects'), value('soil_texture', { can_override: false })]);
    expect(qs.map((q) => q.field)).toEqual(['sun', 'water_collects']);
    expect(qs[0].choices).toBe(DEFAULT_SUN_CHOICES);
  });
  it("prefers the zone's own choices over the lot's", () => {
    const qs = correctionQuestions([value('sun', { override_choices: [{ value: 'shade', label: 'Shade' }] })], [value('sun')]);
    expect(qs[0].choices).toEqual([{ value: 'shade', label: 'Shade' }]);
  });
});

describe('saving', () => {
  it('needs a vegetation type and a box', () => {
    expect(draftProblem(emptyDraft(), null)).toBe('Choose what grows there.');
    expect(draftProblem({ ...emptyDraft(), vegetation: 'tree' }, null)).toBe('Stretch a box over the area first.');
    expect(draftProblem({ ...emptyDraft(), vegetation: 'tree' }, ZONE.box!)).toBeNull();
  });
  it('names a zone when the owner does not', () => {
    expect(defaultZoneName('garden_bed', ['Garden bed', 'garden bed 2'])).toBe('Garden bed 3');
    expect(zoneCreateBody({ ...emptyDraft(), vegetation: 'grass' }, ZONE.box!, []).name).toBe('Lawn or grass');
  });
  it('sends leaf habit only where it applies', () => {
    const d = { ...emptyDraft(), vegetation: 'grass' as const, leafHabit: 'evergreen' as const };
    expect(zoneCreateBody(d, ZONE.box!, [])).not.toHaveProperty('leaf_habit');
    expect(zoneCreateBody({ ...d, vegetation: 'tree' }, ZONE.box!, []).leaf_habit).toBe('evergreen');
  });
  it('patches only what changed', () => {
    const d = { name: 'Front bed', vegetation: 'garden_bed' as const, leafHabit: null, corrections: {} };
    expect(zonePatchBody(ZONE, d, ZONE.box!)).toEqual({});
    expect(zonePatchBody(ZONE, { ...d, name: 'Roses' }, { ...ZONE.box!, east: -76.9 }))
      .toEqual({ name: 'Roses', box: { ...ZONE.box!, east: -76.9 } });
  });
  it('sends each correction as a tap for the zone', () => {
    expect(correctionBodies(7, { ...emptyDraft(), corrections: { sun: 'shade', water_collects: '' } }))
      .toEqual([{ zone_id: 7, field: 'sun', value: 'shade', method: 'tap' }]);
  });
});

describe('a zone without drawing', () => {
  it("uses the server's approximate yard when there is one", () => {
    const fp = { west: 1, south: 2, east: 3, north: 4 };
    expect(defaultZoneBox({ default_footprint: fp, pin: null }, { lat: 0, lng: 0 })).toBe(fp);
  });
  it('else makes a square of about 8,500 square feet around the pin', () => {
    const b = defaultZoneBox(null, { lat: 38.9123, lng: -76.9681 });
    const widthM = (b.east - b.west) * 111_320 * Math.cos((38.9123 * Math.PI) / 180);
    const heightM = (b.north - b.south) * 111_320;
    expect(widthM * heightM * 10.7639).toBeCloseTo(8500, -1);
    expect(squareAround(0, 0).north).toBeGreaterThan(0);
  });
});

describe('deleting', () => {
  it('says plainly why a zone cannot go', () => {
    expect(deleteBlockedReason({ is_whole_lot: true, plant_count: 0 })).toMatch(/whole yard cannot be deleted/);
    expect(deleteBlockedReason({ is_whole_lot: false, plant_count: 1 })).toBe(
      'This zone has 1 plant in it, so it cannot be deleted. Move it to another space first.');
    expect(deleteBlockedReason({ is_whole_lot: false, plant_count: 3 })).toMatch(/3 plants.*Move them/);
    expect(deleteBlockedReason({ is_whole_lot: false, plant_count: 0 })).toBeNull();
  });
});

describe('what the map shows', () => {
  it('labels the default yard as approximate', () => {
    expect(zoneLabel({ name: 'Whole lot', is_whole_lot: true, boundary_source: 'default' }))
      .toBe('Approximate yard (typical United States lot size, not your property line)');
    expect(zoneLabel({ name: 'Whole lot', is_whole_lot: true, boundary_source: 'owner' })).toBe('Whole lot');
  });
  it('gives the map a short name for the default yard and keeps other names', () => {
    expect(mapZoneLabel({ name: 'Whole lot', is_whole_lot: true, boundary_source: 'default' })).toBe('Your yard');
    expect(mapZoneLabel({ name: 'Back lot', is_whole_lot: true, boundary_source: 'owner' })).toBe('Back lot');
    expect(mapZoneLabel({ name: 'Garden bed', is_whole_lot: false, boundary_source: 'owner' })).toBe('Garden bed');
    // The list under the map keeps the full, careful wording.
    expect(zoneLabel({ name: 'Whole lot', is_whole_lot: true, boundary_source: 'default' }))
      .toMatch(/^Approximate yard/);
  });
  it('shows sun and where water collects once the server has them', () => {
    expect(zoneValuesPending([])).toBe(true);
    const vals = [value('water_collects'), value('slope'), value('sun')];
    expect(zoneShownValues(vals).map((v) => v.field)).toEqual(['sun', 'water_collects']);
    expect(zoneValuesPending(vals)).toBe(false);
    expect(zoneValuesPending([value('sun'), value('water_collects', { confidence: 'not_known_yet' })])).toBe(true);
  });
});
