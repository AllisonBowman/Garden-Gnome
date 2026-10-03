import {
  SURFACES, SURFACE_LABEL, IS_BED, GOALS, AREA_TYPES, SUN_HINT,
  climateForSurface, areaTypeLabel, dimensionPrompts, uncheckedNotes,
  goalPhrase, goalsAnswered, lengthEcho, measuredLength, surfaceName,
} from './realEstate';
import { GrowingGoal, GrowingSurface } from '../types';
import type { FitFinding } from '../api/growingAreas';

describe('surfaces', () => {
  it('labels and classifies every surface — a missing one renders blank', () => {
    for (const s of SURFACES) {
      expect(SURFACE_LABEL[s]).toBeTruthy();
      expect(typeof IS_BED[s]).toBe('boolean');
      expect(climateForSurface(s)).toBeTruthy();
    }
  });

  it('puts beds outdoors in the sun and sills indoors', () => {
    expect(climateForSurface('raised_bed')).toEqual({
      shelter: 'exposed', temp_exposure: 'outdoor', sun_exposure: 'full_sun',
    });
    expect(climateForSurface('windowsill').temp_exposure).toBe('indoor');
    expect(climateForSurface('shelf_or_floor').sun_exposure).toBe('shade');
  });

  it('names a surface in quotes without the icon its chip wears', () => {
    expect(surfaceName('raised_bed')).toBe('Raised bed');
    for (const s of SURFACES) {
      expect(surfaceName(s)).toMatch(/^[A-Z][a-z-]+( [a-z]+)*$/);
    }
  });

  it('keeps a greenhouse on the outside temperature — glass stops rain, not winter', () => {
    const glass = climateForSurface('greenhouse_bench');
    expect(glass.shelter).toBe('sheltered');
    expect(glass.temp_exposure).toBe('outdoor');
  });
});

describe('the sun setting', () => {
  it('is defined in hours where it is chosen, in the bands the engine reads', () => {
    // fit._AREA_SUN_WORDS: 6+ / 3-6 / under 3 hours of direct sun.
    expect(SUN_HINT).toMatch(/full sun is 6 or more/);
    expect(SUN_HINT).toMatch(/partial 3 to 6/);
    expect(SUN_HINT).toMatch(/shade under 3/);
  });
});

