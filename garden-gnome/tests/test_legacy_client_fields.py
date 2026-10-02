"""The TestFlight 1.1.2 app, replayed against the renamed API.

PR #20 renamed Environment to GrowingArea, and the build testers have
installed (a5d0d07) predates it. Every request below is shaped exactly as that
build sends it, and every assertion reads what that build reads, so the
pre-rename shim in app/models/schemas.py and the `/environments` alias are
held to the old app itself rather than to a guess about it. These tests go
when `legacy_router` goes; until then they are the list of what removing it
would break. The last two pin the new client's shapes, which the shim must
leave alone.
"""
from app.models.models import Plant
from app.services import weather
from tests.test_scoping import iso  # noqa: F401  (fixture: two users, one area each)
from tests.test_weather import SAMPLE_WEATHERKIT

OLD = "/environments"

# Every key 1.1.2's `Environment` type declares (mobile/src/types/index.ts).
OLD_AREA_KEYS = {
    "id", "uuid", "name", "type", "city", "region", "country", "lat", "lng",
    "shelter", "temp_exposure", "sun_exposure", "created_at", "plant_count",
}


def _old_area(iso, name="Back porch"):  # noqa: F811
    """An area for A made the way 1.1.2's Environments screen makes one. A
    plant sent here cannot pass by falling back to A's default, which is the
    fixture's older a-home."""
    r = iso.client.post(f"{OLD}/", headers=iso.a["headers"], json={
        "name": name, "type": "home", "city": "", "region": "", "country": "",
        "shelter": "partial", "temp_exposure": "outdoor",
        "sun_exposure": "partial_sun",
    })
    assert r.status_code == 201, r.text
    area_id = r.json()["id"]
    assert area_id != iso.a["env_id"]
    return area_id


def _old_add_plant(iso, area_id, nickname="Porch fern"):  # noqa: F811
    """AddPlantScreen's createPlant body."""
    r = iso.client.post("/plants/", headers=iso.a["headers"], json={
        "nickname": nickname, "species_id": iso.species_id, "quantity": 1,
        "environment_id": area_id, "location": "by the door",
        "intake_notes": "",
    })
    assert r.status_code == 201, r.text
    return r.json()


# --- What the old app sends -----------------------------------------------------


def test_add_plant_with_environment_id_lands_in_that_area(iso):  # noqa: F811
    porch = _old_area(iso)
    body = _old_add_plant(iso, porch)

    assert body["growing_area_id"] == porch
    with iso.db() as s:
        assert s.get(Plant, body["id"]).growing_area_id == porch


def test_capture_garden_bulk_with_environment_id_lands_in_that_area(iso):  # noqa: F811
    """CaptureGardenScreen's createPlantsBulk body."""
    porch = _old_area(iso)
    r = iso.client.post("/plants/bulk", headers=iso.a["headers"], json={
        "plants": [
            {"species_id": iso.species_id, "quantity": 12,
             "location": "south fence", "environment_id": porch},
            {"species_id": iso.species_id, "quantity": 3,
             "location": "", "environment_id": porch},
        ]})
    assert r.status_code == 201, r.text

    plants = r.json()["plants"]
    assert [p["growing_area_id"] for p in plants] == [porch, porch]
    assert [p["environment_id"] for p in plants] == [porch, porch]


def test_move_plant_with_to_environment_id_moves_it(iso):  # noqa: F811
    """PlantDetailScreen's transferPlant body. Without the alias this is a
    422, because the new name is required."""
    porch = _old_area(iso)
    r = iso.client.post(
        f"/plants/{iso.a['plant_id']}/transfer", headers=iso.a["headers"],
        json={"to_environment_id": porch, "transfer_notes": ""})
    assert r.status_code == 200, r.text
    assert r.json()["growing_area_id"] == porch
    assert r.json()["environment_id"] == porch
    with iso.db() as s:
        assert s.get(Plant, iso.a["plant_id"]).growing_area_id == porch


def test_the_old_move_is_still_scoped_to_its_owner(iso):  # noqa: F811
    """An accepted old name is not a back door into B's area."""
    r = iso.client.post(
        f"/plants/{iso.a['plant_id']}/transfer", headers=iso.a["headers"],
        json={"to_environment_id": iso.b["env_id"], "transfer_notes": ""})
    assert r.status_code == 404
    with iso.db() as s:
        assert s.get(Plant, iso.a["plant_id"]).growing_area_id == iso.a["env_id"]


