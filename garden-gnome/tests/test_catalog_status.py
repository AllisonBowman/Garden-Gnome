"""GET / says whether the catalog this build ships is the one serving.

seed.py swallows a failed claim sync so the API still boots ("claim sync
skipped", exit 0), and the deploy's smoke check used to look only for a 200 --
so a boot that served the old catalog went green. The root now reports
`catalog.synced`, true only when the last sync recorded the fingerprint of
the files in this build and reached every row, and the smoke check asserts it.
"""
from pathlib import Path

import pytest
from sqlmodel import Session, create_engine

from app.data.claims.recompute import RESOLVER_VERSION
from app.db import catalog_state
from app.models.models import Species, SpeciesSource, SyncState
from tests.test_migrations import _upgrade

SHIPPED = "0123456789abcdef0123456789abcdef:5:1"


@pytest.fixture()
def root(tmp_path: Path, monkeypatch):
    """A fresh database of its own: `synced` looks at every row, and the
    shared test database holds rows other tests left unresolved."""
    from fastapi.testclient import TestClient

    from app.db.database import get_session
    from app.main import app

    url = f"sqlite:///{(tmp_path / 'catalog.db').as_posix()}"
    _upgrade(url)
    engine = create_engine(url, connect_args={"check_same_thread": False})

    def override():
        with Session(engine) as s:
            yield s

    monkeypatch.setattr(catalog_state, "shipped_fingerprint", lambda: SHIPPED)
    app.dependency_overrides[get_session] = override
    client = TestClient(app)

    def catalog() -> dict:
        r = client.get("/")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"
        return r.json()["catalog"]

    try:
        yield catalog, engine
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def _species(engine, resolver_version):
    with Session(engine) as s:
        s.add(Species(common_name="Status Fern", scientific_name="Statusia testus",
                      source=SpeciesSource.claims, source_ref="b1-test.json",
                      toxic_to_pets=None, care_notes="",
                      resolver_version=resolver_version))
        s.commit()


def _record(engine, fingerprint: str) -> None:
    with Session(engine) as s:
        state = s.get(SyncState, "tranche_fingerprint")
        if state is None:
            s.add(SyncState(key="tranche_fingerprint", value=fingerprint))
        else:
            state.value = fingerprint
            s.add(state)
        s.commit()


def test_a_database_no_sync_has_reached_is_not_synced(root):
    catalog, engine = root
    status = catalog()
    assert status == {"version": "0123456789ab:5:1", "synced": False,
                      "species": 0, "claims": 0}


def test_synced_when_the_last_sync_recorded_this_builds_files(root):
    catalog, engine = root
    _species(engine, RESOLVER_VERSION)
    _record(engine, SHIPPED)
    status = catalog()
    assert status["synced"] is True
    assert status["species"] == 1


def test_a_skipped_sync_after_a_new_tranche_is_not_synced(root):
    """The case the smoke check missed: new batch files in the image, the
    sync failed, the old fingerprint is still recorded."""
    catalog, engine = root
    _species(engine, RESOLVER_VERSION)
    _record(engine, "an-older-tranche:5:1")
    assert catalog()["synced"] is False


def test_a_row_the_sync_never_reached_is_not_synced(root):
    """seed.py inserted a row and the sync that would have resolved it failed."""
    catalog, engine = root
    _species(engine, None)
    _record(engine, SHIPPED)
    assert catalog()["synced"] is False


def test_the_root_answers_even_when_the_state_cannot_be_read(root, monkeypatch):
    catalog, engine = root

    def broken(session):
        raise RuntimeError("no catalog tables")

    import app.main as main
    monkeypatch.setattr(main, "catalog_status", broken)
    assert catalog() == {"synced": False}


def test_the_shipped_fingerprint_is_the_claim_syncs_own():
    """No second idea of what "the catalog this build ships" means."""
    from app.data.claims.sync import tranche_fingerprint
    catalog_state.shipped_fingerprint.cache_clear()
    try:
        assert catalog_state.shipped_fingerprint() == tranche_fingerprint()
    finally:
        catalog_state.shipped_fingerprint.cache_clear()
