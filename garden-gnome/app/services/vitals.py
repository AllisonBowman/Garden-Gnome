"""The Home vitals report (build spec sections 3, 4 and 6).

    vitals(session, user, prop | None, *, today=None) -> VitalsOut

With a property: the seasonal plan (forecast, events, tasks), cards for
weather now, frost, rain, heat, sun, soil, drainage and the season, "This
week", "The season ahead" and the person's spaces. The land cards read the
site profile (`app.services.site.profile.site_profile`) and say "Not known
yet" while it is pending.

Without a property: weather for the first growing area that has
coordinates, the person's spaces, and, when the land feature is on, one calm
line inviting them to add land if they have any.

Weather, with or without a property: United States coordinates
(`app.services.coverage`) read the National Weather Service through the
seasonal forecast path (cached, guarded). Only a place outside the United
States, or one the Weather Service itself says it does not cover (a 404
from its points lookup, outside the territories), goes to the existing
weather service and its full chain. A United States place the Weather
Service cannot answer for right now gets Apple WeatherKit alone, never
Open-Meteo (PLAN.md D11).
"""
from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from sqlmodel import Session, select

from app.config import get_settings
from app.models.models import GrowingArea, Plant, Property, TempExposure, User
from app.models.schemas import (
    Explained, ForecastOut, SeasonEvent, SeasonEventSummary, SourceOut, SpaceOut,
    ThisWeekItem, VitalCard, VitalsOut)
from app.services import coverage
from app.services.season import events as ev
from app.services.season import forecast as fcm
from app.services.season import plan as plan_mod

logger = logging.getLogger("plantadvocate.vitals")

DEGREE = "°F"
ACTIVE = ("forecast", "happening", "expected")
SETTLED = ("done", "not_needed")
AHEAD_COUNT = 5


def _spaces(session: Session, user: User) -> list[SpaceOut]:
    areas = session.exec(
        select(GrowingArea).where(GrowingArea.user_id == user.id)
        .order_by(GrowingArea.id.asc())).all()
    out = []
    for a in areas:
        # Rows, not quantities: the same count /growing-areas reports.
        count = len(session.exec(
            select(Plant).where(Plant.growing_area_id == a.id)).all())
        out.append(SpaceOut(
            growing_area_id=a.id, name=a.name,
            kind="zone" if a.property_id is not None else "space",
            vegetation_type=a.vegetation_type.value if a.vegetation_type else None,
            indoor=a.temp_exposure == TempExposure.indoor,
            plant_count=count))
    return out


def _weekday(d: date) -> str:
    return ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")[d.weekday()]


def _night_words(d: date, today: date) -> str:
    lead = (d - today).days
    if lead == 0:
        return "tonight"
    if lead == 1:
        return "tomorrow night"
    return f"{_weekday(d)} night"


def _day_words(d: date, today: date) -> str:
    lead = (d - today).days
    return "today" if lead == 0 else "tomorrow" if lead == 1 else _weekday(d)


def _nws_explained(fc: fcm.Forecast, display: str, reason: str) -> Explained:
    src = dict(fcm.NWS_SOURCE, detail=f"Forecast as of {_as_of(fc)}")
    return Explained(display=display, confidence="area_estimate", reason=reason,
                     sources=[SourceOut(**src)], provenance="modelled")


def _as_of(fc: fcm.Forecast) -> str:
    return ev.clock_text(fc.issued_at.replace(tzinfo=timezone.utc).astimezone(ZoneInfo(fc.timezone)))


# --- weather cards from our forecast ---------------------------------------------------

