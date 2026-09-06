"""What the API says about a species now that the claim graph is wired in.

A row minted from the tranche has no legacy care values and no toxicity
record; a recomputed row has resolved values and the authorities that settled
them. Both routes must carry either without inventing a value or a verdict,
and without letting anything server-side out -- the quote, the researcher's
prose, the review trail (ADR 0003).
"""
import pytest
from sqlmodel import Session, create_engine

from app.data.claims.recompute import RESOLVED_FIELDS, SERVER_ONLY_FIELDS
from app.models.models import CareDataStatus, Species, SpeciesSource
from app.models.schemas import CareSourceRead, SpeciesDetail, SpeciesRead

NCSU = "https://plants.ces.ncsu.edu/plants/fuchsia-magellanica/"
LEGACY = ("light_need", "humidity_pct_min", "humidity_pct_max",
          "temp_f_min", "temp_f_max", "soil_type", "toxic_to_pets")
SERVER_ONLY = ("toxicity_detail", "water_dry_down_target",
               "water_estimate_basis", "cool_rest_note", "resolver_version",
               "review_status", "review_note", "source", "source_ref")


@pytest.fixture()
def api(migrated_db_url):
    from fastapi.testclient import TestClient

    from app.db.database import get_session
    from app.main import app
    from app.models.models import User
    from app.services import tokens

    engine = create_engine(
        migrated_db_url, connect_args={"check_same_thread": False})

    def override():
        with Session(engine) as s:
            yield s

    app.dependency_overrides[get_session] = override
    with Session(engine) as s:
        user = User(email="species-read@example.com")
        s.add(user)
        s.commit()
        headers = {
            "Authorization": f"Bearer {tokens.issue_access_token(user.id)}"}
    try:
        yield TestClient(app), headers, engine
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def minted(scientific_name, common_name, **over):
    fields = dict(common_name=common_name, scientific_name=scientific_name,
                  source=SpeciesSource.claims, source_ref="b1-test.json",
                  toxic_to_pets=None, care_notes="")
    fields.update(over)
    return Species(**fields)


def store(engine, *rows):
    with Session(engine) as s:
        for row in rows:
            s.add(row)
        s.commit()
        return [row.id for row in rows]


def test_bare_minted_row_serializes_on_both_routes(api):
    client, headers, engine = api
    (sid,) = store(engine, minted("Fuchsia readtest", "Readtest Fuchsia"))

    listed = {sp["id"]: sp for sp in
              client.get("/species/", headers=headers).json()}[sid]
    assert listed["common_name"] == "Readtest Fuchsia"
    # Absent values are absent keys on the list, not nulls to type around.
    for column in LEGACY:
        assert column not in listed, column
    assert listed["humidity_sourced"] is True
    assert listed["care_notes"] == ""

    resp = client.get(f"/species/{sid}", headers=headers)
    assert resp.status_code == 200
    detail = resp.json()
    for column in LEGACY:
        assert detail[column] is None, column
    assert detail["care_sources"] == []
    assert detail["care_data_status"] is None


def test_minted_row_toxicity_is_unknown_not_safe(api):
    client, headers, engine = api
    row = minted("Fuchsia toxtest", "Toxtest Fuchsia")
    assert "treat it as unknown rather than safe" in row.toxicity_description
    (sid,) = store(engine, row)

    detail = client.get(f"/species/{sid}", headers=headers).json()
    assert "treat it as unknown rather than safe" in detail["toxicity_description"]
    listed = {sp["id"]: sp for sp in
              client.get("/species/", headers=headers).json()}[sid]
    assert "treat it as unknown rather than safe" in listed["toxicity_description"]


