import {
  AXIS_LABEL, CHECK_FAILED, confirmedLine, findingHeading, findingLabel, joinAnd,
} from './fitFindings';
import type { FitAxis, FitFinding } from '../api/growingAreas';

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
