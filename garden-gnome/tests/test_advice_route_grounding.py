"""The groundedness guard holds through the wired route, not just the service.

test_advisor_grounding.py covers get_care_advice() directly. This exercises
POST /plants/{id}/advice end to end — real router, real auth, real session —
because that is the path a caretaker's phone actually takes, and a guard that
works in the service but is bypassed by the route protects nobody.
"""
import pytest
from sqlmodel import Session, create_engine, select

from app.models.models import (
    CareSchedule, CareType, Environment, EnvironmentType, Plant, Species, User,
)
from app.services import advisor, tokens


@pytest.fixture()
def api(migrated_db_url):
    """One user with a plant whose species has a watering schedule."""
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

    with Session(engine) as s:
        species = Species(
            common_name="Guard Fern", scientific_name="Guardus testus",
            light_need="medium", humidity_pct_min=40, humidity_pct_max=60,
            temp_f_min=60, temp_f_max=80, soil_type="mix",
        )
        s.add(species)
        s.flush()
        s.add(CareSchedule(
            species_id=species.id, care_type=CareType.water,
            interval_days_min=5, interval_days_max=9,
        ))
        user = User(email="guard@example.com")
        s.add(user)
        s.flush()
        env = Environment(name="home", type=EnvironmentType.home, user_id=user.id)
        s.add(env)
        s.flush()
        plant = Plant(
            nickname="Ferny", species_id=species.id,
            environment_id=env.id, user_id=user.id,
        )
        s.add(plant)
        s.flush()
        ctx = {
            "plant_id": plant.id,
            "headers": {
                "Authorization": f"Bearer {tokens.issue_access_token(user.id)}"
            },
        }
        s.commit()

    class Api:
        def __init__(self):
            self.client = client
            self.plant_id = ctx["plant_id"]
            self.headers = ctx["headers"]

        def advice(self, symptoms=""):
            return self.client.post(
                f"/plants/{self.plant_id}/advice",
                json={"symptoms": symptoms},
                headers=self.headers,
            )

    yield Api()
    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture()
def drifting_backend(monkeypatch):
    def _install(text):
        monkeypatch.setitem(advisor._BACKENDS, "anthropic", lambda *a, **k: text)
        monkeypatch.setattr(advisor, "BACKEND", "anthropic")
        monkeypatch.setattr(advisor, "SYMPTOMS_BACKEND", "anthropic")
    return _install


def test_the_screenshot_letter_cannot_reach_the_client(api, drifting_backend):
    """The exact defect from 2026-07-20-gnome-voice-letter.png, served by the
    model backend, must not appear in the response body."""
    drifting_backend(
        "Dear Plant Owner,\n\n"
        "I've watered your lovely Ferny two days ago, and I'll send you a "
        "reminder when it's time to fertilize.\n\nLove,\n\n[Your Name]"
    )
    r = api.advice()
    assert r.status_code == 200
    body = r.json()

    assert "[Your Name]" not in body["advice"]
    assert "I've watered" not in body["advice"]
    assert "reminder" not in body["advice"]
    # And the badge tells the truth about what replaced it.
    assert body["backend"] == "stub"
    assert body["guarded"] is True


def test_guarded_response_still_carries_real_advice(api, drifting_backend):
    drifting_backend("I'll repot it for you in 90 days.")
    body = api.advice().json()

    # Not an error string — the deterministic stub, which is always computable.
    assert "Watering" in body["advice"]
    assert body["nickname"] == "Ferny"


def test_grounded_model_output_reaches_the_client_intact(api, drifting_backend):
    drifting_backend("Ferny has no watering logged yet; every 5-9 days suits it.")
    body = api.advice().json()

    assert body["backend"] == "anthropic"
    assert body["guarded"] is False
    assert "5-9 days" in body["advice"]


def test_stub_backend_reports_itself_unguarded(api, monkeypatch):
    monkeypatch.setattr(advisor, "BACKEND", "stub")
    monkeypatch.setattr(advisor, "SYMPTOMS_BACKEND", "stub")
    body = api.advice().json()

    assert body["backend"] == "stub"
    assert body["guarded"] is False
