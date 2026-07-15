"""Phase 6 acceptance: data isolation between users + census consent.

Two real users (A and B) with real tokens hit the real routers; every
cross-user access must 404 (never 403 — no id probing), lists must be
filtered, transfers must be impossible across accounts, and the census
export must contain only opted-in users' data with rotated identifiers.
"""
import pytest
from sqlmodel import Session, create_engine, select

from app.models.models import (
    Environment, EnvironmentType, Plant, Species, User,
)
from app.services import tokens


@pytest.fixture()
def iso(migrated_db_url):
    """Two users with an environment + plant each, plus an API client."""
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
                common_name="Iso Fern", scientific_name="Isolatus testus",
                light_need="medium", humidity_pct_min=40, humidity_pct_max=60,
                temp_f_min=60, temp_f_max=80, soil_type="mix",
            )
            s.add(species)
            s.flush()
        species_id = species.id  # capture while still session-bound

        data = {}
        for label in ("a", "b"):
            user = User(email=f"user-{label}@example.com")
            s.add(user)
            s.flush()
            env = Environment(
                name=f"{label}-home", type=EnvironmentType.home,
                user_id=user.id)
            s.add(env)
            s.flush()
            plant = Plant(
                nickname=f"{label}-plant", species_id=species_id,
                environment_id=env.id, user_id=user.id)
            s.add(plant)
            s.flush()
            data[label] = {
                "user_id": user.id, "env_id": env.id, "plant_id": plant.id,
                "headers": {
                    "Authorization":
                        f"Bearer {tokens.issue_access_token(user.id)}"},
            }
        s.commit()

    class Iso:
        def __init__(self):
            self.client = client
            self.engine = engine
            self.a = data["a"]
            self.b = data["b"]
            self.species_id = species_id

        def db(self):
            return Session(self.engine)

    yield Iso()
    app.dependency_overrides.clear()
    engine.dispose()


# --- Plants -------------------------------------------------------------------


def test_unauthenticated_is_401(iso):
    assert iso.client.get("/plants/").status_code == 401
    assert iso.client.get("/environments/").status_code == 401
    assert iso.client.get("/census/summary").status_code == 401
    assert iso.client.get("/census/export").status_code == 401


def test_plant_list_is_filtered(iso):
    r = iso.client.get("/plants/", headers=iso.a["headers"])
    assert r.status_code == 200
    nicknames = {p["nickname"] for p in r.json()}
    assert "a-plant" in nicknames
    assert "b-plant" not in nicknames


def test_cannot_read_other_users_plant(iso):
    r = iso.client.get(
        f"/plants/{iso.b['plant_id']}", headers=iso.a["headers"])
    assert r.status_code == 404  # not 403 — no id probing


def test_cannot_modify_other_users_plant(iso):
    assert iso.client.post(
        f"/plants/{iso.b['plant_id']}/logs",
        json={"action": "water"}, headers=iso.a["headers"],
    ).status_code == 404
    assert iso.client.delete(
        f"/plants/{iso.b['plant_id']}", headers=iso.a["headers"],
    ).status_code == 404
    with iso.db() as s:  # B's plant untouched
        assert s.get(Plant, iso.b["plant_id"]) is not None


def test_cannot_get_advice_or_timeline_for_other_users_plant(iso):
    assert iso.client.post(
        f"/plants/{iso.b['plant_id']}/advice", headers=iso.a["headers"],
    ).status_code == 404
    assert iso.client.get(
        f"/plants/{iso.b['plant_id']}/timeline", headers=iso.a["headers"],
    ).status_code == 404
    assert iso.client.get(
        f"/plants/{iso.b['plant_id']}/logs", headers=iso.a["headers"],
    ).status_code == 404


def test_create_plant_defaults_to_callers_env_not_first_in_db(iso):
    # B's environment has the LOWEST id in the table (created second in the
    # fixture? ensure by checking) — regardless, A creating a plant with no
    # environment_id must land in A's env, never "first env in the DB".
    r = iso.client.post(
        "/plants/",
        json={"nickname": "a-second", "species_id": iso.species_id},
        headers=iso.a["headers"],
    )
    assert r.status_code == 201, r.text
    assert r.json()["environment_id"] == iso.a["env_id"]
    assert r.json()["environment_id"] != iso.b["env_id"]


def test_create_plant_into_other_users_env_404(iso):
    r = iso.client.post(
        "/plants/",
        json={
            "nickname": "intruder", "species_id": iso.species_id,
            "environment_id": iso.b["env_id"],
        },
        headers=iso.a["headers"],
    )
    assert r.status_code == 404


# --- Transfers ----------------------------------------------------------------


