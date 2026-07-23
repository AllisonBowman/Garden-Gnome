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


async def fetch_weather(lat: float, lng: float, lang: str = "en") -> dict | None:
    """Normalized Apple Weather for a coordinate, or None when unconfigured or
    on any error. Cached per (~1km, hour)."""
    token = _build_token()
    if token is None:
        return None

    bucket = (round(lat, 2), round(lng, 2), int(time.time() // _WEATHER_CACHE_TTL))
    if bucket in _weather_cache:
        return _weather_cache[bucket]

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

    payload = normalize(data)
    _weather_cache[bucket] = payload
    return payload
