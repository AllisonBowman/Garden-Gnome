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
            # Cited for its sun range, borrowed from the genus for its soil:
            # the two ways a finding says where it came from. Never planted,
            # and a sun misfit in the bed, so it is on no list by default.
            "attributed": dict(
                common_name="Attributed Fern", scientific_name="Umbra testae",
                outdoor_sun_exposure=["part_shade", "full_shade"],
                soil_base="garden_bed",
                care_provenance={"outdoor_sun_exposure": "sourced",
                                 "soil_base": "genus_inferred"},
                care_sources=[
                    {"authority": "NC State Extension",
                     "url": "https://plants.ces.ncsu.edu/umbra",
                     "fields": ["outdoor_sun_exposure"], "inferred": False},
                    {"authority": "Royal Horticultural Society",
                     "url": "https://www.rhs.org.uk/umbra",
                     "fields": ["soil_base"], "inferred": True},
                ]),
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


def test_the_count_before_the_cut_travels_with_the_cut_list(garden):
    """A screen showing the first twelve has to be able to say "12 of 263".
    The body stays the bare list every installed build parses; the whole
    count rides in a header, whatever the limit cut it to."""
    every = garden.client.get(
        f"{BASE}/{garden.bed_id}/candidates?limit=100000", headers=garden.headers)
    cut = garden.client.get(
        f"{BASE}/{garden.bed_id}/candidates?limit=0", headers=garden.headers)
    assert cut.status_code == 200, cut.text
    assert cut.json() == []
    total = len(every.json())
    assert total >= 1, "the coneflower belongs in this bed"
    assert cut.headers["X-Total-Count"] == str(total)
    assert every.headers["X-Total-Count"] == str(total)


def test_a_negative_limit_is_refused_rather_than_dropping_the_last_candidate(garden):
    resp = garden.client.get(
        f"{BASE}/{garden.bed_id}/candidates?limit=-1", headers=garden.headers)
    assert resp.status_code == 422


def test_the_web_preview_is_allowed_to_read_the_count(garden):
    """A browser hides a response header CORS doesn't expose, and the web
    preview runs in one."""
    resp = garden.client.get(
        f"{BASE}/{garden.bed_id}/candidates?limit=1",
        headers={**garden.headers, "Origin": "http://localhost:8081"})
    exposed = resp.headers.get("access-control-expose-headers", "")
    assert "x-total-count" in exposed.lower()


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


# --- one species, before it is planted ------------------------------------
# What Add Plant asks. The misfit list only speaks for plants already in the
# area and the candidate list only for species that cleared it, so neither
# could say what a spot has against the plant someone is about to put in it.

def _fit(garden, key):
    return garden.client.get(
        f"{BASE}/{garden.bed_id}/fit/{garden.species[key]}", headers=garden.headers)


def test_the_misfit_is_known_before_the_plant_goes_in(garden):
    resp = _fit(garden, "hosta")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["common_name"] == "Hosta"
    assert body["candidate"] is False
    sun = next(f for f in body["findings"] if f["axis"] == "sun")
    assert sun["verdict"] == "misfits"
    assert "6+ hours of direct sun" in sun["sentence"]


def test_every_axis_comes_back_unknowns_included(garden):
    """The client decides what to show, never what the verdict is -- so it
    gets the unknowns too, labelled as unknowns."""
    body = _fit(garden, "mystery").json()
    assert body["candidate"] is False and body["score"] == 0
    assert body["findings"], "every axis should still report"
    assert {f["verdict"] for f in body["findings"]} == {"unknown"}
    axes = [f["axis"] for f in body["findings"]]
    assert axes[:4] == ["indoor_outdoor", "sun", "soil", "footprint"]


def test_the_candidate_flag_agrees_with_the_candidate_list(garden):
    listed = {c["species_id"] for c in garden.client.get(
        f"{BASE}/{garden.bed_id}/candidates?limit=1000",
        headers=garden.headers).json()}
    for key in ("coneflower", "hosta", "mystery", "attributed"):
        body = _fit(garden, key).json()
        assert body["candidate"] == (garden.species[key] in listed), key


def test_a_finding_says_whose_word_it_is_and_what_was_borrowed(garden):
    body = _fit(garden, "attributed").json()
    sun = next(f for f in body["findings"] if f["axis"] == "sun")
    assert sun["verdict"] == "misfits"
    assert sun["authorities"] == ["NC State Extension"]
    assert sun["borrowed"] is False
    soil = next(f for f in body["findings"] if f["axis"] == "soil")
    assert soil["borrowed"] is True
    assert soil["authorities"] == [], "a genus page does not speak for the species"
    assert "from the genus" in soil["sentence"]


def test_a_goal_finding_says_which_goal_it_answers(garden):
    body = _fit(garden, "coneflower").json()
    goal = next(f for f in body["findings"] if f["axis"] == "goal")
    assert goal["goal"] == "pollinators"
    assert all(f["goal"] is None for f in body["findings"] if f["axis"] != "goal")


def test_an_unknown_species_is_a_404(garden):
    assert garden.client.get(
        f"{BASE}/{garden.bed_id}/fit/987654321", headers=garden.headers
    ).status_code == 404


# --- scoping ---------------------------------------------------------------

def _paths(garden, area_id):
    return [f"{BASE}/{area_id}/candidates", f"{BASE}/{area_id}/misfits",
            f"{BASE}/{area_id}/fit/{garden.species['hosta']}"]


def test_another_accounts_area_is_a_404_on_every_fit_endpoint(garden):
    for path in _paths(garden, garden.their_bed_id):
        assert garden.client.get(path, headers=garden.headers).status_code == 404, path


def test_every_fit_endpoint_requires_a_token(garden):
    for path in _paths(garden, garden.bed_id):
        assert garden.client.get(path).status_code == 401, path


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
