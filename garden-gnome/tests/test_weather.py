"""Weather service (Apple WeatherKit REST) + the environment weather endpoint.

The WeatherKit HTTP call is never made in tests — we test the pure normalizer,
the JWT construction (with a generated EC key), the unconfigured/no-location
degradation, and the endpoint against a monkeypatched fetch.
"""
import pytest
from sqlmodel import Session, create_engine, select

import app.services.weather as weather


# A representative slice of a WeatherKit REST response (SI units).
SAMPLE_WEATHERKIT = {
    "currentWeather": {
        "temperature": 24.0,        # °C -> 75 °F
        "humidity": 0.55,           # -> 55%
        "uvIndex": 6,
        "conditionCode": "PartlyCloudy",
    },
    "forecastDaily": {
        "days": [
            {
                "forecastStart": "2026-07-24T00:00:00Z",
                "temperatureMax": 30.0,   # -> 86 °F
                "temperatureMin": 18.0,   # -> 64 °F
                "precipitationChance": 0.8,
                "maxUvIndex": 8,
                "sunrise": "2026-07-24T09:50:00Z",
                "sunset": "2026-07-25T00:20:00Z",  # ~14.5h daylight
                "conditionCode": "Rain",
            },
        ],
    },
}


# --- normalize (pure) -----------------------------------------------------

def test_normalize_converts_units_and_shape():
    out = weather.normalize(SAMPLE_WEATHERKIT)
    assert out["current"] == {
        "temp_f": 75, "humidity_pct": 55, "uv_index": 6, "condition": "PartlyCloudy",
    }
    day = out["daily"][0]
    assert day["high_f"] == 86 and day["low_f"] == 64
    assert day["precip_chance_pct"] == 80
    assert day["uv_max"] == 8
    assert day["daylight_hours"] == pytest.approx(14.5, abs=0.1)
    assert out["attribution"]["url"].startswith("https://weatherkit.apple.com")


def test_normalize_tolerates_missing_fields():
    out = weather.normalize({})
    assert out["current"]["temp_f"] is None
    assert out["daily"] == []


# --- Open-Meteo fallback normalizer (pure) --------------------------------

# A representative Open-Meteo response (already °F / % via request params).
SAMPLE_OPENMETEO = {
    "current": {
        "temperature_2m": 83.9, "relative_humidity_2m": 42,
        "weather_code": 2, "uv_index": 7.3,
    },
    "daily": {
        "time": ["2026-07-30", "2026-07-31"],
        "weather_code": [3, 81],
        "temperature_2m_max": [85.3, 89.7],
        "temperature_2m_min": [68.1, 67.4],
        "precipitation_probability_max": [10, 55],
        "uv_index_max": [7.8, 8.1],
        "sunrise": ["2026-07-30T06:05", "2026-07-31T06:06"],
        "sunset": ["2026-07-30T20:25", "2026-07-31T20:24"],  # ~14.3h daylight
    },
}


def test_normalize_openmeteo_shape_and_condition_mapping():
    out = weather.normalize_openmeteo(SAMPLE_OPENMETEO)
    # Rounded, and WMO code 2 -> WeatherKit-style "PartlyCloudy"
    assert out["current"] == {
        "temp_f": 84, "humidity_pct": 42, "uv_index": 7, "condition": "PartlyCloudy",
    }
    d0, d1 = out["daily"]
    assert d0["high_f"] == 85 and d0["low_f"] == 68
    assert d0["precip_chance_pct"] == 10 and d0["uv_max"] == 8
    assert d0["condition"] == "Cloudy"        # WMO 3 (overcast)
    assert d1["condition"] == "Showers"       # WMO 81 (rain showers)
    assert d0["daylight_hours"] == pytest.approx(14.3, abs=0.1)
    # Fallback source is credited honestly, not as Apple.
    assert out["attribution"]["url"].startswith("https://open-meteo.com")


def test_normalize_openmeteo_tolerates_missing_fields():
    out = weather.normalize_openmeteo({})
    assert out["current"]["temp_f"] is None
    assert out["daily"] == []


# --- NWS fallback normalizer (pure) ---------------------------------------

# NWS forecast periods alternate daytime/nighttime; temps already °F.
SAMPLE_NWS_PERIODS = [
    {"isDaytime": True,  "startTime": "2026-07-30T14:00:00-04:00", "temperature": 86,
     "probabilityOfPrecipitation": {"value": 1}, "shortForecast": "Partly Sunny"},
    {"isDaytime": False, "startTime": "2026-07-30T18:00:00-04:00", "temperature": 68,
     "probabilityOfPrecipitation": {"value": 20}, "shortForecast": "Partly Cloudy"},
    {"isDaytime": True,  "startTime": "2026-07-31T06:00:00-04:00", "temperature": 90,
     "probabilityOfPrecipitation": {"value": 0}, "shortForecast": "Sunny"},
    {"isDaytime": False, "startTime": "2026-07-31T18:00:00-04:00", "temperature": 67,
     "probabilityOfPrecipitation": {"value": 5}, "shortForecast": "Clear"},
]
SAMPLE_NWS_OBS = {
    "temperature": {"value": 28.3},        # °C -> 83 °F
    "relativeHumidity": {"value": 48.5},   # -> 48%
    "textDescription": "Cloudy",
}


