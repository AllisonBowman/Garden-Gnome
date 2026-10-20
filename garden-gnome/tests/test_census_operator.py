"""The census export is the operator's, and nothing in it outlives one export.

It holds every opted-in household's plants, city and care history, so it is
not a user route: GET /census/export and POST /census/sync answer only the
operator credential (X-Operator-Token against CENSUS_OPERATOR_TOKEN), and
with none configured they answer 404. And because the consent copy promises
that no identifier links two exports, no record carries a plant's real UUID:
it carries a hash under a salt drawn for that export alone. Nor does its
position or its care dates link it: records are shuffled, and care is a
count per month (test_the_census_content_does_not_link_two_exports).
"""
import json
import re
from datetime import date, datetime

import pytest
from sqlmodel import Session, create_engine, select

from app.models.models import (
    CareLog, CareType, GrowingArea, GrowingAreaType, Plant, Species, User,
)
from app.services import tokens
from tests import census_operator


@pytest.fixture()
def census(migrated_db_url, monkeypatch):
    """One opted-in user with a planting, a split-off and a care log.

    Hermetic about where a sync would go: app.main loads garden-gnome/.env,
    and a CENSUS_API_URL there or in the shell would have these tests post
    the test database's export to it. Unset here, and any send that a test
    has not stubbed itself fails loudly instead of leaving the machine."""
    from fastapi.testclient import TestClient
    import httpx

    monkeypatch.delenv("CENSUS_API_URL", raising=False)

    def no_sending(*args, **kwargs):
        raise AssertionError("a census test tried to send an export")

    monkeypatch.setattr(httpx, "post", no_sending)

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
            species = Species(common_name="Census Fern",
                              scientific_name="Censusia testus")
            s.add(species)
            s.flush()
        user = User(email="census-op@example.com", census_opt_in=True)
        s.add(user)
        s.flush()
        area = GrowingArea(name="Back bed", type=GrowingAreaType.home,
                           user_id=user.id, city="Baltimore", region="MD",
                           country="US", lat=39.290613, lng=-76.612189)
        s.add(area)
        s.flush()
        parent = Plant(nickname="Bed of twelve", species_id=species.id,
                       growing_area_id=area.id, user_id=user.id, quantity=9,
                       acquired_on=date(2026, 4, 17))
        s.add(parent)
        s.flush()
        offshoot = Plant(nickname="Three off the end", species_id=species.id,
                         growing_area_id=area.id, user_id=user.id, quantity=3,
                         split_from_uuid=parent.plant_uuid)
        s.add(offshoot)
        s.flush()
        s.add(CareLog(plant_id=parent.id, action=CareType.water,
                      logged_at=datetime(2026, 5, 2, 9, 14, 22, 123456)))
        s.commit()
        uuids = (parent.plant_uuid, offshoot.plant_uuid)
        headers = {"Authorization":
                   f"Bearer {tokens.issue_access_token(user.id)}"}

    class Census:
        def __init__(self):
            self.client = client
            self.parent_uuid, self.offshoot_uuid = uuids
            self.user_headers = headers

        def mine(self, body: dict, refs: set) -> list:
            return [p for p in body["plants"] if p["plant_ref"] in refs]

    yield Census()
    app.dependency_overrides.clear()
    engine.dispose()


# --- Who may call it ----------------------------------------------------------


def test_unconfigured_the_routes_do_not_exist(census, monkeypatch):
    monkeypatch.delenv("CENSUS_OPERATOR_TOKEN", raising=False)
    for headers in ({}, census.user_headers,
                    {"X-Operator-Token": "anything at all"}):
        assert census.client.get(
            "/census/export", headers=headers).status_code == 404
        assert census.client.post(
            "/census/sync", headers=headers).status_code == 404


def test_an_empty_credential_does_not_switch_them_on(census, monkeypatch):
    monkeypatch.setenv("CENSUS_OPERATOR_TOKEN", "")
    assert census.client.get(
        "/census/export", headers={"X-Operator-Token": ""}).status_code == 404


def test_configured_they_want_the_operator_credential(census, monkeypatch):
    headers = census_operator.as_operator(monkeypatch)
    # No credential, a signed-in user's token, or a wrong guess: 401.
    for wrong in ({}, census.user_headers, {"X-Operator-Token": "guess"},
                  {"X-Operator-Token": headers["X-Operator-Token"] + "x"}):
        assert census.client.get(
            "/census/export", headers=wrong).status_code == 401
        assert census.client.post(
            "/census/sync", headers=wrong).status_code == 401

    assert census.client.get("/census/export", headers=headers).status_code == 200
    synced = census.client.post("/census/sync", headers=headers)
    assert synced.status_code == 200
    assert synced.json()["status"] == "skipped", "nothing configured, nothing sent"


@pytest.mark.parametrize("secret", [
    "x" * 31,                 # a character short
    "  short-but-padded   ",  # whitespace does not count toward it
    "   ",
])
def test_a_secret_too_short_to_honour_leaves_the_routes_off(
        census, monkeypatch, caplog, secret):
    """`openssl rand -hex 32` gives 64 characters. A short or mistyped
    secret could be guessed against the route that hands out every
    opted-in household, so it counts as unset -- 404, even with the secret
    itself in the header -- and the log says why."""
    from app.routers import census as census_router

    monkeypatch.setattr(census_router, "_short_token_logged", set())
    monkeypatch.setenv("CENSUS_OPERATOR_TOKEN", secret)
    caplog.set_level("WARNING", logger="app.routers.census")
    for _ in range(2):
        assert census.client.get(
            "/census/export", headers={"X-Operator-Token": secret.strip() or "x"}
        ).status_code == 404
        assert census.client.post(
            "/census/sync", headers={"X-Operator-Token": secret.strip() or "x"}
        ).status_code == 404
    said = [r for r in caplog.records if "CENSUS_OPERATOR_TOKEN" in r.getMessage()]
    if secret.strip():
        assert len(said) == 1, "said once, not on every request"
        assert "at least 32" in said[0].getMessage()
        assert secret.strip() not in said[0].getMessage(), "never the secret itself"


