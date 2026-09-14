"""The two fit endpoints, against a real database and a real client.

`test_fit` covers the rules; this covers the wiring — that the right plants
and species are fetched, that another account's area is invisible, and that
the answers survive serialisation with their sentences intact.
"""
import pytest
from sqlmodel import Session, create_engine, select

from app.models.models import (
    GrowingArea, GrowingAreaType, GrowingGoal, GrowingSurface, Plant, Species,
    Shelter, SunExposure, TempExposure, User,
)
from app.services import tokens


@pytest.fixture()
def garden(migrated_db_url):
    """One user with a sunny outdoor bed, and a catalog with something in it."""
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
        # A small, deliberately-shaped catalog: one that belongs in a sunny
        # bed, one that cannot be there, and one nobody has researched.
        made = {}
        for key, kw in {
            "coneflower": dict(
                common_name="Purple Coneflower",
                scientific_name="Echinacea purpurea",
                is_houseplant=False, outdoor_sun_exposure=["full_sun"],
                soil_base="garden_bed", attracts_pollinators=True,
                water_regime="dry_thoroughly_between"),
            "hosta": dict(
                common_name="Hosta", scientific_name="Hosta sieboldiana",
                is_houseplant=False, outdoor_sun_exposure=["full_shade"],
                soil_base="garden_bed"),
            "mystery": dict(
                common_name="Unresearched Thing",
                scientific_name="Ignotus ignotus"),
        }.items():
            row = s.exec(select(Species).where(
                Species.scientific_name == kw["scientific_name"])).first()
            if row is None:
                row = Species(**kw)
                s.add(row)
                s.flush()
            made[key] = row.id

        user = User(email="fit@example.com")
        other = User(email="other@example.com")
        s.add(user); s.add(other); s.flush()

        bed = GrowingArea(
            name="Back bed", type=GrowingAreaType.community_garden,
            user_id=user.id, shelter=Shelter.exposed,
            temp_exposure=TempExposure.outdoor, sun_exposure=SunExposure.full_sun,
            surface=GrowingSurface.raised_bed, area_sqft=32, headroom_in=84,
            goals=[GrowingGoal.pollinators.value])
        theirs = GrowingArea(
            name="Their bed", type=GrowingAreaType.home, user_id=other.id)
        s.add(bed); s.add(theirs); s.flush()

        # A hosta standing in full sun: the case the misfit card exists for.
        s.add(Plant(nickname="Big Hosta", species_id=made["hosta"],
                    growing_area_id=bed.id, user_id=user.id))
        s.add(Plant(nickname="Echie", species_id=made["coneflower"],
                    growing_area_id=bed.id, user_id=user.id))
        s.commit()

        data = dict(
            bed_id=bed.id, their_bed_id=theirs.id, user_id=user.id,
            species=made,
            headers={"Authorization": f"Bearer {tokens.issue_access_token(user.id)}"},
        )

    class G:
        def __init__(self):
            self.client = client
            self.__dict__.update(data)

    yield G()
    app.dependency_overrides.clear()
    engine.dispose()


BASE = "/growing-areas"


# --- candidates ------------------------------------------------------------

def test_a_sunny_bed_gets_the_sun_lover_and_not_the_shade_one(garden):
    body = garden.client.get(
        f"{BASE}/{garden.bed_id}/candidates", headers=garden.headers).json()
    names = [c["common_name"] for c in body]
    assert "Purple Coneflower" in names
    assert "Hosta" not in names, "a full-shade plant is not a candidate for full sun"


def test_an_unresearched_species_is_never_put_forward(garden):
    body = garden.client.get(
        f"{BASE}/{garden.bed_id}/candidates", headers=garden.headers).json()
    assert "Unresearched Thing" not in [c["common_name"] for c in body]


def test_every_candidate_says_why_and_only_confirmed_reasons_count(garden):
    body = garden.client.get(
        f"{BASE}/{garden.bed_id}/candidates", headers=garden.headers).json()
    echinacea = next(c for c in body if c["common_name"] == "Purple Coneflower")
    assert echinacea["score"] == len(echinacea["fits"]) > 0
    assert all(f["verdict"] == "fits" for f in echinacea["fits"])
    assert all(f["sentence"] for f in echinacea["fits"])


def test_candidates_are_ranked_by_confirmed_evidence(garden):
    body = garden.client.get(
        f"{BASE}/{garden.bed_id}/candidates", headers=garden.headers).json()
    scores = [c["score"] for c in body]
    assert scores == sorted(scores, reverse=True)


def test_limit_is_honoured(garden):
    body = garden.client.get(
        f"{BASE}/{garden.bed_id}/candidates?limit=1", headers=garden.headers).json()
    assert len(body) <= 1


# --- misfits ---------------------------------------------------------------

def test_the_shade_plant_in_the_sun_is_what_needs_addressing(garden):
    body = garden.client.get(
        f"{BASE}/{garden.bed_id}/misfits", headers=garden.headers).json()
    assert [m["nickname"] for m in body] == ["Big Hosta"]
    reasons = body[0]["misfits"]
    assert any(r["axis"] == "sun" for r in reasons)
    assert all(r["verdict"] == "misfits" for r in reasons)


def test_the_misfit_names_the_specific_problem_not_just_a_verdict(garden):
    body = garden.client.get(
        f"{BASE}/{garden.bed_id}/misfits", headers=garden.headers).json()
    sun = next(r for r in body[0]["misfits"] if r["axis"] == "sun")
    assert "6+ hours of direct sun" in sun["sentence"]
    assert "full shade" in sun["sentence"]


def test_a_plant_that_suits_the_space_is_absent_from_the_list(garden):
    body = garden.client.get(
        f"{BASE}/{garden.bed_id}/misfits", headers=garden.headers).json()
    assert "Echie" not in [m["nickname"] for m in body]


# --- scoping ---------------------------------------------------------------

@pytest.mark.parametrize("suffix", ["candidates", "misfits"])
def test_another_accounts_area_is_a_404_on_both(garden, suffix):
    assert garden.client.get(
        f"{BASE}/{garden.their_bed_id}/{suffix}", headers=garden.headers
    ).status_code == 404


@pytest.mark.parametrize("suffix", ["candidates", "misfits"])
def test_both_require_a_token(garden, suffix):
    assert garden.client.get(
        f"{BASE}/{garden.bed_id}/{suffix}").status_code == 401


# --- the plants filter the misfit endpoint needed --------------------------

def test_plants_can_be_filtered_to_one_area_server_side(garden):
    all_plants = garden.client.get("/plants/", headers=garden.headers).json()
    in_bed = garden.client.get(
        f"/plants/?growing_area_id={garden.bed_id}", headers=garden.headers).json()
    assert {p["nickname"] for p in in_bed} == {"Big Hosta", "Echie"}
    assert len(in_bed) <= len(all_plants)


def test_filtering_by_someone_elses_area_returns_nothing_rather_than_theirs(garden):
    body = garden.client.get(
        f"/plants/?growing_area_id={garden.their_bed_id}", headers=garden.headers).json()
    assert body == []
