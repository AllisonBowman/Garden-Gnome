"""GET /species/ is built once per catalog version, not once per request.

Validating every row into SpeciesRead on every request took a 256 MB machine
past 220 MB at ten requests at once (1,940 production rows plus the minted
ones). The body is now built once and served as bytes. What has to hold: the
bytes are what the response model would have produced, the build happens
once however many phones ask at once, and any change to the catalog -- a
sync, a seeded row, a write through the API -- is seen on the next request.
"""
import gzip
import threading
import time

import pytest
from sqlmodel import Session, create_engine, select

from app.models.models import Species, SpeciesSource, SpeciesTrait, SyncState
from app.models.schemas import SpeciesRead
from app.routers import species as species_router


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
        user = User(email="catalog-cache@example.com")
        s.add(user)
        s.commit()
        headers = {
            "Authorization": f"Bearer {tokens.issue_access_token(user.id)}"}
    species_router._catalog = None
    try:
        yield TestClient(app), headers, engine
    finally:
        species_router._catalog = None
        app.dependency_overrides.clear()
        engine.dispose()


def _add(engine, name: str) -> int:
    with Session(engine) as s:
        row = Species(common_name=f"Cache {name}", scientific_name=f"Cachea {name}",
                      source=SpeciesSource.claims, source_ref="b1-test.json",
                      toxic_to_pets=None, care_notes="")
        s.add(row)
        s.commit()
        return row.id


def _count_builds(monkeypatch) -> list:
    builds = []
    real = species_router._build_catalog

    def counting(session):
        builds.append(1)
        return real(session)

    monkeypatch.setattr(species_router, "_build_catalog", counting)
    return builds


def test_the_bytes_are_what_the_response_model_would_produce(api):
    client, headers, engine = api
    _add(engine, "exactus")
    with Session(engine) as s:
        derived = set(s.exec(select(SpeciesTrait.species_id).where(
            SpeciesTrait.trait == "humidity_source")).all())
        expected = [
            SpeciesRead.model_validate(
                sp, update={"humidity_sourced": sp.id not in derived}
            ).model_dump(mode="json", exclude_none=True)
            for sp in s.exec(select(Species)).all()]

    plain = client.get("/species/", headers={**headers, "Accept-Encoding": "identity"})
    assert plain.status_code == 200
    assert plain.headers["content-type"] == "application/json"
    assert plain.json() == expected
    # Absent values stay absent keys, as response_model_exclude_none did.
    assert all(None not in row.values() for row in plain.json())


def test_gzip_is_the_same_body_compressed_once(api, monkeypatch):
    client, headers, engine = api
    builds = _count_builds(monkeypatch)
    packed = client.get("/species/", headers={**headers, "Accept-Encoding": "gzip"})
    plain = client.get("/species/", headers={**headers, "Accept-Encoding": "identity"})
    assert packed.headers["content-encoding"] == "gzip"
    assert "accept-encoding" in packed.headers["vary"].lower()
    assert "content-encoding" not in plain.headers
    assert packed.json() == plain.json()
    # Both encodings came from one build.
    assert builds == [1]
    assert gzip.decompress(species_router._catalog.gzipped) == plain.content


def test_repeat_requests_reuse_the_built_body(api, monkeypatch):
    client, headers, engine = api
    builds = _count_builds(monkeypatch)
    for _ in range(5):
        assert client.get("/species/", headers=headers).status_code == 200
    assert builds == [1]


def test_a_row_added_behind_the_api_is_seen_on_the_next_request(api, monkeypatch):
    """The seed and the claim sync write straight to the database."""
    client, headers, engine = api
    builds = _count_builds(monkeypatch)
    client.get("/species/", headers=headers)
    sid = _add(engine, "seedus")
    ids = {row["id"] for row in client.get("/species/", headers=headers).json()}
    assert sid in ids
    assert builds == [1, 1]


def test_a_new_sync_fingerprint_rebuilds(api, monkeypatch):
    client, headers, engine = api
    builds = _count_builds(monkeypatch)
    client.get("/species/", headers=headers)
    with Session(engine) as s:
        state = s.get(SyncState, "tranche_fingerprint")
        before = state.value if state else None
        if state is None:
            s.add(SyncState(key="tranche_fingerprint", value="test-fingerprint"))
        else:
            state.value = "test-fingerprint"
            s.add(state)
        s.commit()
    try:
        client.get("/species/", headers=headers)
        assert builds == [1, 1]
    finally:
        with Session(engine) as s:
            state = s.get(SyncState, "tranche_fingerprint")
            if before is None:
                s.delete(state)
            else:
                state.value = before
                s.add(state)
            s.commit()


def test_a_write_through_the_api_is_seen_on_the_next_request(api):
    client, headers, engine = api
    client.get("/species/", headers=headers)
    created = client.post("/species/", headers=headers, json={
        "common_name": "Cache Created", "scientific_name": "Cachea creata",
        "light_need": "medium", "humidity_pct_min": 40, "humidity_pct_max": 60,
        "temp_f_min": 60, "temp_f_max": 80, "soil_type": "mix",
        "toxic_to_pets": False, "care_notes": "", "schedules": [], "traits": [],
    })
    assert created.status_code == 201, created.text
    names = {row["scientific_name"]
             for row in client.get("/species/", headers=headers).json()}
    assert "Cachea creata" in names


def test_ten_requests_at_a_cold_start_build_once(api, monkeypatch):
    """The case that ran the machine out of memory: everyone at once."""
    client, headers, engine = api
    real = species_router._build_catalog
    builds = []

    def slow(session):
        builds.append(1)
        time.sleep(0.2)  # long enough that every thread arrives mid-build
        return real(session)

    monkeypatch.setattr(species_router, "_build_catalog", slow)
    start = threading.Barrier(10)
    bodies = []

    def ask():
        with Session(engine) as s:
            start.wait()
            bodies.append(species_router._catalog_body(s).identity)

    threads = [threading.Thread(target=ask) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)
    assert len(bodies) == 10 and len(set(bodies)) == 1
    assert builds == [1]
