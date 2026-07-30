"""Apple WeatherKit REST weather service.

The ONLY place that talks to a weather provider. Given an Environment's
coordinates the backend fetches Apple Weather via the WeatherKit REST API,
authenticated with an ES256 JWT signed by a WeatherKit key (the same
`.p8`/Key-ID/Team-ID machinery the app already uses for Sign in with Apple),
and normalizes the response to a compact payload the advisor grounds on and
the app renders.

Design: weather is an *enhancement*, never a hard dependency. Every failure
mode — unconfigured, no coordinates, HTTP/parse error — resolves to `None`,
and callers fall back to weather-free behavior. Units are converted to °F to
match the species care facts the advisor already reasons over.

WeatherKit's terms require showing the Apple Weather attribution + legal link
wherever this data is displayed; the normalized payload carries it.
"""
from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timedelta, timezone

import httpx
import jwt

from app.config import get_settings

logger = logging.getLogger("plantadvocate.weather")

WEATHERKIT_BASE = "https://weatherkit.apple.com/api/v1"
DATASETS = "currentWeather,forecastDaily"
ATTRIBUTION = {
    "text": " Weather",
    "url": "https://weatherkit.apple.com/legal-attribution.html",
}

# Open-Meteo: keyless, free web forecast used as a FALLBACK when WeatherKit is
# unavailable (unconfigured, or — as of 2026-07 — Apple returning NOT_ENABLED).
# Same normalized shape as WeatherKit so callers and the advisor are unchanged;
# its own attribution travels in the payload (CC-BY, credit + link required).
# Note: Open-Meteo's free tier is licensed for non-commercial use — revisit the
# provider before a paid/commercial launch.
OPENMETEO_URL = "https://api.open-meteo.com/v1/forecast"
OPENMETEO_ATTRIBUTION = {
    "text": "Weather data by Open-Meteo.com",
    "url": "https://open-meteo.com/",
}
# WMO weather codes -> WeatherKit-style condition codes, so the client's
# existing conditionText() maps them to friendly labels with no client change.
_WMO_CONDITION = {
    0: "Clear", 1: "MostlyClear", 2: "PartlyCloudy", 3: "Cloudy",
    45: "Foggy", 48: "Foggy",
    51: "Drizzle", 53: "Drizzle", 55: "Drizzle", 56: "Drizzle", 57: "Drizzle",
    61: "Rain", 63: "Rain", 65: "Rain", 66: "Rain", 67: "Rain",
    71: "Snow", 73: "Snow", 75: "Snow", 77: "Snow",
    80: "Showers", 81: "Showers", 82: "Showers", 85: "Snow", 86: "Snow",
    95: "Thunderstorms", 96: "Thunderstorms", 99: "Thunderstorms",
}


def _wmo_condition(code) -> str | None:
    return _WMO_CONDITION.get(code) if isinstance(code, int) else None


def _round_or_none(v) -> int | None:
    return round(v) if isinstance(v, (int, float)) else None


# U.S. National Weather Service: public-domain, free (incl. commercial), no key.
# US-only, and provides neither UV index nor sunrise/sunset — those fields come
# back None. NWS requires a descriptive User-Agent or it returns 403. Preferred
# over Open-Meteo for US coordinates because its data is unrestricted; Open-Meteo
# remains the global fallback for coordinates NWS can't serve.
NWS_BASE = "https://api.weather.gov"
NWS_HEADERS = {
    "User-Agent": "PlantAdvocate/1.0 (plantadvocate.ai)",
    "Accept": "application/geo+json",
}
NWS_ATTRIBUTION = {
    "text": "Weather data by the U.S. National Weather Service",
    "url": "https://www.weather.gov/",
}

_TOKEN_TTL_MIN = 30
_WEATHER_CACHE_TTL = 3600  # seconds — one WeatherKit call per location per hour
_FORECAST_DAYS = 5