def test_a_secret_of_32_characters_is_honoured(census, monkeypatch):
    secret = "k" * 32
    monkeypatch.setenv("CENSUS_OPERATOR_TOKEN", secret)
    assert census.client.get(
        "/census/export", headers={"X-Operator-Token": secret}).status_code == 200
    assert census.client.get(
        "/census/export", headers={"X-Operator-Token": "k" * 31}).status_code == 401


def test_the_routes_are_not_advertised(census):
    paths = census.client.get("/openapi.json").json()["paths"]
    assert "/census/export" not in paths and "/census/sync" not in paths
    # The caller's own summary is unchanged: a user route, in the schema.
    assert "/census/summary" in paths


def test_the_callers_own_summary_still_answers_the_user(census):
    r = census.client.get("/census/summary", headers=census.user_headers)
    assert r.status_code == 200
    assert census.client.get("/census/summary").status_code == 401


# --- What it carries ----------------------------------------------------------


def test_no_record_carries_a_real_plant_uuid(census, monkeypatch):
    body = census_operator.export(census.client, monkeypatch)
    text = json.dumps(body)
    assert census.parent_uuid not in text and census.offshoot_uuid not in text
    for record in body["plants"]:
        assert "plant_uuid" not in record
        assert "split_from_uuid" not in record
        assert re.fullmatch(r"[0-9a-f]{64}", record["plant_ref"])
    assert body["export_version"] == "4.1"


def test_the_refs_differ_between_two_exports(census, monkeypatch):
    first = census_operator.export(census.client, monkeypatch)
    second = census_operator.export(census.client, monkeypatch)
    refs_1 = {p["plant_ref"] for p in first["plants"]}
    refs_2 = {p["plant_ref"] for p in second["plants"]}
    assert refs_1 and refs_2
    assert refs_1.isdisjoint(refs_2), "two exports could be joined on plant_ref"
    split_1 = {p["split_from_ref"] for p in first["plants"]} - {None}
    assert split_1 and split_1.isdisjoint(refs_2)


def test_a_split_still_names_its_parent_within_one_export(census, monkeypatch):
    census_operator.pin_salt(monkeypatch)
    body = census_operator.export(census.client, monkeypatch)
    parent_ref = census_operator.ref(census.parent_uuid)
    offshoot_ref = census_operator.ref(census.offshoot_uuid)
    by_ref = {p["plant_ref"]: p for p in census.mine(
        body, {parent_ref, offshoot_ref})}
    assert by_ref[offshoot_ref]["split_from_ref"] == parent_ref
    assert by_ref[parent_ref]["split_from_ref"] is None
    assert by_ref[parent_ref]["quantity"] + by_ref[offshoot_ref]["quantity"] == 12


def test_care_is_counted_by_month_and_every_time_is_a_month(census, monkeypatch):
    """A microsecond timestamp repeated in every export is as good as an id,
    and so is a list of care dates."""
    census_operator.pin_salt(monkeypatch)
    body = census_operator.export(census.client, monkeypatch)
    [parent] = census.mine(body, {census_operator.ref(census.parent_uuid)})
    assert parent["care_history"] == {"water": {"2026-05": 1}}
    assert parent["acquired_month"] == "2026-04"
    assert "acquired_on" not in parent
    for link in parent["stewardship_chain"]:
        assert set(link) == {"started_month", "ended_month"}
        assert re.fullmatch(r"\d{4}-\d{2}", link["started_month"])
    assert not re.search(r"\d{4}-\d{2}-\d{2}", json.dumps(body["plants"])), \
        "no day reaches the export"
    area = parent["growing_area"]
    assert {"lat", "lng", "uuid"}.isdisjoint(area)
    assert area["city"] == "Baltimore"


def test_sync_pushes_the_same_unlinkable_export(census, monkeypatch):
    headers = census_operator.as_operator(monkeypatch)
    monkeypatch.setenv("CENSUS_API_URL", "https://census.invalid")
    sent = []

    class Ok:
        def raise_for_status(self):
            return None

    import httpx
    monkeypatch.setattr(httpx, "post",
                        lambda url, json, timeout: sent.append((url, json)) or Ok())
    r = census.client.post("/census/sync", headers=headers)
    assert r.status_code == 200 and r.json()["status"] == "ok"
    [(url, payload)] = sent
    assert url == "https://census.invalid/ingest"
    text = json.dumps(payload)
    assert census.parent_uuid not in text and census.offshoot_uuid not in text


def test_sync_with_no_destination_sends_nothing(census, monkeypatch):
    headers = census_operator.as_operator(monkeypatch)
    monkeypatch.delenv("CENSUS_API_URL", raising=False)
    r = census.client.post("/census/sync", headers=headers)
    assert r.status_code == 200 and r.json()["status"] == "skipped"
