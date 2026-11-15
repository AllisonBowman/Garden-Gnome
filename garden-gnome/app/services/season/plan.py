"""Seasonal plan entry point (build spec section 3; PLAN.md section 7).

    seasonal_plan(session, prop, *, today=None) -> SeasonalPlanOut

Computed on each request from: the National Weather Service forecast for the
pin's weather cell (cached three hours), the NOAA station normals held on our
server, day length, what is on the lot (lot_contents, zones with their
vegetation and leaf habit), the owner's frost setting, and the owner's
answers in `season_event_state`.

The plan always covers the next twelve months: the current season (1 July to
30 June) in full, so a late-winter install still sees the fall behind it,
plus the next season's events up to a year from today.

Writes (committed here, because the GET routes do not commit):
- the forecast cache rows;
- the property's city, region, country and time zone from the Weather
  Service lookup, once;
- a "seen_in_forecast" event state when tonight's forecast low crosses a
  frost band, so that once the night has passed the plan can say it was
  forecast for the area (PLAN.md P0-5 fallback path). Only Weather Service
  data is ever recorded this way; nothing from Apple WeatherKit is stored.

`today` pins the clock for tests: with it, the forecast is read as if it
were 14:00 UTC that day.
"""
from __future__ import annotations

from datetime import date, datetime, time, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlmodel import Session, select

from app.models.models import GrowingArea, Property, SeasonEventState
from app.models.schemas import ForecastOut, SeasonalPlanOut
from app.services.season import alerts as alerts_mod
from app.services.season import events as ev
from app.services.season import forecast as fcm
from app.services.season.normals import frost_normals

SEEN = "seen_in_forecast"


def _clock(prop: Property, today: Optional[date]) -> tuple[datetime, date]:
    if today is not None:
        return datetime.combine(today, time(14, 0)), today
    now = datetime.utcnow()
    tz = ZoneInfo(prop.timezone) if prop.timezone else timezone.utc
    return now, now.replace(tzinfo=timezone.utc).astimezone(tz).date()


def _zones(session: Session, prop: Property) -> list[ev.Zone]:
    rows = session.exec(select(GrowingArea).where(GrowingArea.property_id == prop.id)
                        .order_by(GrowingArea.id.asc())).all()
    return [ev.Zone(id=r.id,
                    vegetation_type=r.vegetation_type.value if r.vegetation_type else None,
                    leaf_habit=r.leaf_habit.value if r.leaf_habit else None,
                    is_whole_lot=bool(r.is_whole_lot)) for r in rows]


def _copy_place_to_zones(session: Session, prop: Property) -> None:
    """Each zone keeps a server-written copy of the property's place, which
    the 1.1.x client shows; refresh it once the place is known."""
    for row in session.exec(select(GrowingArea).where(GrowingArea.property_id == prop.id)).all():
        row.city = prop.city or ""
        row.region = prop.region or ""
        row.country = prop.country or ""
        session.add(row)


def _states(session: Session, prop: Property) -> dict[str, ev.OwnerState]:
    rows = session.exec(select(SeasonEventState)
                        .where(SeasonEventState.property_id == prop.id)
                        .where(SeasonEventState.zone_id == None)).all()  # noqa: E711
    return {r.event_key: ev.OwnerState(status=r.status, observed_on=r.observed_on, band=r.band)
            for r in rows}


def find_state(session: Session, property_id: int, event_key: str) -> Optional[SeasonEventState]:
    """The whole-lot row for one event, or None."""
    return session.exec(select(SeasonEventState)
                        .where(SeasonEventState.property_id == property_id)
                        .where(SeasonEventState.zone_id == None)  # noqa: E711
                        .where(SeasonEventState.event_key == event_key)).first()


def claim_state(session: Session, property_id: int, event_key: str, status: str,
                now: datetime) -> SeasonEventState:
    """The whole-lot row for one event, inserted if there is none. Home asks
    for /vitals and the seasonal plan at once, and both may write the same
    event: the insert does nothing when the other request got there first
    (the unique index on property, zone and event key), and the row that
    is there is returned."""
    session.execute(sqlite_insert(SeasonEventState).values(
        property_id=property_id, zone_id=None, event_key=event_key, status=status,
        first_seen_at=now, updated_at=now).on_conflict_do_nothing())
    row = find_state(session, property_id, event_key)
    assert row is not None
    return row