def test_a_move_that_names_no_area_is_still_refused(iso):  # noqa: F811
    """The alias widens what the field is called, not whether it is needed."""
    r = iso.client.post(
        f"/plants/{iso.a['plant_id']}/transfer", headers=iso.a["headers"],
        json={"transfer_notes": ""})
    assert r.status_code == 422


def test_the_new_name_wins_when_both_are_sent(iso):  # noqa: F811
    porch, shed = _old_area(iso, "Porch"), _old_area(iso, "Shed")

    created = iso.client.post("/plants/", headers=iso.a["headers"], json={
        "species_id": iso.species_id,
        "growing_area_id": porch, "environment_id": shed})
    assert created.status_code == 201, created.text
    assert created.json()["growing_area_id"] == porch

    moved = iso.client.post(
        f"/plants/{created.json()['id']}/transfer", headers=iso.a["headers"],
        json={"to_growing_area_id": shed, "to_environment_id": porch})
    assert moved.status_code == 200, moved.text
    assert moved.json()["growing_area_id"] == shed


def test_split_accepts_to_environment_id(iso):  # noqa: F811
    """1.1.2 never splits, but the field was renamed with the rest, and a
    half-aliased API would send three tomatoes to the wrong bed silently."""
    porch = _old_area(iso)
    planting = iso.client.post("/plants/", headers=iso.a["headers"], json={
        "species_id": iso.species_id, "quantity": 12}).json()

    r = iso.client.post(
        f"/plants/{planting['id']}/split", headers=iso.a["headers"],
        json={"quantity": 3, "to_environment_id": porch})
    assert r.status_code == 201, r.text
    assert r.json()["growing_area_id"] == porch
    assert r.json()["environment_id"] == porch


# --- What the old app reads -----------------------------------------------------


def test_one_plant_and_the_list_carry_both_names(iso):  # noqa: F811
    one = iso.client.get(
        f"/plants/{iso.a['plant_id']}", headers=iso.a["headers"]).json()
    assert one["environment_id"] == one["growing_area_id"] == iso.a["env_id"]

    listed = iso.client.get("/plants/", headers=iso.a["headers"]).json()
    assert listed
    for plant in listed:
        assert plant["environment_id"] == plant["growing_area_id"]


def test_per_area_care_grouping_finds_each_areas_plants(iso):  # noqa: F811
    """useCareTasks, the weather nudge and the reminder planner all group by
    `plant.environment_id === env.id`. Without the field every area's group is
    empty, which is how a screen full of plants says "No care scheduled"."""
    porch = _old_area(iso)
    _old_add_plant(iso, porch)

    areas = iso.client.get(f"{OLD}/", headers=iso.a["headers"]).json()
    plants = iso.client.get("/plants/", headers=iso.a["headers"]).json()
    assert {a["id"] for a in areas} == {iso.a["env_id"], porch}
    for area in areas:
        grouped = [p for p in plants if p.get("environment_id") == area["id"]]
        assert len(grouped) == area["plant_count"] == 1, area["name"]


def test_stewardship_records_carry_environment_id(iso):  # noqa: F811
    """1.1.2's StewardshipRecord declares `environment_id: number`, required."""
    porch, shed = _old_area(iso, "Porch"), _old_area(iso, "Shed")
    plant = _old_add_plant(iso, porch)
    iso.client.post(
        f"/plants/{plant['id']}/transfer", headers=iso.a["headers"],
        json={"to_environment_id": shed, "transfer_notes": "more light"})

    r = iso.client.get(
        f"/plants/{plant['id']}/stewardship", headers=iso.a["headers"])
    assert r.status_code == 200, r.text
    records = r.json()
    assert [rec["environment_id"] for rec in records] == [porch, shed]
    assert [rec["growing_area_id"] for rec in records] == [porch, shed]


def test_census_summary_carries_the_old_keys(iso):  # noqa: F811
    """CensusScreen renders `Object.entries(summary.environments_by_type)`,
    which throws on a missing key and takes the screen down with it."""
    body = iso.client.get("/census/summary", headers=iso.a["headers"]).json()

    assert body["total_environments"] == body["total_growing_areas"] == 1
    assert body["environments_by_type"] == body["growing_areas_by_type"] == {
        "home": 1}
    assert (body["plants_by_environment_type"]
            == body["plants_by_growing_area_type"] == {"home": 1})