# Process-local caches (single Fly machine; a cold start just refetches).
_token_cache: dict = {"jwt": None, "exp": 0.0}
_weather_cache: dict = {}  # (lat2, lng2, hour_bucket) -> normalized payload


def _config() -> tuple[str, str, str, str] | None:
    """(team_id, key_id, service_id, private_key_pem) or None if unconfigured."""
    s = get_settings()
    key = s.weatherkit_private_key_pem()
    if s.apple_team_id and s.weatherkit_key_id and s.weatherkit_service_id and key:
        return s.apple_team_id, s.weatherkit_key_id, s.weatherkit_service_id, key
    return None


def is_configured() -> bool:
    return _config() is not None


def _build_token() -> str | None:
    """A cached ES256 JWT for WeatherKit. Header carries `kid` and
    `id = TeamID.ServiceID`; payload `iss = TeamID`, `sub = ServiceID`."""
    now = time.time()
    if _token_cache["jwt"] and now < _token_cache["exp"] - 60:
        return _token_cache["jwt"]
    cfg = _config()
    if cfg is None:
        return None
    team_id, key_id, service_id, private_key = cfg
    issued = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "iss": team_id,
            "iat": issued,
            "exp": issued + timedelta(minutes=_TOKEN_TTL_MIN),
            "sub": service_id,
        },
        private_key,
        algorithm="ES256",
        headers={"kid": key_id, "id": f"{team_id}.{service_id}"},
    )
    _token_cache.update(jwt=token, exp=now + _TOKEN_TTL_MIN * 60)
    return token


def _c_to_f(celsius) -> int | None:
    return round(celsius * 9 / 5 + 32) if isinstance(celsius, (int, float)) else None


def _daylight_hours(sunrise: str | None, sunset: str | None) -> float | None:
    if not sunrise or not sunset:
        return None
    try:
        a = datetime.fromisoformat(sunrise.replace("Z", "+00:00"))
        b = datetime.fromisoformat(sunset.replace("Z", "+00:00"))
        return round((b - a).total_seconds() / 3600, 1)
    except ValueError:
        return None


def normalize(data: dict) -> dict:
    """WeatherKit REST JSON -> compact payload (°F, %, UV, per-day forecast).

    WeatherKit reports SI units (Celsius, humidity 0-1, precip chance 0-1);
    we convert to the °F / % the rest of the app speaks."""
    cur = data.get("currentWeather") or {}
    current = {
        "temp_f": _c_to_f(cur.get("temperature")),
        "humidity_pct": round(cur["humidity"] * 100) if isinstance(cur.get("humidity"), (int, float)) else None,
        "uv_index": cur.get("uvIndex"),
        "condition": cur.get("conditionCode"),
    }

    days = []
    for d in (data.get("forecastDaily") or {}).get("days", [])[:_FORECAST_DAYS]:
        sunrise, sunset = d.get("sunrise"), d.get("sunset")
        days.append({
            "date": (d.get("forecastStart") or "")[:10],
            "high_f": _c_to_f(d.get("temperatureMax")),
            "low_f": _c_to_f(d.get("temperatureMin")),
            "precip_chance_pct": round(d["precipitationChance"] * 100)
            if isinstance(d.get("precipitationChance"), (int, float)) else None,
            "uv_max": d.get("maxUvIndex"),
            "sunrise": sunrise,
            "sunset": sunset,
            "daylight_hours": _daylight_hours(sunrise, sunset),
            "condition": d.get("conditionCode"),
        })

    return {"current": current, "daily": days, "attribution": ATTRIBUTION}


