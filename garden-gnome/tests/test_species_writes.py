"""Writing to the shared catalog is an operator job, not a user's.

Every account reads the same species table, so a row one person adds is a
row everyone sees and every advice call trusts. The write routes (create,
bulk import, generate) therefore take the operator credential the census
export takes, and are hidden from the public schema; a signed-in gardener
gets the same 404 or 401 as anyone else. Reading, identifying and the
client's catalog list are untouched.
"""
import pytest
from sqlmodel import Session, create_engine

from app.models.models import User
from app.services import tokens
from tests.census_operator import as_operator


@pytest.fixture()
def api(migrated_db_url):
    from fastapi.testclient import TestClient

    from app.db.database import get_session
    from app.main import app

    engine = create_engine(migrated_db_url, connect_args={"check_same_thread": False})

    def override():
        with Session(engine) as s:
            yield s

    app.dependency_overrides[get_session] = override
    client = TestClient(app)
    with Session(engine) as s:
        user = User(email="writer@example.com")
        s.add(user)
        s.commit()
        user_id = user.id
    headers = {"Authorization": f"Bearer {tokens.issue_access_token(user_id)}"}
    yield client, headers
    app.dependency_overrides.clear()
    engine.dispose()


NEW_SPECIES = {
    "common_name": "Test Fern", "scientific_name": "Nephrolepis testii",
    "light_need": "medium", "humidity_pct_min": 40, "humidity_pct_max": 70,
    "temp_f_min": 55, "temp_f_max": 85, "soil_type": "peat", "toxic_to_pets": False,
    "care_notes": "A test row.",
}


def test_a_signed_in_gardener_cannot_add_to_the_catalog(api, monkeypatch):
    client, headers = api
    monkeypatch.delenv("CENSUS_OPERATOR_TOKEN", raising=False)
    # No operator credential configured: the routes do not exist, as far as
    # anyone can tell.
    assert client.post("/species/", headers=headers, json=NEW_SPECIES).status_code == 404
    assert client.post("/species/bulk", headers=headers, json=[NEW_SPECIES]).status_code == 404
    assert client.post("/species/generate", headers=headers,
                       json={"common_name": "Anything"}).status_code == 404


def test_the_wrong_operator_token_is_refused(api, monkeypatch):
    client, headers = api
    as_operator(monkeypatch)
    bad = {**headers, "X-Operator-Token": "not-the-token"}
    assert client.post("/species/", headers=bad, json=NEW_SPECIES).status_code == 401


def test_the_operator_can_add_a_species(api, monkeypatch):
    client, headers = api
    operator = {**headers, **as_operator(monkeypatch)}
    r = client.post("/species/", headers=operator, json=NEW_SPECIES)
    assert r.status_code == 201, r.text
    assert r.json()["scientific_name"] == "Nephrolepis testii"


def test_reading_the_catalog_still_needs_only_a_sign_in(api):
    client, headers = api
    assert client.get("/species/", headers=headers).status_code == 200


def test_the_write_routes_are_not_advertised(api):
    client, _ = api
    paths = client.get("/openapi.json").json()["paths"]
    assert "/species/bulk" not in paths
    assert "/species/generate" not in paths
    assert "post" not in paths.get("/species/", {})
    assert "/species/identify-photo" in paths