def test_cannot_transfer_own_plant_into_other_users_env(iso):
    r = iso.client.post(
        f"/plants/{iso.a['plant_id']}/transfer",
        json={"to_environment_id": iso.b["env_id"]},
        headers=iso.a["headers"],
    )
    assert r.status_code == 404
    with iso.db() as s:  # unchanged
        assert s.get(Plant, iso.a["plant_id"]).environment_id == iso.a["env_id"]


def test_cannot_transfer_other_users_plant_at_all(iso):
    r = iso.client.post(
        f"/plants/{iso.b['plant_id']}/transfer",
        json={"to_environment_id": iso.a["env_id"]},
        headers=iso.a["headers"],
    )
    assert r.status_code == 404


def test_transfer_within_own_account_works(iso):
    r = iso.client.post(
        "/environments/",
        json={"name": "a-balcony", "type": "balcony"},
        headers=iso.a["headers"],
    )
    assert r.status_code == 201, r.text
    new_env = r.json()["id"]
    t = iso.client.post(
        f"/plants/{iso.a['plant_id']}/transfer",
        json={"to_environment_id": new_env},
        headers=iso.a["headers"],
    )
    assert t.status_code == 200, t.text
    assert t.json()["environment_id"] == new_env


# --- Environments ---------------------------------------------------------------


def test_environment_list_and_read_scoped(iso):
    r = iso.client.get("/environments/", headers=iso.a["headers"])
    names = {e["name"] for e in r.json()}
    assert "a-home" in names and "b-home" not in names
    assert iso.client.get(
        f"/environments/{iso.b['env_id']}", headers=iso.a["headers"],
    ).status_code == 404


def test_cannot_patch_other_users_environment(iso):
    r = iso.client.patch(
        f"/environments/{iso.b['env_id']}",
        json={"name": "hijacked"}, headers=iso.a["headers"],
    )
    assert r.status_code == 404


def test_delete_environment_with_plants_409(iso):
    r = iso.client.delete(
        f"/environments/{iso.a['env_id']}", headers=iso.a["headers"])
    assert r.status_code == 409


def test_delete_empty_environment_204(iso):
    r = iso.client.post(
        "/environments/",
        json={"name": "a-empty", "type": "other"},
        headers=iso.a["headers"],
    )
    env_id = r.json()["id"]
    assert iso.client.delete(
        f"/environments/{env_id}", headers=iso.a["headers"],
    ).status_code == 204


# --- Census consent (decision 3) -------------------------------------------------


def test_census_summary_is_callers_own(iso):
    r = iso.client.get("/census/summary", headers=iso.a["headers"])
    assert r.status_code == 200
    assert r.json()["total_plants"] == 1  # only A's plant, not B's


def test_export_excludes_non_opted_in_users(iso):
    with iso.db() as s:
        a_uuid = s.get(Plant, iso.a["plant_id"]).plant_uuid
        b_uuid = s.get(Plant, iso.b["plant_id"]).plant_uuid

    # Neither A nor B has opted in -> neither's plants may be exported
    # (assert on OUR plants, not global emptiness — the test DB is shared
    # across modules and other tests may have opted-in users of their own)
    r = iso.client.get("/census/export", headers=iso.a["headers"])
    assert r.status_code == 200
    uuids = {p["plant_uuid"] for p in r.json()["plants"]}
    assert a_uuid not in uuids
    assert b_uuid not in uuids

    # A opts in via PATCH /me; B stays out
    p = iso.client.patch(
        "/me", json={"census_opt_in": True}, headers=iso.a["headers"])
    assert p.status_code == 200 and p.json()["census_opt_in"] is True

    uuids = {p["plant_uuid"] for p in iso.client.get(
        "/census/export", headers=iso.a["headers"]).json()["plants"]}
    assert a_uuid in uuids
    assert b_uuid not in uuids  # B never opted in — never exported


def test_export_has_no_stable_env_ids_and_no_latlng(iso):
    iso.client.patch(
        "/me", json={"census_opt_in": True}, headers=iso.a["headers"])
    e1 = iso.client.get("/census/export", headers=iso.a["headers"]).json()
    e2 = iso.client.get("/census/export", headers=iso.a["headers"]).json()

    def env_refs(body):
        return {p["environment"]["ref"]
                for p in body["plants"] if p["environment"]}

    refs1, refs2 = env_refs(e1), env_refs(e2)
    assert refs1 and refs2
    assert refs1.isdisjoint(refs2)  # rotated per export — not linkable

    with iso.db() as s:
        real_uuids = {e.uuid for e in s.exec(select(Environment)).all()}
    assert refs1.isdisjoint(real_uuids)  # never the real environment uuid

    for p in e1["plants"]:
        if p["environment"]:
            assert "lat" not in p["environment"]
            assert "lng" not in p["environment"]
            assert "uuid" not in p["environment"]