async def _fetch_weatherkit(lat: float, lng: float, lang: str) -> dict | None:
    """Normalized Apple Weather, or None when unconfigured / on any error."""
    token = _build_token()
    if token is None:
        return None
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
            resp = await client.get(
                f"{WEATHERKIT_BASE}/weather/{lang}/{lat}/{lng}",
                params={"dataSets": DATASETS},
                headers={"Authorization": f"Bearer {token}"},
            )
            resp.raise_for_status()
            data = resp.json()
    except (httpx.HTTPError, ValueError) as e:
        logger.warning("WeatherKit fetch failed for (%.2f, %.2f): %s", lat, lng, e)
        return None
    return normalize(data)


def normalize_openmeteo(data: dict) -> dict:
    """Open-Meteo forecast JSON -> the same compact payload as `normalize`.

    We request °F and % directly, so values need only rounding; WMO weather
    codes map to WeatherKit-style condition codes the client already knows."""
    cur = data.get("current") or {}
    current = {
        "temp_f": _round_or_none(cur.get("temperature_2m")),
        "humidity_pct": _round_or_none(cur.get("relative_humidity_2m")),
        "uv_index": _round_or_none(cur.get("uv_index")),
        "condition": _wmo_condition(cur.get("weather_code")),
    }

    daily = data.get("daily") or {}
    times = daily.get("time") or []

    def col(key: str, i: int):
        arr = daily.get(key) or []
        return arr[i] if i < len(arr) else None

    days = []
    for i, date in enumerate(times[:_FORECAST_DAYS]):
        sunrise, sunset = col("sunrise", i), col("sunset", i)
        days.append({
            "date": date,
            "high_f": _round_or_none(col("temperature_2m_max", i)),
            "low_f": _round_or_none(col("temperature_2m_min", i)),
            "precip_chance_pct": _round_or_none(col("precipitation_probability_max", i)),
            "uv_max": _round_or_none(col("uv_index_max", i)),
            "sunrise": sunrise,
            "sunset": sunset,
            "daylight_hours": _daylight_hours(sunrise, sunset),
            "condition": _wmo_condition(col("weather_code", i)),
        })

    return {"current": current, "daily": days, "attribution": OPENMETEO_ATTRIBUTION}


async def _fetch_openmeteo(lat: float, lng: float) -> dict | None:
    """Normalized Open-Meteo forecast, or None on any error. No key needed."""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
            resp = await client.get(OPENMETEO_URL, params={
                "latitude": lat,
                "longitude": lng,
                "current": "temperature_2m,relative_humidity_2m,weather_code,uv_index",
                "daily": ("weather_code,temperature_2m_max,temperature_2m_min,"
                          "precipitation_probability_max,uv_index_max,sunrise,sunset"),
                "temperature_unit": "fahrenheit",
                "timezone": "auto",
                "forecast_days": _FORECAST_DAYS,
            })
            resp.raise_for_status()
            data = resp.json()
    except (httpx.HTTPError, ValueError) as e:
        logger.warning("Open-Meteo fetch failed for (%.2f, %.2f): %s", lat, lng, e)
        return None
    return normalize_openmeteo(data)