def _weather_cards(fc: fcm.Forecast, today: date, frost_bias: Optional[str],
                   frost_event: Optional[SeasonEvent]) -> list[VitalCard]:
    cards = []
    cur = fc.current or {}
    if cur.get("temp_f") is not None:
        summary = (cur.get("summary") or "").lower()
        period = cur.get("period") or "Now"
        cards.append(VitalCard(
            key="weather_now", title="Weather now",
            value_text=f"{cur['temp_f']} {DEGREE}" + (f", {summary}" if summary else ""),
            detail=f"{period}, from the National Weather Service forecast as of {_as_of(fc)}.",
            tone="ok",
            explained=_nws_explained(fc, f"{period}: {cur['temp_f']} {DEGREE}.",
                                     "The first period of the Weather Service forecast for your area. "
                                     "It is a forecast for an area about 2.5 kilometres across, not a "
                                     "thermometer in your yard.")))
    # Frost: the first night in seven with a frost band on the adjusted low.
    hit = None
    for n in fc.nights:
        lead = (n.date - today).days
        if lead < 0:
            continue
        adj = fcm.adjusted_low(n, frost_bias)
        b = fcm.band(None if adj is None else round(adj))
        if b != "none":
            hit = (n, adj, b, lead)
            break
    if hit:
        n, adj, b, lead = hit
        word = {"frost": "Frost possible", "freeze": "Freeze possible",
                "hard_freeze": "Hard freeze possible"}[b]
        value = f"{word} {_night_words(n.date, today)}"
        tone = "act" if lead <= 1 else "watch"
        detail = f"Low near {round(n.low_f)} {DEGREE}."
        if round(adj) != round(n.low_f):
            detail += f" We count it as about {round(adj)} {DEGREE} for your yard."
        expl = (frost_event.explained if frost_event is not None and frost_event.status == "forecast"
                else _nws_explained(fc, f"{value}: low near {round(n.low_f)} {DEGREE}.",
                                    f"The lowest forecast night at or below 36 {DEGREE} in the next "
                                    "seven nights."))
    else:
        lows = [n.low_f for n in fc.nights if n.low_f is not None]
        value = "No frost in the next 7 nights"
        tone = "ok"
        detail = f"Lowest forecast night: {round(min(lows))} {DEGREE}." if lows else "No lows in the forecast."
        expl = _nws_explained(fc, value, f"No forecast night in the next seven is at or below 36 {DEGREE}.")
    cards.append(VitalCard(key="frost", title="Frost", value_text=value, detail=detail, tone=tone,
                           explained=expl, link="Season"))
    # Rain.
    days = [(date.fromisoformat(d["date"]), d) for d in fc.days]
    chances = [(d, x["precipitation_chance"]) for d, x in days if x.get("precipitation_chance") is not None]
    total = sum(x["rain_in"] for _, x in days if x.get("rain_in"))
    wet = [(d, c) for d, c in chances if c >= 50]
    if wet:
        d, c = wet[0]
        value = f"Rain likely {_day_words(d, today)} ({round(c)}% chance)"
        tone = "watch" if total >= 1.5 else "ok"
    else:
        value = "Little rain in the forecast"
        tone = "ok"
    detail = (f"About {total:.1f} inches forecast in the next few days." if total >= 0.05
              else "Under a tenth of an inch forecast in the next few days.")
    cards.append(VitalCard(key="rain", title="Rain", value_text=value, detail=detail, tone=tone,
                           explained=_nws_explained(fc, value, "The highest daily chance of rain and "
                                                    "the forecast rain amount, added up.")))
    # Heat.
    highs = [(d, x["high_f"]) for d, x in days if x.get("high_f") is not None]
    if highs:
        d, h = max(highs, key=lambda t: t[1])
        tone = "act" if h >= 100 else "watch" if h >= 90 else "ok"
        value = (f"Hot {_day_words(d, today)}: {round(h)} {DEGREE}" if h >= 90
                 else f"No heat in the forecast; warmest {round(h)} {DEGREE}")
        cards.append(VitalCard(
            key="heat", title="Heat", value_text=value,
            detail="Water new plantings and pots in the morning on hot days." if h >= 90
            else f"Warmest day: {_day_words(d, today)}.", tone=tone,
            explained=_nws_explained(fc, value, f"The highest forecast temperature this week. "
                                     f"Heat is flagged at 90 {DEGREE} and above.")))
    return cards


