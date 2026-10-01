import {
  SURFACES, SURFACE_LABEL, IS_BED, GOALS,
  climateForSurface, typeForSurface, dimensionPrompts, uncheckedNotes,
} from './realEstate';
import { GrowingSurface } from '../types';

describe('surfaces', () => {
  it('labels and classifies every surface — a missing one renders blank', () => {
    for (const s of SURFACES) {
      expect(SURFACE_LABEL[s]).toBeTruthy();
      expect(typeof IS_BED[s]).toBe('boolean');
      expect(climateForSurface(s)).toBeTruthy();
      expect(typeForSurface(s)).toBeTruthy();
    }
  });

  it('puts beds outdoors in the sun and sills indoors', () => {
    expect(climateForSurface('raised_bed')).toEqual({
      shelter: 'exposed', temp_exposure: 'outdoor', sun_exposure: 'full_sun',
    });
    expect(climateForSurface('windowsill').temp_exposure).toBe('indoor');
    expect(climateForSurface('shelf_or_floor').sun_exposure).toBe('shade');
  });

  it('keeps a greenhouse on the outside temperature — glass stops rain, not winter', () => {
    const glass = climateForSurface('greenhouse_bench');
    expect(glass.shelter).toBe('sheltered');
    expect(glass.temp_exposure).toBe('outdoor');
  });
});

describe('dimension prompts', () => {
  it('asks a bed about soil and a shelf about the pot', () => {
    expect(dimensionPrompts('in_ground_bed').depth.label).toMatch(/Soil depth/);
    expect(dimensionPrompts('containers').depth.label).toMatch(/Pot depth/);
    expect(dimensionPrompts('pond_or_water').depth.label).toMatch(/Water depth/);
  });

  it('still asks all three before a surface is chosen', () => {
    const p = dimensionPrompts(null);
    expect(p.area.label).toBeTruthy();
    expect(p.headroom.label).toBeTruthy();
    expect(p.depth.label).toBeTruthy();
  });

  it('gives every prompt a hint saying what to measure', () => {
    const surfaces: (GrowingSurface | null)[] = [null, ...SURFACES];
    for (const s of surfaces) {
      const p = dimensionPrompts(s);
      for (const prompt of [p.area, p.headroom, p.depth]) {
        expect(prompt.hint.length).toBeGreaterThan(10);
      }
    }
  });
});

describe('goals', () => {
  it('offers exactly the three the setup asks about', () => {
    expect(GOALS.map((g) => g.value)).toEqual(
      ['edible', 'low_upkeep', 'pollinators']);
  });

  it('describes each as a narrowing, never a loosening', () => {
    for (const g of GOALS) {
      expect(g.hint).toMatch(/^Only species/);
    }
  });
});

describe('unchecked notes', () => {
  const candidate = (axes: string[]) => ({
    species_id: 1, common_name: 'X', scientific_name: 'X x', score: axes.length,
    fits: axes.map((axis) => ({
      axis: axis as any, verdict: 'fits' as const, sentence: 's', borrowed: false,
    })),
  });

  it('says indoor light is not checked, because it cannot be', () => {
    const notes = uncheckedNotes(
      { temp_exposure: 'indoor', goals: null, area_sqft: null, headroom_in: null },
      [candidate(['indoor_outdoor'])]);
    expect(notes.join(' ')).toMatch(/Indoor light isn’t checked/);
  });

  it('says so when a goal was asked for and nothing could answer it', () => {
    const notes = uncheckedNotes(
      { temp_exposure: 'outdoor', goals: ['edible'], area_sqft: null, headroom_in: null },
      [candidate(['sun', 'soil'])]);
    expect(notes.join(' ')).toMatch(/Nothing here is filtered by what you asked for/);
    expect(notes.join(' ')).toMatch(/something to eat/);
  });

  it('stays quiet about a goal the catalog did answer', () => {
    const notes = uncheckedNotes(
      { temp_exposure: 'outdoor', goals: ['edible'], area_sqft: null, headroom_in: null },
      [candidate(['sun', 'goal'])]);
    expect(notes.join(' ')).not.toMatch(/Nothing here is filtered/);
  });

  it('says measurements went unused when no candidate confirmed a footprint', () => {
    const notes = uncheckedNotes(
      { temp_exposure: 'outdoor', goals: null, area_sqft: 32, headroom_in: 84 },
      [candidate(['sun'])]);
    expect(notes.join(' ')).toMatch(/Size isn’t checked/);
  });

  it('says nothing about size when the area was never measured', () => {
    const notes = uncheckedNotes(
      { temp_exposure: 'outdoor', goals: null, area_sqft: null, headroom_in: null },
      [candidate(['sun'])]);
    expect(notes.join(' ')).not.toMatch(/Size isn’t checked/);
  });

  it('is silent when every axis the space turns on was answered', () => {
    const notes = uncheckedNotes(
      { temp_exposure: 'outdoor', goals: ['edible'], area_sqft: 32, headroom_in: 84 },
      [candidate(['sun', 'goal', 'footprint'])]);
    expect(notes).toEqual([]);
  });
});