describe('the kind of place', () => {
  it('names every type the setup offers in words, not a bare icon', () => {
    for (const t of AREA_TYPES) {
      // An emoji, then at least one word.
      expect(areaTypeLabel(t)).toMatch(/^\S+ [A-Z][a-z]+/);
    }
    expect(areaTypeLabel('community_garden')).toBe('🌳 Community garden');
  });

  it('still says a type the server knows and this build does not in words', () => {
    expect(areaTypeLabel('greenhouse')).toBe('🏕️ Greenhouse');
    expect(areaTypeLabel('rooftop_farm')).toBe('Rooftop farm');
  });

  it('is never preset from the surface — a raised bed is not a community plot', () => {
    // The climate preset is all a surface decides; who keeps the space is asked.
    expect(Object.keys(climateForSurface('raised_bed')).sort())
      .toEqual(['shelter', 'sun_exposure', 'temp_exposure']);
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

  it('says where a depth is asked that nothing checks a plant against it', () => {
    // No fit axis reads soil_depth_in; a field that silently does nothing
    // breaks the form's promise that what's given here shapes the suggestions.
    for (const s of [null, ...SURFACES]) {
      expect(dimensionPrompts(s).depth.hint).toMatch(/no plant is checked against it yet/);
    }
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

describe('a measured length, shown back', () => {
  it('is said the way the reasons say it, beside the inches typed', () => {
    // "there is 7 ft of headroom" in a reason, and 84 in on the card, read as
    // two different numbers until the card says both.
    expect(measuredLength(84)).toBe('7 ft (84 in)');
    expect(measuredLength(87)).toBe('7.3 ft (87 in)');
  });

  it('stays in inches where the reasons do', () => {
    expect(measuredLength(12)).toBe('12 in');
    expect(measuredLength(18.5)).toBe('18.5 in');
  });

  it('is echoed under the field as it is typed, once it would be said in feet', () => {
    expect(lengthEcho('84')).toBe('That’s 7 ft.');
    expect(lengthEcho('12')).toBeNull();
    expect(lengthEcho('')).toBeNull();
    expect(lengthEcho('0')).toBeNull();
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
  // An axis name, or `axis:goal` for a finding the server tagged with the
  // goal it answers ("goal:edible", "upkeep:low_upkeep").
  const candidate = (axes: string[]) => ({
    species_id: 1, common_name: 'X', scientific_name: 'X x', score: axes.length,
    fits: axes.map((spec) => {
      const [axis, goal] = spec.split(':');
      return {
        axis: axis as FitFinding['axis'], verdict: 'fits' as const,
        sentence: 's', borrowed: false,
        ...(goal ? { goal: goal as GrowingGoal } : {}),
      };
    }),
  });

  it('says indoor light is not checked, because it cannot be', () => {
    const notes = uncheckedNotes(
      { temp_exposure: 'indoor', goals: null, area_sqft: null, headroom_in: null },
      [candidate(['indoor_outdoor'])]);
    expect(notes.join(' ')).toMatch(/Indoor light isn’t checked/);
  });

  it('says it in a gardener’s words, not the database’s', () => {
    // A new account's first area is indoors, so this is the first note
    // anyone reads; "the old light column" and "footcandles" were on it.
    const [note] = uncheckedNotes(
      { temp_exposure: 'indoor', goals: null, area_sqft: null, headroom_in: null }, []);
    expect(note).not.toMatch(/column|footcandle|catalog/i);
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

  it('says a measured depth narrowed nothing, in the words the form asked it', () => {
    const bed = uncheckedNotes(
      { temp_exposure: 'outdoor', goals: null, area_sqft: null, headroom_in: null,
        surface: 'raised_bed', soil_depth_in: 12 },
      [candidate(['sun'])]);
    expect(bed).toEqual(
      ['Soil depth isn’t checked: nothing on this list was compared with the 12 in you measured.']);
    const pots = uncheckedNotes(
      { temp_exposure: 'outdoor', goals: null, area_sqft: null, headroom_in: null,
        surface: 'containers', soil_depth_in: 10 },
      [candidate(['sun'])]);
    expect(pots[0]).toMatch(/^Pot depth isn’t checked/);
  });

  it('says nothing about depth when none was measured', () => {
    const notes = uncheckedNotes(
      { temp_exposure: 'outdoor', goals: null, area_sqft: null, headroom_in: null,
        surface: 'raised_bed', soil_depth_in: null },
      [candidate(['sun'])]);
    expect(notes).toEqual([]);
  });

  it('is silent when every axis the space turns on was answered', () => {
    const notes = uncheckedNotes(
      { temp_exposure: 'outdoor', goals: ['edible'], area_sqft: 32, headroom_in: 84 },
      [candidate(['sun', 'goal', 'footprint'])]);
    expect(notes).toEqual([]);
  });

  it('counts low upkeep as answered when the list was narrowed by it', () => {
    // Low upkeep is answered on its own axis. Reading only the `goal` axis
    // reported it unchecked on every list, including the ones it had shaped.
    const notes = uncheckedNotes(
      { temp_exposure: 'outdoor', goals: ['low_upkeep'], area_sqft: null, headroom_in: null },
      [candidate(['sun', 'upkeep:low_upkeep'])]);
    expect(notes).toEqual([]);
  });

  it('names the goal nothing answered, not the one something did', () => {
    const notes = uncheckedNotes(
      { temp_exposure: 'outdoor', goals: ['edible', 'pollinators'], area_sqft: null, headroom_in: null },
      [candidate(['sun', 'goal:pollinators'])]);
    const text = notes.join(' ');
    expect(text).toMatch(/something to eat/);
    expect(text).not.toMatch(/feeds pollinators/);
  });

  it('reads an untagged goal fit from an older server the way it always did', () => {
    const notes = uncheckedNotes(
      { temp_exposure: 'outdoor', goals: ['edible', 'pollinators'], area_sqft: null, headroom_in: null },
      [candidate(['sun', 'goal'])]);
    expect(notes).toEqual([]);
  });

  it('speaks about the list, never about the whole catalog', () => {
    // The catalog keeps being researched; "no species carries a mature size
    // yet" stayed on screen after the size backfill made it false.
    const notes = uncheckedNotes(
      { temp_exposure: 'outdoor', goals: ['edible'], area_sqft: 32, headroom_in: 84,
        surface: 'raised_bed', soil_depth_in: 12 },
      [candidate(['sun'])]);
    expect(notes).toHaveLength(3);
    for (const note of notes) {
      expect(note).not.toMatch(/in the catalog/);
      expect(note).toMatch(/on this list/);
    }
  });

  it('says only what is true of the space when the list is empty', () => {
    expect(uncheckedNotes(
      { temp_exposure: 'outdoor', goals: ['edible'], area_sqft: 32, headroom_in: 84 },
      [])).toEqual([]);
    const indoor = uncheckedNotes(
      { temp_exposure: 'indoor', goals: ['edible'], area_sqft: 32, headroom_in: 84 },
      []);
    expect(indoor).toHaveLength(1);
    expect(indoor[0]).toMatch(/Indoor light isn’t checked/);
  });
});

describe('goals a finding answers', () => {
  const finding = (axis: FitFinding['axis'], goal?: GrowingGoal | null): FitFinding => ({
    axis, verdict: 'fits', sentence: 's', borrowed: false, goal,
  });

  it('takes the server’s word when it gives one', () => {
    expect(goalsAnswered(finding('goal', 'edible'))).toEqual(['edible']);
    expect(goalsAnswered(finding('upkeep', 'low_upkeep'))).toEqual(['low_upkeep']);
  });

  it('knows low upkeep by its axis, and the space axes answer none', () => {
    expect(goalsAnswered(finding('upkeep'))).toEqual(['low_upkeep']);
    expect(goalsAnswered(finding('sun'))).toEqual([]);
    expect(goalsAnswered(finding('footprint', null))).toEqual([]);
  });

  it('phrases every goal for the middle of a sentence', () => {
    expect(GOALS.map((g) => goalPhrase(g.value))).toEqual(
      ['something to eat', 'low upkeep', 'feeds pollinators']);
  });
});