def record_seen(session: Session, prop: Property, inp: ev.Inputs,
                fc: Optional[fcm.Forecast]) -> int:
    """Remember tonight's forecast cold night for each frost event it
    reaches, once a season. Returns how many rows were written."""
    if fc is None:
        return 0
    night = fc.night(inp.today)
    if night is None:
        return 0
    adj = fcm.adjusted_low(night, inp.frost_bias)
    band = fcm.band(None if adj is None else round(adj))
    if band == "none":
        return 0
    year = ev.season_year(inp.today)
    if inp.today.month < 7:
        return 0  # spring frosts are shown from the forecast, not remembered
    written = 0
    now = datetime.utcnow()
    for etype in ev.FALL_TYPES:
        if ev.BAND_RANK[band] < ev.TYPE_RANK[etype]:
            continue
        key = ev.event_key(etype, year, "fall")
        row = find_state(session, prop.id, key)
        if row is not None and not (row.status == "not_yet" and row.updated_at.date() < inp.today):
            continue
        if row is None:
            row = claim_state(session, prop.id, key, SEEN, now)
        row.status = SEEN
        row.band = band
        row.provider_name = fc.provider_name
        row.observed_on = inp.today
        row.updated_at = now
        session.add(row)
        inp.states[key] = ev.OwnerState(status=SEEN, observed_on=inp.today, band=band)
        written += 1
    return written


def _notes(prop: Property, fc: Optional[fcm.Forecast], normals: dict, us: bool) -> list[str]:
    notes = []
    if not us:
        notes.append("The seasonal plan uses United States weather and climate data. Outside the "
                     "United States it shows little until other sources are added.")
    elif fc is None:
        notes.append("No forecast right now: the dates shown are typical dates, not this year's forecast.")
    if normals.get("status") != "ready":
        notes.append("No weather station with frost records is close enough, so tasks are shown "
                     "without typical dates.")
    notes.append("We do not read measured temperatures for your area yet. A frost or freeze shows as "
                 "happened when you tell us, or when the forecast for that night called for it.")
    if prop.frost_bias:
        notes.append(f"You told us your yard frosts {prop.frost_bias} than the neighbours: forecast "
                     f"lows are moved {fcm.BIAS_F} degrees on clear, calm nights.")
    return notes


def build(session: Session, prop: Property, *, today: Optional[date] = None,
          client=None) -> tuple[SeasonalPlanOut, Optional[fcm.Forecast], ev.Inputs]:
    """The plan plus the forecast and inputs it was built from (vitals
    reuses them). Commits its writes."""
    now, local_today = _clock(prop, today)
    us = fcm.in_united_states(prop.pin_lat, prop.pin_lng)
    fc = fcm.get_forecast(session, prop.pin_lat, prop.pin_lng, now=now, client=client) if us else None
    if fc is not None:
        fcm.add_second_opinion(session, fc, prop.pin_lat, prop.pin_lng, now=now)
        if fcm.fill_place(prop, fc):
            _copy_place_to_zones(session, prop)
        session.add(prop)
        if today is None:
            local_today = fcm.local_today(fc)
    normals = frost_normals(prop.pin_lat, prop.pin_lng)
    inp = ev.Inputs(
        lat=prop.pin_lat, today=local_today, normals=normals, forecast=fc,
        lot_contents=prop.lot_contents,
        frost_bias=prop.frost_bias.value if prop.frost_bias else None,
        zones=_zones(session, prop), states=_states(session, prop))
    record_seen(session, prop, inp, fc)
    session.commit()
    events = ev.plan_events(inp)
    out = SeasonalPlanOut(
        property_id=prop.id,
        generated_at=datetime.utcnow(),
        season_label=ev.season_label(local_today),
        forecast=ForecastOut(**fcm.forecast_out(fc, inp.frost_bias)) if fc else None,
        events=events,
        alerts=alerts_mod.build_alerts(events, fc, now=now, today=local_today),
        notes=_notes(prop, fc, normals, us),
    )
    return out, fc, inp


def seasonal_plan(session: Session, prop: Property, *,
                  today: Optional[date] = None) -> SeasonalPlanOut:
    """The plan for `prop`, computed on each request."""
    return build(session, prop, today=today)[0]