def test_the_old_area_routes_answer_with_the_old_shape(iso):  # noqa: F811
    """fetchEnvironments, fetchEnvironment, createEnvironment and the
    location patch, as 1.1.2 calls them."""
    headers = iso.a["headers"]
    porch = _old_area(iso)

    listed = iso.client.get(f"{OLD}/", headers=headers)
    assert listed.status_code == 200
    for area in listed.json():
        assert OLD_AREA_KEYS <= set(area), area["name"]

    patched = iso.client.patch(f"{OLD}/{porch}", headers=headers, json={
        "city": "Baltimore", "region": "Maryland", "country": "United States",
        "lat": 39.29, "lng": -76.61})
    assert patched.status_code == 200, patched.text

    one = iso.client.get(f"{OLD}/{porch}", headers=headers)
    assert one.status_code == 200
    assert OLD_AREA_KEYS <= set(one.json())
    assert one.json()["city"] == "Baltimore" and one.json()["lat"] == 39.29


def test_the_old_weather_route_answers_with_the_old_shape(iso, monkeypatch):  # noqa: F811
    headers = iso.a["headers"]
    porch = _old_area(iso)

    unlocated = iso.client.get(f"{OLD}/{porch}/weather", headers=headers)
    assert unlocated.status_code == 200
    assert unlocated.json()["available"] is False
    assert unlocated.json()["weather"] is None

    async def fake_fetch(lat, lng, lang="en"):
        return weather.normalize(SAMPLE_WEATHERKIT)

    monkeypatch.setattr("app.routers.growing_areas.fetch_weather", fake_fetch)
    iso.client.patch(f"{OLD}/{porch}", headers=headers, json={
        "city": "Baltimore", "region": "Maryland", "country": "United States",
        "lat": 39.29, "lng": -76.61})
    located = iso.client.get(f"{OLD}/{porch}/weather", headers=headers)
    assert located.status_code == 200
    body = located.json()
    assert body["available"] is True
    assert {"current", "daily", "attribution"} <= set(body["weather"])


# --- What the new client sends and reads, unchanged -----------------------------


def test_the_new_clients_shapes_still_work(iso):  # noqa: F811
    headers = iso.a["headers"]
    bed = iso.client.post("/growing-areas/", headers=headers,
                          json={"name": "Raised bed", "type": "balcony"})
    assert bed.status_code == 201, bed.text
    bed_id = bed.json()["id"]

    created = iso.client.post("/plants/", headers=headers, json={
        "species_id": iso.species_id, "growing_area_id": bed_id})
    assert created.status_code == 201, created.text
    assert created.json()["growing_area_id"] == bed_id

    moved = iso.client.post(
        f"/plants/{created.json()['id']}/transfer", headers=headers,
        json={"to_growing_area_id": iso.a["env_id"], "transfer_notes": ""})
    assert moved.status_code == 200, moved.text
    assert moved.json()["growing_area_id"] == iso.a["env_id"]

    one = iso.client.get(f"/plants/{created.json()['id']}", headers=headers)
    assert one.json()["growing_area_id"] == iso.a["env_id"]

    summary = iso.client.get("/census/summary", headers=headers).json()
    assert summary["total_growing_areas"] == 2
    assert summary["growing_areas_by_type"] == {"home": 1, "balcony": 1}


def test_the_schema_documents_only_the_new_names(iso):  # noqa: F811
    """A request schema names only the canonical field, so nobody builds a
    new client against the old one, and a response's copy says it is going."""
    schemas = iso.client.get("/openapi.json").json()["components"]["schemas"]

    for name, field in (("PlantCreate", "growing_area_id"),
                        ("PlantTransferRequest", "to_growing_area_id"),
                        ("PlantSplitRequest", "to_growing_area_id")):
        props = schemas[name]["properties"]
        assert field in props, name
        assert not [p for p in props if "environment" in p], name
    assert schemas["PlantTransferRequest"]["required"] == ["to_growing_area_id"]

    for name in ("PlantRead", "StewardshipRecordRead"):
        props = schemas[name]["properties"]
        assert "growing_area_id" in props
        assert props["environment_id"]["deprecated"] is True
        assert "TestFlight 1.1.2" in props["environment_id"]["description"]
