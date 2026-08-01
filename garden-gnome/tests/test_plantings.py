"""Plantings: a plant row that can stand for more than one physical plant.

A houseplant owner names individuals; a gardener counts. These tests pin the
three things that keeps honest: quantity defaults so existing rows mean exactly
what they always did, bulk import is all-or-nothing, and splitting conserves
the total rather than inventing plants the census would double-count.
"""
import pytest
from sqlmodel import Session, create_engine, select

from app.models.models import Environment, EnvironmentType, Plant, Species, User
from app.services import tokens


@pytest.fixture()
def garden(migrated_db_url):
    """One user with an environment and an API client."""
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
        species = s.exec(
            select(Species).where(Species.common_name == "Garden Tomato")
        ).first()
        if species is None:
            species = Species(
                common_name="Garden Tomato", scientific_name="Solanum testus",
                light_need="direct", humidity_pct_min=40, humidity_pct_max=70,
                temp_f_min=55, temp_f_max=90, soil_type="loam",
            )
            s.add(species)
            s.flush()
        species_id = species.id

        user = User(email="gardener@example.com")
        s.add(user)
        s.flush()
        env = Environment(
            name="Vegetable garden", type=EnvironmentType.home, user_id=user.id)
        s.add(env)
        s.flush()
        env_id, user_id = env.id, user.id
        s.commit()

    class G:
        def __init__(self):
            self.client = client
            self.engine = engine
            self.species_id = species_id
            self.env_id = env_id
            self.user_id = user_id
            self.headers = {
                "Authorization": f"Bearer {tokens.issue_access_token(user_id)}"}

        def db(self):
            return Session(self.engine)

    yield G()
    app.dependency_overrides.clear()
    engine.dispose()


# --- quantity defaults --------------------------------------------------------


def test_a_plant_created_without_quantity_is_an_individual(garden):
    """The pre-existing meaning of a row. Everything already in the database
    predates this column and must keep meaning exactly one physical plant."""
    r = garden.client.post("/plants/", headers=garden.headers, json={
        "nickname": "Bernie", "species_id": garden.species_id,
        "environment_id": garden.env_id,
    })
    assert r.status_code == 201
    body = r.json()
    assert body["quantity"] == 1
    assert body["split_from_uuid"] is None


def test_a_planting_carries_its_count(garden):
    r = garden.client.post("/plants/", headers=garden.headers, json={
        "species_id": garden.species_id, "quantity": 12,
        "location": "south fence", "environment_id": garden.env_id,
    })
    assert r.status_code == 201
    assert r.json()["quantity"] == 12


def test_quantity_must_be_at_least_one(garden):
    r = garden.client.post("/plants/", headers=garden.headers, json={
        "species_id": garden.species_id, "quantity": 0,
        "environment_id": garden.env_id,
    })
    assert r.status_code == 422


# --- generated nicknames ------------------------------------------------------


def test_a_planting_with_no_nickname_borrows_species_and_place(garden):
    """Notification bodies, to-do rows and both LLM prompts address a plant by
    name, so a blank would render as a hole in a sentence."""
    r = garden.client.post("/plants/", headers=garden.headers, json={
        "species_id": garden.species_id, "quantity": 12,
        "location": "south fence", "environment_id": garden.env_id,
    })
    assert r.json()["nickname"] == "Garden Tomato — south fence"


def test_a_nickname_free_plant_with_no_place_uses_the_species_alone(garden):
    r = garden.client.post("/plants/", headers=garden.headers, json={
        "species_id": garden.species_id, "environment_id": garden.env_id,
    })
    assert r.json()["nickname"] == "Garden Tomato"


def test_a_supplied_nickname_always_wins(garden):
    r = garden.client.post("/plants/", headers=garden.headers, json={
        "nickname": "Bernie", "species_id": garden.species_id,
        "location": "south fence", "environment_id": garden.env_id,
    })
    assert r.json()["nickname"] == "Bernie"


# --- bulk import --------------------------------------------------------------


def test_bulk_creates_every_plant_in_one_call(garden):
    r = garden.client.post("/plants/bulk", headers=garden.headers, json={
        "plants": [
            {"species_id": garden.species_id, "quantity": 12,
             "location": "south fence", "environment_id": garden.env_id},
            {"species_id": garden.species_id, "quantity": 3,
             "location": "by the gate", "environment_id": garden.env_id},
        ]
    })
    assert r.status_code == 201
    body = r.json()
    assert body["created"] == 2
    assert [p["quantity"] for p in body["plants"]] == [12, 3]
    assert body["plants"][0]["nickname"] == "Garden Tomato — south fence"


def test_a_bad_species_rolls_the_whole_batch_back(garden):
    """All-or-nothing. A partially imported garden is worse than none: the user
    cannot tell which half landed, and re-running would duplicate it."""
    before = len(garden.client.get("/plants/", headers=garden.headers).json())

    r = garden.client.post("/plants/bulk", headers=garden.headers, json={
        "plants": [
            {"species_id": garden.species_id, "quantity": 12,
             "environment_id": garden.env_id},
            {"species_id": 999_999, "quantity": 3,
             "environment_id": garden.env_id},
        ]
    })
    assert r.status_code == 400

    after = garden.client.get("/plants/", headers=garden.headers).json()
    assert len(after) == before, "the valid first plant must not have survived"