# --- land cards from the site profile --------------------------------------------------

_LAND = (("sun", "Sun", ("sun",)),
         ("soil", "Soil", ("soil_texture", "soil_drainage")),
         ("drainage", "Drainage", ("water_collects", "soil_drainage")))


def _land_cards(session: Session, prop: Property) -> list[VitalCard]:
    values = []
    try:
        from app.services.site.profile import site_profile
        values = site_profile(session, prop).values
    except Exception as exc:  # the profile is a teammate's; Home must still answer
        logger.info("site profile unavailable for vitals: %s", exc)
    by_field = {v.field: v for v in values if v.zone_id is None}
    cards = []
    for key, title, fields in _LAND:
        sv = next((by_field[f] for f in fields if f in by_field), None)
        if sv is None or sv.confidence == "not_known_yet":
            cards.append(VitalCard(key=key, title=title, value_text="Not known yet",
                                   detail="Your land report is still being put together.",
                                   tone="ok", link="Land"))
            continue
        # The card has its own title, so drop the sentence's "Sun: " lead-in.
        text = sv.display
        lead = f"{sv.title}: " if sv.title else ""
        if lead and text.startswith(lead):
            text = text[len(lead)].upper() + text[len(lead) + 1:]
        cards.append(VitalCard(
            key=key, title=title, value_text=text, detail=sv.confidence_label or "",
            tone="ok", link="Land",
            explained=Explained(display=sv.display, confidence=sv.confidence, reason=sv.reason,
                                sources=sv.sources, provenance=sv.provenance)))
    return cards


# --- the report ------------------------------------------------------------------------

def _summary(e: SeasonEvent) -> SeasonEventSummary:
    return SeasonEventSummary(**e.model_dump(exclude={"tasks"}))


def _this_week(events: list[SeasonEvent], today: date) -> list[ThisWeekItem]:
    week_end = today + timedelta(days=7)
    open_items, settled = [], []
    for e in events:
        in_window = ((e.window.start is None or e.window.start <= week_end)
                     and (e.window.end is None or e.window.end >= today))
        near = e.sort_date is not None and today <= e.sort_date <= week_end
        if e.status in ACTIVE and (in_window or near):
            open_items += [ThisWeekItem(event_key=e.event_key, task=t) for t in e.tasks]
        elif e.status in SETTLED and (near or (in_window and e.window.start is not None
                                               and e.window.start <= today)):
            settled += [ThisWeekItem(event_key=e.event_key, task=t) for t in e.tasks]
    return open_items + settled


def _ahead(events: list[SeasonEvent], today: date) -> list[SeasonEventSummary]:
    upcoming = [e for e in events
                if e.status not in ("happened", "done", "not_needed")
                and (e.sort_date is None or e.sort_date >= today or e.status in ACTIVE)]
    return [_summary(e) for e in upcoming[:AHEAD_COUNT]]


def _season_card(label: str, ahead: list[SeasonEventSummary]) -> VitalCard:
    if not ahead:
        return VitalCard(key="season", title="Season", value_text=label,
                         detail="Nothing seasonal is due soon.", tone="ok", link="Season")
    nxt = ahead[0]
    tone = "watch" if nxt.status in ("forecast", "happening") else "ok"
    return VitalCard(key="season", title="Season", value_text=label,
                     detail=f"{'Now' if nxt.status == 'happening' else 'Next'}: "
                            f"{nxt.title}. {nxt.window.text}", tone=tone,
                     explained=nxt.explained, link="Season")


_HAPPENING_LINES = {
    "leaf_drop": "Leaves are coming down; leave them whole on your beds.",
    "fall_hardening": "Trees and shrubs are hardening for winter, so skip fertilizer and pruning.",
    "spring_cleanup": "The spring cleanup window is open.",
}


