import { Species } from '../types';
import { matchSpecies, classifyMatches, CONFIDENT, PLAUSIBLE } from './fuzzyMatch';

// Parity contract shared with the backend eval mirror
// (garden-gnome/evals/fuzzy_mirror.py PARITY_FIXTURES). This TS file is the
// AUTHORITATIVE matcher; the Python port must produce identical tiers/top
// candidates for these fixtures. Keep the two tables byte-identical.

function sp(id: number, common_name: string, scientific_name: string): Species {
  // The matcher reads only id/common_name/scientific_name; fill the rest
  // minimally to satisfy the type.
  return {
    id, common_name, scientific_name,
    light_need: 'medium', humidity_pct_min: 0, humidity_pct_max: 0,
    temp_f_min: 0, temp_f_max: 0, soil_type: '', toxic_to_pets: false,
    care_notes: '',
  };
}

const FIXTURE_CATALOG: Species[] = [
  sp(1, 'Snake Plant', 'Dracaena trifasciata'),
  sp(2, 'Pothos', 'Epipremnum aureum'),
  sp(3, 'Monstera', 'Monstera deliciosa'),
  sp(4, 'Peace Lily', 'Spathiphyllum wallisii'),
  sp(5, 'Aloe Vera', 'Aloe barbadensis'),
];

type Fixture = { aiText: string; tier: 'confident' | 'plausible' | 'none'; top: string | null };

const PARITY_FIXTURES: Fixture[] = [
  { aiText: 'Monstera deliciosa', tier: 'confident', top: 'Monstera' },
  { aiText: 'This looks like a snake plant to me.', tier: 'confident', top: 'Snake Plant' },
  { aiText: 'pothos', tier: 'confident', top: 'Pothos' },
  { aiText: 'Peace lily, maybe?', tier: 'confident', top: 'Peace Lily' },
  { aiText: 'aloe', tier: 'plausible', top: 'Aloe Vera' },
  { aiText: 'UNKNOWN', tier: 'none', top: null },
  { aiText: 'a small orange tabby cat', tier: 'none', top: null },
];

describe('fuzzyMatch parity fixtures', () => {
  it.each(PARITY_FIXTURES)('grounds "$aiText" → $tier / $top', ({ aiText, tier, top }) => {
    const result = classifyMatches(matchSpecies(aiText, FIXTURE_CATALOG));
    expect(result.tier).toBe(tier);
    const gotTop = result.candidates.length ? result.candidates[0].species.common_name : null;
    expect(gotTop).toBe(top);
  });
});

describe('fuzzyMatch thresholds', () => {
  it('keeps the tier boundaries the mirror depends on', () => {
    expect(CONFIDENT).toBe(0.6);
    expect(PLAUSIBLE).toBe(0.42);
  });

  it('never offers a candidate below the plausible floor', () => {
    const result = classifyMatches(matchSpecies('a small orange tabby cat', FIXTURE_CATALOG));
    expect(result.candidates).toHaveLength(0);
  });
});