def test_detail_carries_values_provenance_and_named_sources_only(api):
    client, headers, engine = api
    (sid,) = store(engine, minted(
        "Fuchsia sourcetest", "Sourcetest Fuchsia",
        water_regime="dry_surface_between", water_check_depth_cm=3.0,
        water_dry_down_target="verbatim passage from the page",
        chill_damage_f=45, light_fc_min=100,
        outdoor_sun_exposure=["part_sun", "part_shade"],
        fertilize_active_months=[3, 4, 5], hardiness_zones=[7, 8],
        toxicity_detail="researcher prose naming harm",
        cool_rest_note="researcher prose", water_estimate_basis="assumptions",
        care_data_status=CareDataStatus.sourced,
        care_provenance={"water_regime": "sourced",
                         "water_check_depth_cm": "sourced",
                         "light_fc_min": "sourced",
                         "chill_damage_f": "genus_inferred",
                         "toxicity_detail": "sourced",
                         "water_dry_down_target": "sourced"},
        care_sources=[
            {"authority": "NC State Extension", "url": NCSU,
             "fields": ["light_fc_min", "water_check_depth_cm", "water_regime"],
             "inferred": False},
            {"authority": "NC State Extension",
             "url": "https://plants.ces.ncsu.edu/plants/fuchsia/",
             "fields": ["chill_damage_f"], "inferred": True},
        ],
        resolver_version="2"))

    detail = client.get(f"/species/{sid}", headers=headers).json()
    assert detail["water_regime"] == "dry_surface_between"
    assert detail["water_check_depth_cm"] == 3.0
    assert detail["chill_damage_f"] == 45
    assert detail["outdoor_sun_exposure"] == ["part_sun", "part_shade"]
    assert detail["fertilize_active_months"] == [3, 4, 5]
    assert detail["hardiness_zones"] == [7, 8]
    assert detail["care_data_status"] == "sourced"
    # Provenance names only columns the client has: the server-only ones are
    # dropped rather than announced by name.
    assert detail["care_provenance"] == {
        "water_regime": "sourced", "water_check_depth_cm": "sourced",
        "light_fc_min": "sourced", "chill_damage_f": "genus_inferred"}
    assert detail["care_sources"] == [
        {"authority": "NC State Extension", "url": NCSU,
         "fields": ["light_fc_min", "water_check_depth_cm", "water_regime"],
         "inferred": False},
        {"authority": "NC State Extension",
         "url": "https://plants.ces.ncsu.edu/plants/fuchsia/",
         "fields": ["chill_damage_f"], "inferred": True},
    ]
    for key in SERVER_ONLY:
        assert key not in detail, key
    for banned in ("verbatim", "researcher prose", *SERVER_ONLY_FIELDS):
        assert banned not in resp_text(detail), banned

    listed = {sp["id"]: sp for sp in
              client.get("/species/", headers=headers).json()}[sid]
    assert listed["care_data_status"] == "sourced"
    assert listed["water_regime"] == "dry_surface_between"
    assert "care_sources" not in listed  # detail only
    assert "toxicity_detail" not in listed["care_provenance"]
    for key in SERVER_ONLY:
        assert key not in listed, key
    for banned in SERVER_ONLY_FIELDS:
        assert banned not in resp_text(listed), banned


def resp_text(payload) -> str:
    import json
    return json.dumps(payload)


def test_create_route_returns_a_fresh_row_without_sources(api):
    """POST /species/ answers with SpeciesDetail too; a row that has never
    been recomputed must not 500 on its null care_sources."""
    client, headers, _ = api
    resp = client.post("/species/", headers=headers, json={
        "common_name": "Createtest Fern", "scientific_name": "Testus createus",
        "light_need": "medium", "humidity_pct_min": 40, "humidity_pct_max": 60,
        "temp_f_min": 60, "temp_f_max": 80, "soil_type": "mix"})
    assert resp.status_code == 201, resp.text
    assert resp.json()["care_sources"] == []
    assert resp.json()["light_need"] == "medium"
    # An omitted flag is no record, not a verdict: null on the row, and the
    # sentence says unknown rather than safe.
    assert resp.json()["toxic_to_pets"] is None
    assert "unknown rather than safe" in resp.json()["toxicity_description"]


def test_a_cited_false_credits_the_authority_in_the_toxicity_sentence():
    """Rows hold a False an authority stated. The legacy wording, 'nothing
    harmful has been noted', is the catalog default's story, not theirs."""
    row = minted(
        "Toxicodendron radicans", "Poison Ivy", id=1, toxic_to_pets=False,
        care_provenance={"toxic_to_pets": "sourced"},
        care_sources=[{"authority": "UGA Cooperative Extension",
                       "url": "https://extension.uga.edu/",
                       "fields": ["toxic_to_pets"], "inferred": False}])
    assert row.toxicity_description.startswith(
        "UGA Cooperative Extension records no toxicity to pets for poison ivy")
    assert "unknown rather than safe" in minted(
        "Daphne odora", "Winter Daphne", id=2).toxicity_description


def test_provenance_that_names_only_server_side_columns_reads_as_absent():
    out = SpeciesRead.model_validate(minted(
        "Testus tectus", "Tectus", id=1,
        care_provenance={"toxicity_detail": "sourced"}))
    assert out.care_provenance is None


def test_read_schemas_carry_every_resolved_column_and_nothing_server_side():
    shipped = RESOLVED_FIELDS - SERVER_ONLY_FIELDS
    for schema in (SpeciesRead, SpeciesDetail):
        assert shipped <= set(schema.model_fields), schema.__name__
        for key in SERVER_ONLY:
            assert key not in schema.model_fields, (schema.__name__, key)
        for column in LEGACY:
            assert schema.model_fields[column].is_required() is False, column
    assert set(CareSourceRead.model_fields) == {
        "authority", "url", "fields", "inferred"}
    assert "care_sources" in SpeciesDetail.model_fields
    assert "care_sources" not in SpeciesRead.model_fields


def test_detail_schema_tolerates_a_never_recomputed_row():
    """Validating straight off the model, as tests and tooling do, must give
    an empty list where the column is still null."""
    out = SpeciesDetail.model_validate(minted("Testus nullus", "Nullus", id=1))
    assert out.care_sources == []
    assert out.toxic_to_pets is None
