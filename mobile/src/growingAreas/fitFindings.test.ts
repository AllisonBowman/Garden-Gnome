import {
  AXIS_LABEL, CHECK_FAILED, confirmedLine, findingHeading, findingLabel, joinAnd,
  misfitIntro, misfitsOf, plantTitle, speciesFitNote,
} from './fitFindings';
import type { FitAxis, FitFinding, SpeciesFit } from '../api/growingAreas';

const finding = (over: Partial<FitFinding> = {}): FitFinding => ({
  axis: 'sun', verdict: 'misfits',
  sentence: 'This spot gets 6+ hours of direct sun; sources record it for part shade.',
  borrowed: false, ...over,
});

describe('finding labels', () => {
  it('names every axis the server sends in words, never as a token', () => {
    const axes: FitAxis[] = ['indoor_outdoor', 'sun', 'soil', 'footprint', 'upkeep', 'goal'];
    for (const axis of axes) {
      expect(AXIS_LABEL[axis]).toBeTruthy();
      expect(findingLabel(finding({ axis }))).not.toMatch(/_/);
    }
  });

  it('calls a goal finding by its goal, so two goals are told apart', () => {
    expect(findingLabel(finding({ axis: 'goal', goal: 'edible' }))).toBe('Something to eat');
    expect(findingLabel(finding({ axis: 'goal', goal: 'pollinators' }))).toBe('Feeds pollinators');
    expect(findingLabel(finding({ axis: 'upkeep', goal: 'low_upkeep' }))).toBe('Low upkeep');
  });

  it('keeps an axis from a newer server readable', () => {
    expect(findingLabel(finding({ axis: 'soil_depth' as FitAxis }))).toBe('Soil depth');
  });
});

describe('finding headings', () => {
  it('names the axis and whose word it is', () => {
    expect(findingHeading(finding({ authorities: ['NC State Extension'] })))
      .toBe('Sun · NC State Extension');
  });

  it('lists every authority a size finding rests on', () => {
    expect(findingHeading(finding({
      axis: 'footprint', authorities: ['Royal Horticultural Society', 'Missouri Botanical Garden'],
    }))).toBe('Size · Royal Horticultural Society, Missouri Botanical Garden');
  });

  it('says only the axis when nobody is cited — it never invents a source', () => {
    expect(findingHeading(finding({ authorities: [] }))).toBe('Sun');
    expect(findingHeading(finding({ borrowed: true }))).toBe('Sun');
    // A server older than `authorities` sends none at all.
    expect(findingHeading(finding())).toBe('Sun');
  });
});

describe('a failed check', () => {
  it('is never worded as an all-clear', () => {
    expect(CHECK_FAILED).toMatch(/isn’t an all-clear/);
    expect(CHECK_FAILED).not.toMatch(/nothing here contradicts/i);
  });
});

describe('the confirmed line', () => {
  it('lists the confirmed axes once each, in the order the server gave them', () => {
    expect(confirmedLine([
      finding({ axis: 'indoor_outdoor', verdict: 'fits' }),
      finding({ axis: 'sun', verdict: 'fits' }),
      finding({ axis: 'goal', verdict: 'fits', goal: 'edible' }),
      finding({ axis: 'goal', verdict: 'fits', goal: 'pollinators' }),
    ])).toBe('Confirmed here: indoors or out, sun, something to eat and feeds pollinators.');
  });

  it('never counts an unknown or a misfit as a reason', () => {
    expect(confirmedLine([
      finding({ axis: 'sun', verdict: 'unknown' }),
      finding({ axis: 'soil', verdict: 'misfits' }),
      finding({ axis: 'footprint', verdict: 'fits' }),
    ])).toBe('Confirmed here: size.');
    expect(confirmedLine([finding({ verdict: 'unknown' })])).toBeNull();
    expect(confirmedLine([])).toBeNull();
  });

  it('joins lists the way a sentence does', () => {
    expect(joinAnd([])).toBe('');
    expect(joinAnd(['sun'])).toBe('sun');
    expect(joinAnd(['sun', 'soil'])).toBe('sun and soil');
    expect(joinAnd(['sun', 'soil', 'size'])).toBe('sun, soil and size');
  });
});

describe('what Add Plant says about the chosen spot', () => {
  const answer = (findings: FitFinding[], candidate: boolean): SpeciesFit => ({
    species_id: 7, common_name: 'Hosta', scientific_name: 'Hosta sieboldiana',
    score: findings.filter((f) => f.verdict === 'fits').length, candidate, findings,
  });

  it('lists misfits one by one and adds no summary over them', () => {
    const fit = answer([
      finding({ axis: 'indoor_outdoor', verdict: 'fits' }),
      finding({ axis: 'sun', verdict: 'misfits', authorities: ['NC State Extension'] }),
      finding({ axis: 'footprint', verdict: 'unknown' }),
    ], false);
    expect(misfitsOf(fit.findings).map((f) => f.axis)).toEqual(['sun']);
    expect(speciesFitNote(fit, 'Back bed')).toBeNull();
    expect(misfitIntro('Back bed')).toBe('Worth knowing before it goes in Back bed');
  });

  it('says what was confirmed and what is not known when nothing is against it', () => {
    const fit = answer([
      finding({ axis: 'indoor_outdoor', verdict: 'fits' }),
      finding({ axis: 'sun', verdict: 'fits' }),
      finding({ axis: 'footprint', verdict: 'unknown' }),
    ], true);
    expect(speciesFitNote(fit, 'Back bed')).toBe(
      'Nothing on record against it in Back bed. Confirmed: indoors or out and sun. '
      + 'Not known: size.');
  });

  it('never lets "nothing against it" pass for a fit when nothing was judged', () => {
    // Zero misfits because nothing is known is not a recommendation — the
    // Candidate rule's second half, as Add Plant says it.
    const fit = answer([
      finding({ axis: 'indoor_outdoor', verdict: 'unknown' }),
      finding({ axis: 'sun', verdict: 'unknown' }),
    ], false);
    const note = speciesFitNote(fit, 'Back bed')!;
    expect(note).toMatch(/can’t judge it for Back bed/);
    expect(note).toMatch(/no recommendation either way/);
    expect(note).not.toMatch(/Confirmed/);
  });
});

describe('a plant named on the needs-addressing card', () => {
  it('names the species beside a nickname of the gardener’s own', () => {
    expect(plantTitle('Big Blue', 'Hosta')).toEqual({ name: 'Big Blue', species: 'Hosta' });
  });

  it('does not repeat a species the nickname already says', () => {
    // A plant saved with no nickname is named by the server from its species.
    expect(plantTitle('Hosta', 'Hosta')).toEqual({ name: 'Hosta', species: null });
    expect(plantTitle('hosta', 'Hosta')).toEqual({ name: 'hosta', species: null });
    expect(plantTitle('Hosta — north wall', 'Hosta'))
      .toEqual({ name: 'Hosta — north wall', species: null });
  });

  it('falls back to the species when there is no nickname at all', () => {
    expect(plantTitle('', 'Hosta')).toEqual({ name: 'Hosta', species: null });
    expect(plantTitle(null, 'Hosta')).toEqual({ name: 'Hosta', species: null });
  });

  it('still names the species when a nickname merely starts with it', () => {
    expect(plantTitle('Hostas by the gate', 'Hosta'))
      .toEqual({ name: 'Hostas by the gate', species: 'Hosta' });
  });
});
