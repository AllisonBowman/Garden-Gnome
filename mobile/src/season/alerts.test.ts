import {
  alertBody, fallHardeningStart, forecastAsOfLine, MAX_ALERTS_PER_WEEK, outOfQuietHours,
  planSeasonalNotices, SEASONAL_RESERVE,
} from './alerts';
import { Explained, SeasonAlert, SeasonEvent } from '../types/site';

// Tests run in America/New_York (jest.globalSetup.js), so local hours below
// are New York hours.

const EXPLAINED: Explained = {
  display: 'First freeze likely Tuesday night', confidence: 'area_estimate',
  confidence_label: 'Area estimate', reason: 'Forecast low of 31 °F.',
  sources: [{ name: 'National Weather Service forecast' }], provenance: 'modelled',
};

function event(key: string, type: SeasonEvent['type']): Pick<SeasonEvent, 'event_key' | 'type' | 'explained'> {
  return { event_key: key, type, explained: EXPLAINED };
}

function alert(key: string, eventKey: string, fireLocal: Date, body = 'Cover tender plants before dark.'): SeasonAlert {
  return {
    alert_key: key, event_key: eventKey, title: `Alert ${key}`, body,
    fire_at: fireLocal.toISOString(),
    built_from_forecast_at: new Date(2026, 10, 15, 14, 0).toISOString(),
  };
}

const NOW = new Date(2026, 10, 15, 16, 0); // Sunday 15 November, 4 pm

describe('quiet hours', () => {
  it('holds a 22:00 alert until 08:00 the next morning', () => {
    const d = outOfQuietHours(new Date(2026, 10, 16, 22, 0));
    expect([d.getDate(), d.getHours(), d.getMinutes()]).toEqual([17, 8, 0]);
  });
  it('moves a 06:00 alert to 08:00 the same day', () => {
    const d = outOfQuietHours(new Date(2026, 10, 16, 6, 30));
    expect([d.getDate(), d.getHours()]).toEqual([16, 8]);
  });
  it('leaves a 15:00 alert alone', () => {
    const d = outOfQuietHours(new Date(2026, 10, 16, 15, 0));
    expect(d.getHours()).toBe(15);
  });
  it('never schedules inside quiet hours', () => {
    const notices = planSeasonalNotices({
      alerts: [alert('a', 'e', new Date(2026, 10, 16, 23, 15)), alert('b', 'e', new Date(2026, 10, 18, 3, 0))],
    }, { now: NOW });
    for (const n of notices) {
      expect(n.date.getHours()).toBeGreaterThanOrEqual(8);
      expect(n.date.getHours()).toBeLessThan(21);
    }
  });
});

describe('limits', () => {
  it('keeps one a day, a freeze over a frost for the same night', () => {
    const notices = planSeasonalNotices({
      alerts: [
        alert('frost', 'ev_frost', new Date(2026, 10, 17, 15, 0)),
        alert('freeze', 'ev_freeze', new Date(2026, 10, 17, 15, 0)),
      ],
      events: [event('ev_frost', 'first_frost'), event('ev_freeze', 'first_freeze')],
    }, { now: NOW });
    expect(notices.map((n) => n.alertKey)).toEqual(['freeze']);
  });

  it('keeps at most three in any seven days', () => {
    const alerts = [16, 17, 18, 19, 20].map((day) => alert(`d${day}`, 'e', new Date(2026, 10, day, 9, 0)));
    const notices = planSeasonalNotices({ alerts }, { now: NOW });
    expect(notices).toHaveLength(MAX_ALERTS_PER_WEEK);
    expect(notices.map((n) => n.alertKey)).toEqual(['d16', 'd17', 'd18']);
  });

  it('never goes past its reserved share', () => {
    const alerts = Array.from({ length: 40 }, (_, i) => alert(`a${i}`, 'e', new Date(2026, 10, 16 + i * 3, 9, 0)));
    const notices = planSeasonalNotices({ alerts }, { now: NOW, horizonDays: 400 });
    expect(notices.length).toBeLessThanOrEqual(SEASONAL_RESERVE);
  });

  it('drops past alerts, ones beyond the horizon, and ones with no forecast time', () => {
    const bad = { ...alert('noforecast', 'e', new Date(2026, 10, 17, 9, 0)), built_from_forecast_at: '' };
    const notices = planSeasonalNotices({
      alerts: [
        alert('past', 'e', new Date(2026, 10, 15, 9, 0)),
        alert('far', 'e', new Date(2026, 11, 30, 9, 0)),
        bad,
        alert('ok', 'e', new Date(2026, 10, 18, 9, 0)),
      ],
    }, { now: NOW });
    expect(notices.map((n) => n.alertKey)).toEqual(['ok']);
  });

  it('uses the alert key as the notification identifier', () => {
    const [n] = planSeasonalNotices({ alerts: [alert('frost_2026_11_17_dayof', 'e', new Date(2026, 10, 17, 15, 0))] }, { now: NOW });
    expect(n.identifier).toBe('frost_2026_11_17_dayof');
  });
});

describe('the body', () => {
  it('ends with the forecast time it was built from', () => {
    const [n] = planSeasonalNotices({
      alerts: [alert('a', 'e', new Date(2026, 10, 17, 15, 0))], events: [event('e', 'first_freeze')],
    }, { now: NOW });
    expect(n.body.endsWith('Forecast as of 2 pm on Sunday 15 November.')).toBe(true);
  });

  it('names the data source when the server body does not', () => {
    const body = alertBody(alert('a', 'e', new Date(2026, 10, 17, 15, 0), 'Cover tender plants'), event('e', 'first_freeze'));
    expect(body).toBe('Cover tender plants. Data: National Weather Service forecast. Forecast as of 2 pm on Sunday 15 November.');
  });

  it('does not repeat a source or time the server already wrote', () => {
    const text = 'Data: National Weather Service forecast. Forecast as of 2 pm today.';
    expect(alertBody(alert('a', 'e', NOW, text), event('e', 'first_freeze'))).toBe(text);
  });

  it('has no em dash', () => {
    const [n] = planSeasonalNotices({ alerts: [alert('a', 'e', new Date(2026, 10, 17, 15, 0))] }, { now: NOW });
    expect(n.body).not.toMatch(/—/);
    expect(forecastAsOfLine('nonsense')).toBeNull();
  });
});

describe('fall hardening start', () => {
  const plan = (start: string | null) => ({
    events: [{
      event_key: 'fh', type: 'fall_hardening' as const, title: 'Fall hardening', status: 'happening' as const,
      window: { start, end: null, text: '' }, explained: EXPLAINED, tasks: [], owner_actions: [], sort_date: start,
    }],
  });
  it('reads the window start as a local date', () => {
    const d = fallHardeningStart(plan('2026-10-01'), NOW)!;
    expect([d.getFullYear(), d.getMonth(), d.getDate(), d.getHours()]).toEqual([2026, 9, 1, 0]);
  });
  it('is null without the event or a date', () => {
    expect(fallHardeningStart({ events: [] }, NOW)).toBeNull();
    expect(fallHardeningStart(plan(null), NOW)).toBeNull();
    expect(fallHardeningStart(null, NOW)).toBeNull();
  });
});
