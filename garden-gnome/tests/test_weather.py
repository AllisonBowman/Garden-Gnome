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
async def test_fetch_weather_unconfigured_returns_none(monkeypatch):
    monkeypatch.delenv("WEATHERKIT_KEY_ID", raising=False)
    from app.config import get_settings
    get_settings.cache_clear()
    weather._token_cache.update(jwt=None, exp=0.0)
    try:
        assert await weather.fetch_weather(39.29, -76.61) is None
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