def _headline(label: str, cards: list[VitalCard], events: list[SeasonEvent]) -> str:
    parts = []
    frost = next((c for c in cards if c.key == "frost"), None)
    if frost and frost.tone in ("act", "watch"):
        parts.append(f"{frost.value_text}. {frost.detail}")
    for e in events:
        if e.status == "happening" and e.type in _HAPPENING_LINES and e.tasks:
            parts.append(_HAPPENING_LINES[e.type])
            break
    if not parts:
        nxt = next((e for e in events if e.status in ("typically_around", "expected", "forecast")
                    and e.sort_date), None)
        if nxt:
            parts.append(f"{label}. {nxt.explained.display}")
        else:
            parts.append(f"{label}.")
    return " ".join(parts[:2])


def _with_property(session: Session, user: User, prop: Property, today: Optional[date]) -> VitalsOut:
    plan, fc, inp = plan_mod.build(session, prop, today=today)
    events = plan.events
    cards = []
    if fc is not None:
        first_frost = next((e for e in events if e.type in ("first_frost", "first_freeze",
                                                            "hard_freeze", "last_frost")
                            and e.status == "forecast"), None)
        cards += _weather_cards(fc, inp.today, inp.frost_bias, first_frost)
    forecast = plan.forecast
    if fc is None:
        payload = _fallback_weather(session, prop.pin_lat, prop.pin_lng,
                                    now=_report_clock(today))
        if payload:
            extra, fo = _payload_cards(payload, inp.today)
            cards += extra
            forecast = forecast or fo
    cards += _land_cards(session, prop)
    ahead = _ahead(events, inp.today)
    cards.append(_season_card(plan.season_label, ahead))
    return VitalsOut(
        generated_at=datetime.utcnow(),
        headline=_headline(plan.season_label, cards, events),
        property=None,
        forecast=forecast,
        cards=cards,
        this_week=_this_week(events, inp.today),
        season_ahead=ahead,
        spaces=_spaces(session, user),
        notes=plan.notes,
    )


# --- no property -----------------------------------------------------------------------

def _existing_weather(lat: float, lng: float, *, open_meteo: bool = True) -> Optional[dict]:
    """The existing weather service: its full chain for places outside the
    United States, Apple WeatherKit alone (`open_meteo=False`) for a United
    States place the National Weather Service cannot answer for."""
    from app.services import weather
    try:
        if open_meteo:
            return asyncio.run(weather.fetch_weather(lat, lng))
        return asyncio.run(weather._fetch_weatherkit(*weather._coarse(lat, lng), "en"))
    except RuntimeError:
        return None


def _report_clock(today: Optional[date]) -> Optional[datetime]:
    """The instant a report for a fixed `today` is built at (14:00, as the
    plan does); None means the real clock."""
    return datetime.combine(today, datetime.min.time()).replace(hour=14) if today else None


def _fallback_weather(session: Session, lat: float, lng: float, *,
                      now: Optional[datetime] = None) -> Optional[dict]:
    """Weather when our National Weather Service forecast has none. `now` is
    the report's own clock, so the cache is read at the instant it was
    written at; without it a report built for a fixed day would read the
    3-hour cache against the real time of day."""
    if not coverage.in_united_states(lat, lng):
        return _existing_weather(lat, lng)
    if fcm.outside_coverage(session, lat, lng, now=now) and not coverage.in_territory(lat, lng):
        # Inside the rough boxes, but the Weather Service says it is not a
        # United States place (a city just over the border).
        return _existing_weather(lat, lng)
    return _existing_weather(lat, lng, open_meteo=False)


