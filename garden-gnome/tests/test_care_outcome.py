"""Plan 1.5: a care log records what the check ended in.

The watering verb is *check*; "still damp" is a loggable success. Outcomes
are optional (quick-logs may omit them), constrained to the action they
belong to, and never invented for actions that don't take one.
"""
import pytest
from sqlmodel import Session, create_engine, select

from app.models.models import (
    Environment, EnvironmentType, Plant, Species, User,
)
from app.services import tokens


@pytest.fixture()
def api(migrated_db_url):
    """One user, one plant, an authenticated client."""
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
        species = s.exec(select(Species)).first()
        if species is None:
            species = Species(
                common_name="Outcome Fern", scientific_name="Exitus testus",
                light_need="medium", humidity_pct_min=40, humidity_pct_max=60,
                temp_f_min=60, temp_f_max=80, soil_type="mix",
            )
            s.add(species)
            s.flush()
        user = User(email="outcomes@example.com")
        s.add(user)
        s.flush()
        env = Environment(
            name="outcome-home", type=EnvironmentType.home, user_id=user.id)
        s.add(env)
        s.flush()
        plant = Plant(
            nickname="checked-plant", species_id=species.id,
            environment_id=env.id, user_id=user.id)
        s.add(plant)
        s.flush()
        plant_id = plant.id
        headers = {
            "Authorization": f"Bearer {tokens.issue_access_token(user.id)}"}
        s.commit()

    class Api:
        pass

    a = Api()
    a.client = client
    a.plant_id = plant_id
    a.headers = headers
    yield a
    app.dependency_overrides.clear()
    engine.dispose()


def _log(api, payload):
    return api.client.post(
        f"/plants/{api.plant_id}/logs", json=payload, headers=api.headers)


def test_watered_outcome_round_trips(api):
    r = _log(api, {"action": "water", "outcome": "watered"})
    assert r.status_code == 201
    assert r.json()["outcome"] == "watered"

    listed = api.client.get(
        f"/plants/{api.plant_id}/logs", headers=api.headers).json()
    assert listed[-1]["outcome"] == "watered"


def test_still_damp_is_a_loggable_result(api):
    r = _log(api, {"action": "water", "outcome": "checked_not_needed"})
    assert r.status_code == 201
    assert r.json()["outcome"] == "checked_not_needed"


def test_repot_inspection_outcomes_accepted(api):
    for outcome in ("repotted", "top_dressed", "checked_fine"):
        r = _log(api, {"action": "repot", "outcome": outcome})
        assert r.status_code == 201, outcome
        assert r.json()["outcome"] == outcome


def test_outcome_is_optional_and_null_by_default(api):
    r = _log(api, {"action": "water"})
    assert r.status_code == 201
    assert r.json()["outcome"] is None


def test_outcome_must_belong_to_its_action(api):
    # A fertilize can't end in "watered", and pruning takes no outcome at all.
    assert _log(
        api, {"action": "fertilize", "outcome": "watered"}).status_code == 422
    assert _log(
        api, {"action": "prune", "outcome": "checked_fine"}).status_code == 422
    assert _log(
        api, {"action": "water", "outcome": "repotted"}).status_code == 422


def test_unknown_outcome_is_refused(api):
    assert _log(
        api, {"action": "water", "outcome": "guessed"}).status_code == 422
