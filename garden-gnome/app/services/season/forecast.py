"""The seven-day forecast for the seasonal engine (PLAN.md D10, D11).

United States pins read the National Weather Service: a /points lookup for
the weather cell (the pin at two decimal places, about a kilometre), then the
gridpoint data (lows, highs, chance of rain, rain amount, wind, sky cover)
and the text forecast (one short summary a day). Both answers are kept in
`forecast_cache` for three hours and nowhere else. Open-Meteo is never called
from here.

Apple WeatherKit is read only as a second opinion on the nightly low, only
when the existing weather service is configured and the monthly count in
`provider_usage` is under the cap. Its numbers live in process memory for
three hours and are never written to the database (D10).

Night assignment: "the night of D" runs from the evening of local date D to
the next morning. A Weather Service minTemperature period that starts at or
after local noon belongs to that local date; one that starts before noon
belongs to the night before.

Frost risk per night, on the adjusted low: frost at or below 36 F, freeze at
or below 32 F, hard freeze at or below 28 F. The owner's "frosts earlier /
later than the neighbours" setting moves the low 2 F, only on clear and calm
nights (overnight wind under 5 miles per hour and sky cover under 30%),
as PLAN.md section 7 says. Both figures are engineering defaults.
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional
from zoneinfo import ZoneInfo

from sqlmodel import Session, delete, select

from app.models.models import ForecastCache, Property, ProviderUsage
from app.services import coverage
from app.services.site import grid
from app.services.site import http as site_http

logger = logging.getLogger("plantadvocate.season.forecast")

NWS_BASE = "https://api.weather.gov"
NWS_ACCEPT = {"Accept": "application/geo+json"}
PROVIDER = "nws"
POINTS_PROVIDER = "nws_points"
PROVIDER_NAME = "National Weather Service"
NWS_SOURCE = {"name": "National Weather Service forecast",
              "detail": "api.weather.gov gridpoint forecast", "url": "https://www.weather.gov/"}
CACHE_LIFE = timedelta(hours=3)
FORECAST_NIGHTS = 7

FROST_F, FREEZE_F, HARD_FREEZE_F = 36, 32, 28
BIAS_F = 2
CALM_WIND_MPH = 5
CLEAR_SKY_PCT = 30

#: Apple WeatherKit calls allowed in a month before the second opinion stops.
WEATHERKIT_MONTHLY_CAP = 400_000
WEATHERKIT = "weatherkit"
_second_opinion_memory: dict[str, tuple[float, dict]] = {}


@dataclass
class Night:
    date: date
    low_f: Optional[float]
    wind_mph: Optional[float] = None
    sky_pct: Optional[float] = None


@dataclass
class Forecast:
    """A parsed forecast for one cell. `days` hold the day's high, chance of
    rain, rain amount and summary; `nights` the overnight low that starts
    that evening."""
    provider: str
    provider_name: str
    fetched_at: datetime            # when we read it (UTC, naive)
    issued_at: datetime             # when the Weather Service last updated it
    timezone: str
    days: list[dict]
    nights: list[Night]
    place: dict = field(default_factory=dict)
    current: dict = field(default_factory=dict)
    second_opinion: Optional[dict] = None   # night date (iso) -> low_f, memory only

    def night(self, d: date) -> Optional[Night]:
        return next((n for n in self.nights if n.date == d), None)


def band(low_f: Optional[float]) -> str:
    if low_f is None:
        return "none"
    if low_f <= HARD_FREEZE_F:
        return "hard_freeze"
    if low_f <= FREEZE_F:
        return "freeze"
    if low_f <= FROST_F:
        return "frost"
    return "none"


def radiative(n: Night) -> bool:
    return (n.wind_mph is not None and n.sky_pct is not None
            and n.wind_mph < CALM_WIND_MPH and n.sky_pct < CLEAR_SKY_PCT)


def adjusted_low(n: Night, frost_bias: Optional[str]) -> Optional[float]:
    if n.low_f is None:
        return None
    if frost_bias and radiative(n):
        return n.low_f - BIAS_F if frost_bias == "earlier" else n.low_f + BIAS_F
    return n.low_f


# --- parsing the Weather Service answers -----------------------------------------

def _parse_valid_time(text: str) -> tuple[datetime, timedelta]:
    start_s, _, dur_s = text.partition("/")
    start = datetime.fromisoformat(start_s)
    hours = 0
    rest = dur_s.removeprefix("P")
    days_part, _, time_part = rest.partition("T")
    if days_part.endswith("D"):
        hours += 24 * int(days_part[:-1])
    if time_part:
        num = ""
        for ch in time_part:
            if ch.isdigit():
                num += ch
            elif ch == "H":
                hours += int(num); num = ""
            elif ch == "M":
                num = ""
    return start, timedelta(hours=hours or 1)


def _c_to_f(v):
    return None if v is None else v * 9 / 5 + 32


def _kmh_to_mph(v):
    return None if v is None else v * 0.621371


def _hourly(prop: dict, tz: ZoneInfo, convert=lambda v: v) -> list[tuple[datetime, float]]:
    out = []
    for item in (prop or {}).get("values") or []:
        if item.get("value") is None:
            continue
        start, dur = _parse_valid_time(item["validTime"])
        for h in range(int(dur.total_seconds() // 3600)):
            out.append(((start + timedelta(hours=h)).astimezone(tz), convert(item["value"])))
    return out


def parse_nws(points: dict, gridpoint: dict, text_forecast: Optional[dict], *,
              fetched_at: datetime) -> Forecast:
    """Weather Service JSON -> Forecast. Raises KeyError or ValueError on a
    shape it does not know; the caller treats that as no forecast."""
    pp = points["properties"]
    tzname = pp.get("timeZone") or "UTC"
    tz = ZoneInfo(tzname)
    g = gridpoint["properties"]
    rel = ((pp.get("relativeLocation") or {}).get("properties") or {})
    place = {"city": rel.get("city"), "region": rel.get("state"), "timezone": tzname}

    lows: dict[date, float] = {}
    for item in g["minTemperature"]["values"]:
        start, _ = _parse_valid_time(item["validTime"])
        local = start.astimezone(tz)
        night = local.date() if local.hour >= 12 else local.date() - timedelta(days=1)
        lows[night] = _c_to_f(item["value"])
    highs: dict[date, float] = {}
    for item in g["maxTemperature"]["values"]:
        start, _ = _parse_valid_time(item["validTime"])
        highs[start.astimezone(tz).date()] = _c_to_f(item["value"])

    pop: dict[date, float] = {}
    for t, v in _hourly(g.get("probabilityOfPrecipitation"), tz):
        if 6 <= t.hour < 24:
            pop[t.date()] = max(pop.get(t.date(), 0), v)
    rain: dict[date, float] = {}
    for item in (g.get("quantitativePrecipitation") or {}).get("values") or []:
        if item.get("value") is None:
            continue
        start, _ = _parse_valid_time(item["validTime"])
        d = start.astimezone(tz).date()
        rain[d] = rain.get(d, 0.0) + item["value"] / 25.4
    wind = _hourly(g.get("windSpeed"), tz, _kmh_to_mph)
    sky = _hourly(g.get("skyCover"), tz)

    def overnight(series, d, agg):
        lo = datetime(d.year, d.month, d.day, 18, tzinfo=tz)
        hi = lo + timedelta(hours=14)
        vals = [v for t, v in series if lo <= t < hi]
        return agg(vals) if vals else None

    summaries: dict[date, str] = {}
    current: dict = {}
    for i, p in enumerate((text_forecast or {}).get("properties", {}).get("periods") or []):
        start = datetime.fromisoformat(p["startTime"]).astimezone(tz)
        if i == 0:
            current = {"temp_f": p.get("temperature"), "summary": p.get("shortForecast"),
                       "period": p.get("name")}
        d = start.date()
        if p.get("isDaytime") or d not in summaries:
            summaries[d] = p.get("shortForecast") or summaries.get(d, "")

    today_local = fetched_at.replace(tzinfo=timezone.utc).astimezone(tz).date()
    nights, days = [], []
    for k in range(FORECAST_NIGHTS):
        d = today_local + timedelta(days=k)
        n = Night(date=d, low_f=lows.get(d),
                  wind_mph=overnight(wind, d, max),
                  sky_pct=overnight(sky, d, lambda v: sum(v) / len(v)))
        nights.append(n)
        days.append({"date": d.isoformat(), "high_f": highs.get(d), "low_f": lows.get(d),
                     "precipitation_chance": pop.get(d),
                     "rain_in": round(rain[d], 2) if d in rain else None,
                     "summary": summaries.get(d) or "",
                     "wind_mph": n.wind_mph, "sky_pct": n.sky_pct})
    issued = g.get("updateTime")
    issued_at = (datetime.fromisoformat(issued).astimezone(timezone.utc).replace(tzinfo=None)
                 if issued else fetched_at)
    return Forecast(provider=PROVIDER, provider_name=PROVIDER_NAME, fetched_at=fetched_at,
                    issued_at=issued_at, timezone=tzname, days=days, nights=nights,
                    place=place, current=current)


# --- the cache -------------------------------------------------------------------

def _cache_get(session: Session, cell: str, provider: str, now: datetime) -> Optional[dict]:
    row = session.exec(select(ForecastCache).where(ForecastCache.cell_key == cell)
                       .where(ForecastCache.provider == provider)).first()
    if row is None or row.expires_at <= now:
        return None
    return row.payload


def _cache_put(session: Session, cell: str, provider: str, payload: dict, now: datetime) -> None:
    if WEATHERKIT in provider.lower() or "apple" in provider.lower():
        raise ValueError("Apple WeatherKit data is never stored (PLAN.md D10)")
    row = session.exec(select(ForecastCache).where(ForecastCache.cell_key == cell)
                       .where(ForecastCache.provider == provider)).first()
    if row is None:
        row = ForecastCache(cell_key=cell, provider=provider, payload=payload,
                            fetched_at=now, expires_at=now + CACHE_LIFE)
    else:
        row.payload, row.fetched_at, row.expires_at = payload, now, now + CACHE_LIFE
    session.add(row)


def prune_expired(session: Session, *, now: Optional[datetime] = None) -> int:
    """Delete every cached forecast (and Weather Service points answer) past
    its `expires_at`, in one statement that reads no payloads. Returns the
    count. Called hourly by app.services.housekeeping; the caller commits."""
    now = now or datetime.utcnow()
    result = session.execute(delete(ForecastCache).where(ForecastCache.expires_at <= now))
    return result.rowcount or 0


def _cell(lat: float, lng: float) -> tuple[str, float, float]:
    key = grid.weather_cell_key(lat, lng)
    _, r, c = key.split("_")
    return key, int(r) / 100, int(c) / 100


def _serialise(fc: Forecast) -> dict:
    return {"fetched_at": fc.fetched_at.isoformat(), "issued_at": fc.issued_at.isoformat(),
            "timezone": fc.timezone, "days": fc.days, "place": fc.place, "current": fc.current,
            "nights": [{"date": n.date.isoformat(), "low_f": n.low_f, "wind_mph": n.wind_mph,
                        "sky_pct": n.sky_pct} for n in fc.nights]}


def _deserialise(p: dict) -> Forecast:
    return Forecast(
        provider=PROVIDER, provider_name=PROVIDER_NAME,
        fetched_at=datetime.fromisoformat(p["fetched_at"]),
        issued_at=datetime.fromisoformat(p["issued_at"]),
        timezone=p["timezone"], days=p["days"], place=p.get("place") or {},
        current=p.get("current") or {},
        nights=[Night(date=date.fromisoformat(n["date"]), low_f=n["low_f"],
                      wind_mph=n.get("wind_mph"), sky_pct=n.get("sky_pct"))
                for n in p["nights"]])


class OutsideCoverage(Exception):
    """The Weather Service answered 404 for the point: it does not cover it."""


#: What the points cache holds for a point the Weather Service does not cover.
OUTSIDE = {"outside_coverage": True}


def _fetch_nws(session: Session, cell: str, lat2: float, lng2: float, now: datetime,
               client: site_http.OutboundClient) -> Forecast:
    points = _cache_get(session, cell, POINTS_PROVIDER, now)
    if points is None:
        resp = client.get(f"{NWS_BASE}/points/{lat2:.2f},{lng2:.2f}", headers=NWS_ACCEPT,
                          source_key="nws", raise_for_status=False)
        if resp.status_code == 404:
            _cache_put(session, cell, POINTS_PROVIDER, OUTSIDE, now)
            raise OutsideCoverage(cell)
        if resp.status_code >= 400:
            raise site_http.SourceUnavailable("nws", f"HTTP {resp.status_code}")
        points = resp.json()
        _cache_put(session, cell, POINTS_PROVIDER, points, now)
    if points.get("outside_coverage"):
        raise OutsideCoverage(cell)
    pp = points["properties"]
    base = f"{NWS_BASE}/gridpoints/{pp['gridId']}/{pp['gridX']},{pp['gridY']}"
    gridpoint = client.get(base, headers=NWS_ACCEPT, source_key="nws").json()
    try:
        text = client.get(base + "/forecast", headers=NWS_ACCEPT, source_key="nws").json()
    except site_http.SourceUnavailable:
        text = None  # the numbers still stand; summaries stay empty
    return parse_nws(points, gridpoint, text, fetched_at=now)


def get_forecast(session: Session, lat: float, lng: float, *,
                 now: Optional[datetime] = None,
                 client: Optional[site_http.OutboundClient] = None) -> Optional[Forecast]:
    """The forecast for the cell holding (lat, lng), from the cache when it
    is under three hours old, else from the Weather Service. None when the
    place is outside the Weather Service's coverage or anything fails: the
    plan then runs on normals alone. Commits its cache writes at once, so
    no write lock is held across a later outbound call (the WeatherKit
    second opinion has a 10 second timeout)."""
    now = now or datetime.utcnow()
    try:
        cell, lat2, lng2 = _cell(lat, lng)
    except ValueError:
        return None
    cached = _cache_get(session, cell, PROVIDER, now)
    if cached is not None:
        try:
            return _deserialise(cached)
        except (KeyError, ValueError, TypeError):
            pass
    own = client is None
    try:
        # Home and the seasonal plan wait on this inline, so the Weather
        # Service gets one short attempt per call; with no answer the plan
        # is built from the normals alone and says so.
        client = client or site_http.OutboundClient(
            flag="season_plan", timeout=site_http.INLINE_TIMEOUT, max_retries=0)
        try:
            fc = _fetch_nws(session, cell, lat2, lng2, now, client)
        finally:
            if own:
                client.close()
    except Exception as exc:  # an enhancement, never a hard dependency
        logger.info("forecast unavailable for %s: %s", cell, exc)
        session.commit()  # keeps an "outside coverage" answer
        return None
    _cache_put(session, cell, PROVIDER, _serialise(fc), now)
    session.commit()
    return fc


def outside_coverage(session: Session, lat: float, lng: float, *,
                     now: Optional[datetime] = None) -> bool:
    """True when the Weather Service said, within the cache life, that it
    does not cover this point (a 404 from its points lookup)."""
    try:
        cell, _, _ = _cell(lat, lng)
    except ValueError:
        return False
    hit = _cache_get(session, cell, POINTS_PROVIDER, now or datetime.utcnow())
    return bool(hit and hit.get("outside_coverage"))


# --- Apple WeatherKit as a second opinion (memory only) ----------------------------

def _usage_ok(session: Session, now: datetime) -> bool:
    month = now.strftime("%Y-%m")
    row = session.exec(select(ProviderUsage).where(ProviderUsage.provider == WEATHERKIT)
                       .where(ProviderUsage.month == month)).first()
    return row is None or row.calls < WEATHERKIT_MONTHLY_CAP


def _count_usage(session: Session, now: datetime) -> None:
    month = now.strftime("%Y-%m")
    row = session.exec(select(ProviderUsage).where(ProviderUsage.provider == WEATHERKIT)
                       .where(ProviderUsage.month == month)).first()
    if row is None:
        row = ProviderUsage(provider=WEATHERKIT, month=month, calls=0)
    row.calls += 1
    session.add(row)


def add_second_opinion(session: Session, fc: Optional[Forecast], lat: float, lng: float, *,
                       now: Optional[datetime] = None) -> None:
    """Attach WeatherKit's nightly lows to `fc.second_opinion`, when the
    existing weather service is configured and within the monthly cap.
    WeatherKit's daily minimum for day D is that morning's low, so it is
    filed under the night of D minus one."""
    from app.services import weather  # the existing service, unchanged

    if fc is None or not weather.is_configured():
        return
    now = now or datetime.utcnow()
    cell, lat2, lng2 = _cell(lat, lng)
    hit = _second_opinion_memory.get(cell)
    if hit and time.time() - hit[0] < CACHE_LIFE.total_seconds():
        fc.second_opinion = hit[1]
        return
    if not _usage_ok(session, now):
        return
    try:
        payload = asyncio.run(weather._fetch_weatherkit(lat2, lng2, "en"))
    except RuntimeError:  # an event loop is already running
        return
    _count_usage(session, now)
    if not payload or payload.get("attribution", {}).get("url", "").find("weatherkit") < 0:
        return
    lows = {}
    for d in payload.get("daily") or []:
        try:
            day = date.fromisoformat(d["date"])
        except (KeyError, ValueError):
            continue
        if d.get("low_f") is not None:
            lows[(day - timedelta(days=1)).isoformat()] = d["low_f"]
    _second_opinion_memory[cell] = (time.time(), lows)
    fc.second_opinion = lows


# --- the property's place, from the Weather Service lookup -------------------------

def fill_place(prop: Property, fc: Optional[Forecast]) -> bool:
    """Set the property's city, region, country and time zone from the
    Weather Service lookup for the pin (PLAN.md section 5, D8), once. True
    when something changed."""
    if fc is None or not fc.place or prop.city:
        return False
    prop.city = fc.place.get("city") or None
    prop.region = fc.place.get("region") or None
    prop.timezone = fc.place.get("timezone") or prop.timezone
    prop.country = "United States"
    return True


def forecast_out(fc: Forecast, frost_bias: Optional[str]) -> dict:
    """The contract shape (build spec section 4, Forecast)."""
    days = []
    for d, n in zip(fc.days, fc.nights):
        adj = adjusted_low(n, frost_bias)
        days.append({
            "date": d["date"],
            "high_f": None if d["high_f"] is None else round(d["high_f"]),
            "low_f": None if d["low_f"] is None else round(d["low_f"]),
            "precipitation_chance": d["precipitation_chance"],
            "summary": d["summary"] or _numbers_summary(d),
            "frost_risk": band(None if adj is None else round(adj)),
        })
    return {"provider": fc.provider, "provider_name": fc.provider_name,
            "fetched_at": fc.fetched_at, "days": days}


def _numbers_summary(d: dict) -> str:
    parts = []
    if d.get("high_f") is not None:
        parts.append(f"High {round(d['high_f'])} degrees")
    if d.get("low_f") is not None:
        parts.append(f"low {round(d['low_f'])} overnight")
    return ", ".join(parts) or "No forecast text"


def lead_nights(fc: Forecast, d: date) -> int:
    today = fc.fetched_at.replace(tzinfo=timezone.utc).astimezone(ZoneInfo(fc.timezone)).date()
    return (d - today).days


def local_today(fc: Forecast) -> date:
    return fc.fetched_at.replace(tzinfo=timezone.utc).astimezone(ZoneInfo(fc.timezone)).date()


def in_united_states(lat: float, lng: float) -> bool:
    """The one rule for the whole app (`app.services.coverage`): Open-Meteo
    is never asked about these places on the new routes (PLAN.md D11)."""
    return coverage.in_united_states(lat, lng)