def test_normalize_nws_pairs_day_night_and_omits_uv_and_daylight():
    out = weather.normalize_nws(SAMPLE_NWS_PERIODS, SAMPLE_NWS_OBS)
    assert out["current"] == {
        "temp_f": 83, "humidity_pct": 48, "uv_index": None, "condition": "Cloudy",
    }
    d0, d1 = out["daily"]
    assert d0["date"] == "2026-07-30"
    assert d0["high_f"] == 86 and d0["low_f"] == 68   # daytime high, nighttime low
    assert d0["precip_chance_pct"] == 1
    assert d0["condition"] == "Partly Sunny"          # daytime condition wins
    assert d0["uv_max"] is None and d0["daylight_hours"] is None  # NWS lacks both
    assert d1["high_f"] == 90 and d1["low_f"] == 67
    assert out["attribution"]["url"].startswith("https://www.weather.gov")


def test_normalize_nws_tolerates_empty():
    out = weather.normalize_nws([], {})
    assert out["current"]["temp_f"] is None
    assert out["daily"] == []


# --- token / configuration ------------------------------------------------

def _ec_private_key_pem() -> str:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec

    key = ec.generate_private_key(ec.SECP256R1())
    return key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()


def test_build_token_none_when_unconfigured(monkeypatch):
    monkeypatch.delenv("WEATHERKIT_KEY_ID", raising=False)
    from app.config import get_settings
    get_settings.cache_clear()
    weather._token_cache.update(jwt=None, exp=0.0)
    try:
        assert weather.is_configured() is False
        assert weather._build_token() is None
    finally:
        get_settings.cache_clear()


def test_build_token_has_weatherkit_header_and_claims(monkeypatch):
    import jwt as pyjwt
    from app.config import get_settings

    monkeypatch.setenv("APPLE_TEAM_ID", "TEAM123456")
    monkeypatch.setenv("WEATHERKIT_KEY_ID", "KEY7654321")
    monkeypatch.setenv("WEATHERKIT_SERVICE_ID", "com.example.plantadvocate.weather")
    monkeypatch.setenv("WEATHERKIT_PRIVATE_KEY", _ec_private_key_pem().replace("\n", "\\n"))
    get_settings.cache_clear()
    weather._token_cache.update(jwt=None, exp=0.0)
    try:
        token = weather._build_token()
        assert token is not None
        header = pyjwt.get_unverified_header(token)
        assert header["alg"] == "ES256"
        assert header["kid"] == "KEY7654321"
        assert header["id"] == "TEAM123456.com.example.plantadvocate.weather"
        claims = pyjwt.decode(token, options={"verify_signature": False})
        assert claims["iss"] == "TEAM123456"
        assert claims["sub"] == "com.example.plantadvocate.weather"
    finally:
        get_settings.cache_clear()
        weather._token_cache.update(jwt=None, exp=0.0)


@pytest.mark.asyncio
async def test_fetch_weather_none_when_all_providers_fail(monkeypatch):
    # WeatherKit unconfigured, NWS + Open-Meteo unavailable -> None. Both web
    # providers are stubbed so the test never makes a real network call.
    monkeypatch.delenv("WEATHERKIT_KEY_ID", raising=False)
    from app.config import get_settings
    get_settings.cache_clear()
    weather._token_cache.update(jwt=None, exp=0.0)
    weather._weather_cache.clear()

    async def _none(lat, lng):
        return None
    monkeypatch.setattr(weather, "_fetch_nws", _none)
    monkeypatch.setattr(weather, "_fetch_openmeteo", _none)
    try:
        assert await weather.fetch_weather(39.29, -76.61) is None
    finally:
        get_settings.cache_clear()


@pytest.mark.asyncio
async def test_fetch_weather_prefers_nws_over_openmeteo(monkeypatch):
    # NWS answers first for a US coord; Open-Meteo must not even be called.
    monkeypatch.delenv("WEATHERKIT_KEY_ID", raising=False)
    from app.config import get_settings
    get_settings.cache_clear()
    weather._token_cache.update(jwt=None, exp=0.0)
    weather._weather_cache.clear()

    nws = {"current": {}, "daily": [], "attribution": weather.NWS_ATTRIBUTION}

    async def _nws(lat, lng):
        return nws

    async def _boom(lat, lng):
        raise AssertionError("Open-Meteo must not run when NWS answers")
    monkeypatch.setattr(weather, "_fetch_nws", _nws)
    monkeypatch.setattr(weather, "_fetch_openmeteo", _boom)
    try:
        out = await weather.fetch_weather(38.98, -76.94)
        assert out is nws
        assert out["attribution"]["url"].startswith("https://www.weather.gov")
    finally:
        get_settings.cache_clear()