def normalize_nws(periods: list, obs: dict) -> dict:
    """NWS forecast periods (day/night) + a latest station observation -> the
    same compact payload as `normalize`. Period temps are already °F; the
    observation temperature is °C. UV and sunrise/sunset are unavailable from
    NWS, so those fields are None (the client hides them when absent)."""
    current = {
        "temp_f": _c_to_f((obs.get("temperature") or {}).get("value")),
        "humidity_pct": _round_or_none((obs.get("relativeHumidity") or {}).get("value")),
        "uv_index": None,
        "condition": obs.get("textDescription") or None,
    }

    # Fold the alternating day/night periods into one entry per calendar date:
    # daytime -> high + daytime condition, nighttime -> low.
    by_date: dict[str, dict] = {}
    order: list[str] = []
    for p in periods or []:
        date = (p.get("startTime") or "")[:10]
        if not date:
            continue
        if date not in by_date:
            by_date[date] = {"high_f": None, "low_f": None, "precip": None, "condition": None}
            order.append(date)
        d = by_date[date]
        temp = p.get("temperature")
        precip = (p.get("probabilityOfPrecipitation") or {}).get("value")
        if p.get("isDaytime"):
            if isinstance(temp, (int, float)):
                d["high_f"] = temp
            d["condition"] = p.get("shortForecast") or d["condition"]
            if precip is not None:
                d["precip"] = precip
        else:
            if isinstance(temp, (int, float)):
                d["low_f"] = temp
            if d["condition"] is None:
                d["condition"] = p.get("shortForecast")
            if d["precip"] is None and precip is not None:
                d["precip"] = precip

    days = []
    for date in order[:_FORECAST_DAYS]:
        d = by_date[date]
        days.append({
            "date": date,
            "high_f": _round_or_none(d["high_f"]),
            "low_f": _round_or_none(d["low_f"]),
            "precip_chance_pct": _round_or_none(d["precip"]),
            "uv_max": None,
            "sunrise": None,
            "sunset": None,
            "daylight_hours": None,
            "condition": d["condition"],
        })

    return {"current": current, "daily": days, "attribution": NWS_ATTRIBUTION}


async def _nws_latest_obs(client: httpx.AsyncClient, stations_url: str | None) -> dict:
    """Best-effort latest observation for the nearest station (temp, humidity,
    condition). Returns {} on any problem — the forecast still stands alone."""
    if not stations_url:
        return {}
    try:
        sresp = await client.get(stations_url)
        sresp.raise_for_status()
        feats = sresp.json().get("features") or []
        station_id = feats[0]["properties"]["stationIdentifier"]
        obs = await client.get(f"{NWS_BASE}/stations/{station_id}/observations/latest")
        obs.raise_for_status()
        return obs.json().get("properties") or {}
    except (httpx.HTTPError, ValueError, KeyError, IndexError):
        return {}


async def _fetch_nws(lat: float, lng: float) -> dict | None:
    """Normalized NWS forecast for a US coordinate, or None (non-US / any error).
    Two-step: /points resolves the grid + station URLs, then the forecast."""
    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(10.0), headers=NWS_HEADERS, follow_redirects=True,
        ) as client:
            # NWS rejects coordinates with more than 4 decimal places (301), so
            # trim before asking — geocoded env coords carry more precision.
            presp = await client.get(f"{NWS_BASE}/points/{lat:.4f},{lng:.4f}")
            presp.raise_for_status()
            props = (presp.json().get("properties") or {})
            forecast_url = props.get("forecast")
            if not forecast_url:
                return None
            forecast = await client.get(forecast_url)
            forecast.raise_for_status()
            periods = (forecast.json().get("properties") or {}).get("periods") or []
            obs = await _nws_latest_obs(client, props.get("observationStations"))
    except (httpx.HTTPError, ValueError, KeyError) as e:
        logger.warning("NWS fetch failed for (%.2f, %.2f): %s", lat, lng, e)
        return None
    if not periods:
        return None
    return normalize_nws(periods, obs)


async def fetch_weather(lat: float, lng: float, lang: str = "en") -> dict | None:
    """Normalized local weather for a coordinate, cached per (~1km, hour).

    Provider chain, first that answers wins: Apple WeatherKit (nicest data + the
    Apple Weather credit, when the entitlement works) → the U.S. National Weather
    Service (public-domain, US-only) → keyless Open-Meteo (global fallback). The
    payload's attribution always names whichever source answered, so the on-
    screen credit is honest. None only when every provider fails."""
    bucket = (round(lat, 2), round(lng, 2), int(time.time() // _WEATHER_CACHE_TTL))
    if bucket in _weather_cache:
        return _weather_cache[bucket]

    payload = (
        await _fetch_weatherkit(lat, lng, lang)
        or await _fetch_nws(lat, lng)
        or await _fetch_openmeteo(lat, lng)
    )

    if payload is not None:
        _weather_cache[bucket] = payload
    return payload
