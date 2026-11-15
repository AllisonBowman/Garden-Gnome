import {
  actionBody, forecastCells, forecastCredit, observedDayChoices, orderedActions, orderedTasks,
  sectionOf, seasonSections, STATUS_WORDS, ACTION_LABELS,
} from './sections';
import { Explained, SeasonEvent, SeasonTask } from '../types/site';

const EXPLAINED: Explained = {
  display: 'x', confidence: 'rough_estimate', confidence_label: 'Rough estimate',
  reason: 'Typical date from station normals.', sources: [{ name: 'National Oceanic and Atmospheric Administration normals' }],
  provenance: 'modelled',
};

function task(key: string, state: SeasonTask['state'] = 'open'): SeasonTask {
  return { task_key: key, text: key, reason: 'r', sources: [{ name: 's' }], applies_to: { kind: 'lot', ids: [] }, state };
}

function ev(key: string, status: SeasonEvent['status'], start: string | null, tasks: SeasonTask[] = [], end: string | null = null): SeasonEvent {
  return {
    event_key: key, type: 'first_frost', title: key, status, window: { start, end, text: '' },
    explained: EXPLAINED, tasks, owner_actions: [], sort_date: start,
  };
}

const TODAY = new Date(2026, 10, 15);

describe('season sections', () => {
  const events = [
    ev('spring', 'typically_around', '2027-04-10', [task('t')]),
    ev('freeze', 'forecast', '2026-11-18', [task('cover')]),
    ev('leaves', 'expected', '2026-11-10', [task('rake')], '2026-12-05'),
    ev('frost', 'happened', '2026-10-28'),
    ev('hardening', 'done', '2026-10-01'),
    ev('far', 'typically_around', '2028-03-01'),
    ev('dormancy', 'expected', '2026-12-20'),
  ];
  const sections = seasonSections(events, TODAY);

  it('puts what needs attention now first', () => {
    expect(sections[0].key).toBe('now');
    expect(sections[0].events.map((e) => e.event_key)).toEqual(['leaves', 'freeze']);
  });
  it('lists the next twelve months in date order and leaves off anything later', () => {
    const ahead = sections.find((s) => s.key === 'ahead')!;
    expect(ahead.events.map((e) => e.event_key)).toEqual(['dormancy', 'spring']);
    expect(sections.flatMap((s) => s.events).some((e) => e.event_key === 'far')).toBe(false);
  });
  it('puts settled events last, most recent first', () => {
    expect(sections[2].events.map((e) => e.event_key)).toEqual(['frost', 'hardening']);
  });
  it('keeps a recorded event with a task still open in front of the owner', () => {
    const s = seasonSections([ev('frost', 'happened', '2026-11-14', [task('check')])], TODAY);
    expect(s[0].key).toBe('now');
  });
  it('finds the section for a linked event', () => {
    expect(sectionOf(sections, 'spring')).toBe('ahead');
    expect(sectionOf(sections, 'nope')).toBeNull();
  });
  it('drops empty sections', () => {
    expect(seasonSections([], TODAY)).toEqual([]);
  });
});

describe('owner actions', () => {
  it('offers actions in a fixed order', () => {
    expect(orderedActions(['clear', 'mark_happened', 'mark_done'])).toEqual(['mark_done', 'mark_happened', 'clear']);
  });
  it('builds each PUT body', () => {
    expect(actionBody('mark_happened', '2026-11-14')).toEqual({ state: 'happened', observed_on: '2026-11-14' });
    expect(actionBody('mark_not_yet')).toEqual({ state: 'not_yet' });
    expect(actionBody('mark_done')).toEqual({ state: 'done' });
    expect(actionBody('mark_not_needed')).toEqual({ state: 'not_needed' });
    expect(actionBody('clear')).toEqual({ state: 'clear' });
    expect(actionBody('mark_happened').observed_on).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  });
  it('offers a week of days to say when it happened', () => {
    const days = observedDayChoices(TODAY);
    expect(days).toHaveLength(7);
    expect(days[0]).toEqual({ value: '2026-11-15', label: 'Today' });
    expect(days[1]).toEqual({ value: '2026-11-14', label: 'Yesterday' });
    expect(days[2]).toEqual({ value: '2026-11-13', label: 'Fri 13 Nov' });
  });
  it('lists open tasks before settled ones', () => {
    expect(orderedTasks([task('a', 'done'), task('b'), task('c', 'not_needed'), task('d')]).map((t) => t.task_key))
      .toEqual(['b', 'd', 'a', 'c']);
  });
});

describe('forecast strip', () => {
  it('writes each day in plain words', () => {
    const [today, tomorrow, later] = forecastCells([
      { date: '2026-11-15', high_f: 54.4, low_f: 33.2, precipitation_chance: 20, summary: 'Sunny', frost_risk: 'frost' },
      { date: '2026-11-16', high_f: 48, low_f: null, precipitation_chance: null, summary: 'Cloudy', frost_risk: 'none' },
      { date: '2026-11-17', high_f: null, low_f: null, summary: 'Rain', frost_risk: 'hard_freeze' },
    ], TODAY);
    expect(today).toMatchObject({ day: 'Today', temps: '54°F / 33°F', rain: '20% rain', frost: 'Frost possible' });
    expect(today.a11y).toBe('Today, high 54 degrees Fahrenheit, low 33 degrees Fahrenheit, 20 percent chance of rain, Frost possible, Sunny');
    expect(tomorrow).toMatchObject({ day: 'Tomorrow', rain: null, frost: null });
    expect(later).toMatchObject({ day: 'Tue', temps: 'No temperature', frost: 'Hard freeze' });
  });
  it('credits the provider with the forecast time', () => {
    expect(forecastCredit('National Weather Service', new Date(2026, 10, 15, 14, 0).toISOString()))
      .toBe('Forecast: National Weather Service, as of 2 pm Sun 15 Nov.');
    expect(forecastCredit('', 'bad')).toBe('Forecast: the forecast provider.');
  });
});

describe('words', () => {
  it('has no em dash and no bare acronym', () => {
    for (const w of [...Object.values(STATUS_WORDS), ...Object.values(ACTION_LABELS)]) {
      expect(w).not.toMatch(/—/);
      expect(w).not.toMatch(/\b[A-Z]{2,}\b/);
    }
  });
});
