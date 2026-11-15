"""Frost and freeze alerts, computed here and scheduled on the phone
(PLAN.md D21, section 7 "Notifications alongside reminders.ts").

The server only computes them; the phone's one planner schedules them. Each
alert carries the Weather Service time of the forecast it was built from,
and its body says "Forecast as of ...", because an on-device alert reflects
the forecast at the last app open.

Rules (engineering defaults from PLAN.md):
- only for frost-type events with status "forecast" that are not a "Rough
  estimate" (two providers apart, or six to seven nights away);
- only for nights at most three nights away (days 4 to 7 are plan only);
- a heads-up at 09:00 local two days before the night, and a day-of alert
  at 15:00 local; nothing between 21:00 and 08:00;
- a colder event replaces a milder one for the same night;
- at most one alert a local day and three in seven days;
- never a time already past.
Alerts are worded as plant care, never as safety warnings.
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from app.models.schemas import SeasonAlert, SeasonEvent
from app.services.season import forecast as fcm
from app.services.season import normals as nm

ALERT_TYPES = {"first_frost": 1, "first_freeze": 2, "hard_freeze": 3, "last_frost": 1}
HEADS_UP = time(9, 0)
DAY_OF = time(15, 0)
MAX_LEAD = 3
PER_WEEK = 3

_TITLES = {"first_frost": "Frost", "first_freeze": "Freeze", "hard_freeze": "Hard freeze",
           "last_frost": "Late frost"}
_CARE = {"first_frost": "Bring in or cover tender plants you want to keep.",
         "first_freeze": "Bring in tender potted plants and cover anything you want to keep.",
         "hard_freeze": "Bring in tender potted plants. Perennials will die back; leave their stems standing.",
         "last_frost": "Cover tender new growth and new plantings overnight."}


def _as_of(fc: fcm.Forecast, tz: ZoneInfo) -> str:
    from app.services.season.events import clock_text
    return clock_text(fc.issued_at.replace(tzinfo=timezone.utc).astimezone(tz))


def build_alerts(events: list[SeasonEvent], fc: Optional[fcm.Forecast], *,
                 now: datetime, today: date) -> list[SeasonAlert]:
    if fc is None:
        return []
    tz = ZoneInfo(fc.timezone)
    now_utc = now.replace(tzinfo=timezone.utc) if now.tzinfo is None else now
    built_from = fc.issued_at.replace(tzinfo=timezone.utc)
    # The coldest forecast event per night.
    per_night: dict[date, SeasonEvent] = {}
    for e in events:
        if e.type not in ALERT_TYPES or e.status != "forecast" or e.window.start is None:
            continue
        if e.explained.confidence == "rough_estimate":
            continue
        night = e.window.start
        lead = (night - today).days
        if lead < 0 or lead > MAX_LEAD:
            continue
        held = per_night.get(night)
        if held is None or ALERT_TYPES[e.type] > ALERT_TYPES[held.type]:
            per_night[night] = e
    candidates = []
    for night, e in sorted(per_night.items()):
        when = "tonight" if night == today else f"on the night of {nm.day_text(night)}"
        for stage, day, at in (("heads_up", night - timedelta(days=2), HEADS_UP),
                               ("day_of", night, DAY_OF)):
            fire = datetime.combine(day, at, tzinfo=tz).astimezone(timezone.utc)
            if fire <= now_utc:
                continue
            title = (f"{_TITLES[e.type]} likely {when}" if stage == "day_of"
                     else f"{_TITLES[e.type]} possible {when}")
            body = (f"{e.window.text[0].upper()}{e.window.text[1:]} {_CARE[e.type]} "
                    f"Forecast as of {_as_of(fc, tz)}, National Weather Service.")
            candidates.append(SeasonAlert(
                alert_key=f"{e.event_key}:{night.isoformat()}:{stage}", event_key=e.event_key,
                title=title, body=body, fire_at=fire, built_from_forecast_at=built_from))
    candidates.sort(key=lambda a: a.fire_at)
    out: list[SeasonAlert] = []
    days_used: set[date] = set()
    for a in candidates:
        local_day = a.fire_at.astimezone(tz).date()
        if local_day in days_used:
            continue
        week = [x for x in out if abs((x.fire_at - a.fire_at).days) < 7]
        if len(week) >= PER_WEEK:
            continue
        days_used.add(local_day)
        out.append(a)
    return out