def _payload_cards(payload: dict, today: date) -> tuple[list[VitalCard], Optional[ForecastOut]]:
    att = payload.get("attribution") or {}
    name = (att.get("text") or "Weather").strip() or "Weather"
    src = SourceOut(name=name, url=att.get("url"))

    def ex(display, reason):
        return Explained(display=display, confidence="area_estimate", reason=reason,
                         sources=[src], provenance="modelled")
    cards = []
    cur = payload.get("current") or {}
    if cur.get("temp_f") is not None:
        v = f"{cur['temp_f']} {DEGREE}"
        cards.append(VitalCard(key="weather_now", title="Weather now", value_text=v,
                               detail=f"From {name}.", tone="ok",
                               explained=ex(v, "Current conditions for your area.")))
    days = []
    for d in payload.get("daily") or []:
        try:
            day = date.fromisoformat(d["date"])
        except (KeyError, ValueError):
            continue
        low = d.get("low_f")
        days.append({"date": day, "high_f": d.get("high_f"), "low_f": low,
                     "precipitation_chance": d.get("precip_chance_pct"),
                     "summary": str(d.get("condition") or ""),
                     "frost_risk": fcm.band(low)})
    cold = next((d for d in days if d["frost_risk"] != "none"), None)
    if cold:
        v = f"Frost possible {_day_words(cold['date'], today)}"
        cards.append(VitalCard(key="frost", title="Frost", value_text=v,
                               detail=f"Low near {cold['low_f']} {DEGREE}.",
                               tone="act" if (cold["date"] - today).days <= 1 else "watch",
                               explained=ex(v, f"A forecast low at or below 36 {DEGREE}.")))
    else:
        cards.append(VitalCard(key="frost", title="Frost", value_text="No frost in the forecast",
                               detail="", tone="ok",
                               explained=ex("No frost in the forecast",
                                            f"No forecast low at or below 36 {DEGREE}.")))
    fo = ForecastOut(provider=name.lower().replace(" ", "_")[:40], provider_name=name,
                     fetched_at=datetime.utcnow(),
                     days=[dict(d, summary=d["summary"] or "Forecast") for d in days]) if days else None
    return cards, fo


def _without_property(session: Session, user: User, today: Optional[date]) -> VitalsOut:
    spaces = _spaces(session, user)
    area = session.exec(select(GrowingArea).where(GrowingArea.user_id == user.id)
                        .where(GrowingArea.lat != None).where(GrowingArea.lng != None)  # noqa: E711
                        .order_by(GrowingArea.id.asc())).first()
    cards: list[VitalCard] = []
    forecast = None
    headline = ""
    if area is not None:
        if fcm.in_united_states(area.lat, area.lng):
            now = datetime.combine(today, datetime.min.time()).replace(hour=14) if today else None
            fc = fcm.get_forecast(session, area.lat, area.lng, now=now)
            session.commit()
            if fc is None:
                payload = _fallback_weather(session, area.lat, area.lng, now=now)
                if payload:
                    cards, forecast = _payload_cards(payload, today or date.today())
            else:
                local = today or fcm.local_today(fc)
                cards = _weather_cards(fc, local, None, None)
                forecast = ForecastOut(**fcm.forecast_out(fc, None))
                first = fc.days[0] if fc.days else None
                frost = next((c for c in cards if c.key == "frost"), None)
                if frost and frost.tone != "ok":
                    headline = f"{frost.value_text} where your plants are. {frost.detail}"
                elif first and first.get("summary"):
                    hi = f", high {round(first['high_f'])} {DEGREE}" if first.get("high_f") is not None else ""
                    headline = f"{first['summary']} today{hi}."
        else:
            payload = _existing_weather(area.lat, area.lng)
            if payload:
                cards, forecast = _payload_cards(payload, today or date.today())
    notes = []
    if get_settings().site_profile_enabled:
        notes.append("If you look after a yard or garden, you can add your land for a seasonal "
                     "plan made for it.")
    return VitalsOut(generated_at=datetime.utcnow(), headline=headline, property=None,
                     forecast=forecast, cards=cards, this_week=[], season_ahead=[],
                     spaces=spaces, notes=notes)


def vitals(session: Session, user: User, prop: Optional[Property], *,
           today: Optional[date] = None) -> VitalsOut:
    """The Home report. `property` is left null; the route fills it."""
    if prop is not None:
        return _with_property(session, user, prop, today)
    return _without_property(session, user, today)
