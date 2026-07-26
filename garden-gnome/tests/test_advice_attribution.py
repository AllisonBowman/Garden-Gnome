"""Apple Weather attribution travels with the advice that used it.

WeatherKit's terms require the credit wherever its data is displayed. Advice
for an exposed plant restates the forecast in words ("hold off — rain
Thursday"), which is weather data on the screen even though no temperature is
shown. The client cannot tell from the prose whether the forecast contributed,
so the server says so explicitly.

Both directions matter: a missing credit is a terms violation, and a credit on
advice that used no forecast claims a source that did not contribute.
"""
import pytest
from sqlmodel import Session, create_engine, select

from app.models.models import (
    Environment, EnvironmentType, Plant, Shelter, Species, TempExposure, User,
)
from app.services import tokens

ATTRIBUTION = {
    "text": " Weather",
    "url": "https://weatherkit.apple.com/legal-attribution.html",
}

FAKE_WEATHER = {
    "current": {"temp_f": 78, "humidity_pct": 55, "uv_index": 6, "condition": "Clear"},
    "daily": [{
        "date": "2026-07-26", "high_f": 88, "low_f": 66,
        "precip_chance_pct": 70, "uv_max": 7,
        "sunrise": None, "sunset": None, "daylight_hours": 14.0,
        "condition": "Rain",
    }],
    "attribution": ATTRIBUTION,
}


@pytest.fixture()
def api(migrated_db_url, monkeypatch):
    """One user with two plants: one outdoors and exposed, one indoors."""
    from fastapi.testclient import TestClient

    from app.db.database import get_session
    from app.main import app

    engine = create_engine(
        migrated_db_url, connect_args={"check_same_thread": False})

    def override():
        with Session(engine) as s:
            yield s

    app.dependency_overrides[get_session] = override
    client = TestClient(app)

    # Never call Apple in a test: the fetch is stubbed, so these assertions run
    # offline and without a key.
    async def fake_fetch(lat, lng, lang="en"):
        return FAKE_WEATHER

    monkeypatch.setattr("app.routers.plants.fetch_weather", fake_fetch)

    with Session(engine) as s:
        species = s.exec(select(Species)).first()
        if species is None:
            species = Species(
                common_name="Test Fern", scientific_name="Testus fernus",
                light_need="medium", humidity_pct_min=40, humidity_pct_max=60,
                temp_f_min=60, temp_f_max=80, soil_type="mix",
            )
            s.add(species)
            s.flush()
        species_id = species.id

        user = User(email="credit@example.com")
        s.add(user)
        s.flush()

        outside = Environment(
            name="balcony", type=EnvironmentType.balcony, user_id=user.id,
            shelter=Shelter.exposed, temp_exposure=TempExposure.outdoor,
            lat=37.77, lng=-122.42,
        )
        inside = Environment(
            name="living room", type=EnvironmentType.home, user_id=user.id,
            shelter=Shelter.sheltered, temp_exposure=TempExposure.indoor,
        )
        s.add(outside)
        s.add(inside)
        s.flush()

        plants = {}
        for label, env in (("outdoor", outside), ("indoor", inside)):
            p = Plant(
                nickname=f"{label}-plant", species_id=species_id,
                environment_id=env.id, user_id=user.id)
            s.add(p)
            s.flush()
            plants[label] = p.id

        headers = {
            "Authorization": f"Bearer {tokens.issue_access_token(user.id)}"}
        s.commit()

    class Api:
        def __init__(self):
            self.client = client
            self.headers = headers
            self.plants = plants

        def advice(self, which):
            return self.client.post(
                f"/plants/{self.plants[which]}/advice", headers=self.headers)

    yield Api()
    app.dependency_overrides.clear()
    engine.dispose()


def test_exposed_plant_advice_carries_the_apple_weather_credit(api):
    r = api.advice("outdoor")
    assert r.status_code == 200
    credit = r.json()["weather_attribution"]
    assert credit is not None, (
        "advice grounded in the forecast must ship the attribution — the app "
        "has no other way to know the credit is owed"
    )
    assert credit["text"] == ATTRIBUTION["text"]
    assert credit["url"].startswith("https://")


def test_indoor_plant_advice_claims_no_weather_source(api):
    r = api.advice("indoor")
    assert r.status_code == 200
    # No forecast was fetched for a sheltered indoor plant, so crediting Apple
    # would be a false statement about where the advice came from.
    assert r.json()["weather_attribution"] is None


def test_advice_still_answers_when_the_forecast_is_unavailable(api, monkeypatch):
    async def no_weather(lat, lng, lang="en"):
        return None

    monkeypatch.setattr("app.routers.plants.fetch_weather", no_weather)
    r = api.advice("outdoor")
    assert r.status_code == 200
    assert r.json()["advice"]  # weather is an enhancement, never a dependency
    assert r.json()["weather_attribution"] is None
