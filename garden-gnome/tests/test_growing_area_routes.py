"""Growing areas answer on both paths while the old build is still out there.

0017 renamed the concept, and the shipped TestFlight app calls `/environments`.
The rename is not allowed to brick an app already installed on someone's
phone, so the same handlers are mounted twice and the old prefix is marked
deprecated in the schema rather than deleted. These tests are what says when
it is safe to delete it: when they are the only thing still asking for it.
"""
from tests.test_scoping import iso  # noqa: F401  (fixture: two users, one area each)

NEW = "/growing-areas"
OLD = "/environments"


def test_both_prefixes_answer_with_the_same_area(iso):  # noqa: F811
    new = iso.client.get(f"{NEW}/{iso.a['env_id']}", headers=iso.a["headers"])
    old = iso.client.get(f"{OLD}/{iso.a['env_id']}", headers=iso.a["headers"])
    assert new.status_code == 200 and old.status_code == 200
    assert new.json() == old.json()


def test_the_old_prefix_is_still_scoped_to_its_owner(iso):  # noqa: F811
    """A deprecated path is not a back door: B's area is a 404 on both."""
    for prefix in (NEW, OLD):
        assert iso.client.get(
            f"{prefix}/{iso.b['env_id']}", headers=iso.a["headers"]
        ).status_code == 404


def test_the_old_prefix_still_requires_a_token(iso):  # noqa: F811
    assert iso.client.get(f"{OLD}/{iso.a['env_id']}").status_code == 401


def test_a_write_through_the_old_prefix_is_read_back_through_the_new(iso):  # noqa: F811
    created = iso.client.post(
        f"{OLD}/", headers=iso.a["headers"],
        json={"name": "Old path bed", "type": "balcony"})
    assert created.status_code == 201
    area_id = created.json()["id"]

    read = iso.client.get(f"{NEW}/{area_id}", headers=iso.a["headers"])
    assert read.status_code == 200
    assert read.json()["name"] == "Old path bed"


def test_real_estate_round_trips_through_create_and_read(iso):  # noqa: F811
    created = iso.client.post(
        f"{NEW}/", headers=iso.a["headers"],
        json={
            "name": "Back bed", "type": "community_garden",
            "shelter": "exposed", "temp_exposure": "outdoor",
            "sun_exposure": "full_sun",
            "surface": "raised_bed", "area_sqft": 32, "headroom_in": 84,
            "soil_depth_in": 12, "goals": ["edible", "pollinators"],
        })
    assert created.status_code == 201, created.text

    body = iso.client.get(
        f"{NEW}/{created.json()['id']}", headers=iso.a["headers"]).json()
    assert body["surface"] == "raised_bed"
    assert body["area_sqft"] == 32 and body["headroom_in"] == 84
    assert body["soil_depth_in"] == 12
    assert body["goals"] == ["edible", "pollinators"]


def test_an_area_created_without_measurements_reports_none_not_zero(iso):  # noqa: F811
    """The distinction the whole fit engine rests on: unmeasured is not 0."""
    created = iso.client.post(
        f"{NEW}/", headers=iso.a["headers"], json={"name": "Unmeasured"})
    body = created.json()
    for field in ("surface", "area_sqft", "headroom_in", "soil_depth_in", "goals"):
        assert body[field] is None, f"{field} came back {body[field]!r}"


def test_goals_can_be_asked_and_answered_with_nothing(iso):  # noqa: F811
    created = iso.client.post(
        f"{NEW}/", headers=iso.a["headers"],
        json={"name": "No goals in particular", "goals": []})
    assert created.json()["goals"] == []


def test_measurements_can_be_added_later_by_patch(iso):  # noqa: F811
    """Areas made before the feature existed get filled in, not replaced."""
    patched = iso.client.patch(
        f"{NEW}/{iso.a['env_id']}", headers=iso.a["headers"],
        json={"surface": "windowsill", "headroom_in": 18, "goals": ["low_upkeep"]})
    assert patched.status_code == 200, patched.text
    body = patched.json()
    assert body["surface"] == "windowsill" and body["headroom_in"] == 18
    assert body["goals"] == ["low_upkeep"]
    # Untouched measurements stay unanswered rather than being zeroed.
    assert body["area_sqft"] is None and body["soil_depth_in"] is None


def test_an_unknown_surface_is_rejected(iso):  # noqa: F811
    assert iso.client.post(
        f"{NEW}/", headers=iso.a["headers"],
        json={"name": "Nope", "surface": "hydroponic_tower"}
    ).status_code == 422


def test_the_old_prefix_is_marked_deprecated_and_the_new_one_is_not(iso):  # noqa: F811
    """The schema is where a client author finds out which path to build on."""
    paths = iso.client.get("/openapi.json").json()["paths"]
    assert paths[f"{OLD}/"]["get"]["deprecated"] is True
    assert paths[f"{NEW}/"]["get"].get("deprecated") is not True