def test_bulk_rejects_an_unbounded_batch(garden):
    r = garden.client.post("/plants/bulk", headers=garden.headers, json={
        "plants": [
            {"species_id": garden.species_id, "environment_id": garden.env_id}
        ] * 201
    })
    assert r.status_code == 422


def test_bulk_will_not_plant_into_someone_elses_environment(garden):
    """Ownership is checked per entry, not just on the batch."""
    with garden.db() as s:
        stranger = User(email="stranger@example.com")
        s.add(stranger)
        s.flush()
        their_env = Environment(
            name="not yours", type=EnvironmentType.home, user_id=stranger.id)
        s.add(their_env)
        s.commit()
        their_env_id = their_env.id

    r = garden.client.post("/plants/bulk", headers=garden.headers, json={
        "plants": [
            {"species_id": garden.species_id, "environment_id": their_env_id}
        ]
    })
    assert r.status_code == 404  # not 403 — no id probing


# --- splitting ----------------------------------------------------------------


def test_splitting_conserves_the_total_and_records_the_origin(garden):
    created = garden.client.post("/plants/", headers=garden.headers, json={
        "species_id": garden.species_id, "quantity": 12,
        "location": "south fence", "environment_id": garden.env_id,
    }).json()

    r = garden.client.post(
        f"/plants/{created['id']}/split", headers=garden.headers,
        json={"quantity": 3, "location": "far bed"},
    )
    assert r.status_code == 201
    offshoot = r.json()

    assert offshoot["quantity"] == 3
    assert offshoot["location"] == "far bed"
    # The link that lets an aggregator see these two rows as one planting
    # rather than as fifteen tomatoes.
    assert offshoot["split_from_uuid"] == created["plant_uuid"]
    assert offshoot["plant_uuid"] != created["plant_uuid"]

    remaining = garden.client.get(
        f"/plants/{created['id']}", headers=garden.headers).json()
    assert remaining["quantity"] == 9
    assert remaining["quantity"] + offshoot["quantity"] == 12


def test_splitting_the_whole_planting_is_refused(garden):
    """That is a transfer — it must preserve plant_uuid, not replace it."""
    created = garden.client.post("/plants/", headers=garden.headers, json={
        "species_id": garden.species_id, "quantity": 5,
        "environment_id": garden.env_id,
    }).json()

    r = garden.client.post(
        f"/plants/{created['id']}/split", headers=garden.headers,
        json={"quantity": 5},
    )
    assert r.status_code == 400
    assert "transfer" in r.json()["detail"].lower()


# --- census counting ----------------------------------------------------------


def test_summary_counts_plants_not_rows(garden):
    """The distinction the census turns on: twelve tomatoes are twelve plants
    but one thing to tend."""
    garden.client.post("/plants/bulk", headers=garden.headers, json={
        "plants": [
            {"species_id": garden.species_id, "quantity": 12,
             "environment_id": garden.env_id},
            {"species_id": garden.species_id, "quantity": 3,
             "environment_id": garden.env_id},
        ]
    })
    body = garden.client.get("/census/summary", headers=garden.headers).json()

    assert body["total_plants"] == 15
    assert body["total_plantings"] == 2
    assert body["species_distribution"][0]["count"] == 15


def test_export_carries_quantity_and_split_lineage(garden):
    """An aggregator has to be able to tell a bed from a windowsill, and to
    recognise a split as a rearrangement rather than new plants appearing."""
    with garden.db() as s:
        user = s.get(User, garden.user_id)
        user.census_opt_in = True
        s.add(user)
        s.commit()

    created = garden.client.post("/plants/", headers=garden.headers, json={
        "species_id": garden.species_id, "quantity": 12,
        "environment_id": garden.env_id,
    }).json()
    garden.client.post(
        f"/plants/{created['id']}/split", headers=garden.headers,
        json={"quantity": 3},
    )

    body = garden.client.get("/census/export", headers=garden.headers).json()
    mine = [p for p in body["plants"]
            if p["plant_uuid"] == created["plant_uuid"]
            or p["split_from_uuid"] == created["plant_uuid"]]
    assert len(mine) == 2

    # The split conserved the total: 9 + 3, not 12 + 3.
    assert sum(p["quantity"] for p in mine) == 12
    offshoot = next(p for p in mine if p["split_from_uuid"])
    assert offshoot["split_from_uuid"] == created["plant_uuid"]
    assert body["export_version"] == "2.1"


def test_cannot_split_someone_elses_planting(garden):
    with garden.db() as s:
        stranger = User(email="stranger2@example.com")
        s.add(stranger)
        s.flush()
        theirs = Plant(
            nickname="theirs", species_id=garden.species_id,
            quantity=10, user_id=stranger.id)
        s.add(theirs)
        s.commit()
        theirs_id = theirs.id

    r = garden.client.post(
        f"/plants/{theirs_id}/split", headers=garden.headers,
        json={"quantity": 2},
    )
    assert r.status_code == 404
