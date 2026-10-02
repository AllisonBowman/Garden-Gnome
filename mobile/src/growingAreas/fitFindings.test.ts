import { AXIS_LABEL, CHECK_FAILED, findingHeading, findingLabel } from './fitFindings';
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