@pytest.mark.asyncio
async def test_fetch_weather_falls_back_to_openmeteo_when_nws_empty(monkeypatch):
    # Non-US / NWS-less coord: falls through NWS to Open-Meteo, credited to it.
    monkeypatch.delenv("WEATHERKIT_KEY_ID", raising=False)
    from app.config import get_settings
    get_settings.cache_clear()
    weather._token_cache.update(jwt=None, exp=0.0)
    weather._weather_cache.clear()

    sentinel = {"current": {}, "daily": [], "attribution": weather.OPENMETEO_ATTRIBUTION}

    async def _none(lat, lng):
        return None

    async def _fake_openmeteo(lat, lng):
        return sentinel
    monkeypatch.setattr(weather, "_fetch_nws", _none)
    monkeypatch.setattr(weather, "_fetch_openmeteo", _fake_openmeteo)
    try:
        out = await weather.fetch_weather(1.0, 2.0)
        assert out is sentinel
        assert out["attribution"]["url"].startswith("https://open-meteo.com")
    finally:
        get_settings.cache_clear()


# --- endpoint -------------------------------------------------------------

@pytest.fixture()
def api(migrated_db_url):
    from fastapi.testclient import TestClient

    from app.db.database import get_session
    from app.main import app
    from app.models.models import Environment, EnvironmentType, User
    from app.services import tokens

    engine = create_engine(migrated_db_url, connect_args={"check_same_thread": False})

    def override():
        with Session(engine) as s:
            yield s

    app.dependency_overrides[get_session] = override

    with Session(engine) as s:
        user = User(email="weather@example.com")
        s.add(user)
        s.flush()
        located = Environment(name="Balcony", type=EnvironmentType.balcony,
                              user_id=user.id, lat=39.29, lng=-76.61)
        no_loc = Environment(name="Desk", type=EnvironmentType.home, user_id=user.id)
        s.add(located)
        s.add(no_loc)
        s.commit()
        ids = {"located": located.id, "no_loc": no_loc.id}
        headers = {"Authorization": f"Bearer {tokens.issue_access_token(user.id)}"}

    client = TestClient(app)
    try:
        yield client, headers, ids
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_weather_endpoint_no_location(api):
    client, headers, ids = api
    resp = client.get(f"/environments/{ids['no_loc']}/weather", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["available"] is False
    assert body["weather"] is None
    assert "location" in body["detail"].lower()


def test_weather_endpoint_happy_path(api, monkeypatch):
    client, headers, ids = api

    async def fake_fetch(lat, lng, lang="en"):
        assert (round(lat, 2), round(lng, 2)) == (39.29, -76.61)
        return weather.normalize(SAMPLE_WEATHERKIT)

    monkeypatch.setattr("app.routers.environments.fetch_weather", fake_fetch)
    resp = client.get(f"/environments/{ids['located']}/weather", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["available"] is True
    assert body["weather"]["current"]["temp_f"] == 75
    assert body["weather"]["daily"][0]["precip_chance_pct"] == 80


def test_weather_endpoint_requires_auth(api):
    client, _, ids = api
    assert client.get(f"/environments/{ids['located']}/weather").status_code == 401


def test_adding_a_location_later_turns_weather_on(api, monkeypatch):
    """An environment created without coordinates can be given them afterwards.

    This is the path that made weather look broken on device: environments
    predating the address picker had no lat/lng, and nothing in the app could
    add them, so the forecast never appeared no matter what the caretaker did
    with location permission. The server always supported the PATCH — only the
    screen was missing — so this pins the half that has to keep working."""
    client, headers, ids = api

    before = client.get(f"/environments/{ids['no_loc']}/weather", headers=headers)
    assert before.json()["available"] is False

    patched = client.patch(
        f"/environments/{ids['no_loc']}",
        json={"city": "Baltimore", "region": "MD", "country": "US",
              "lat": 39.29, "lng": -76.61},
        headers=headers,
    )
    assert patched.status_code == 200
    assert patched.json()["lat"] == 39.29

    async def fake_fetch(lat, lng, lang="en"):
        return weather.normalize(SAMPLE_WEATHERKIT)

    monkeypatch.setattr("app.routers.environments.fetch_weather", fake_fetch)
    after = client.get(f"/environments/{ids['no_loc']}/weather", headers=headers)
    assert after.json()["available"] is True
