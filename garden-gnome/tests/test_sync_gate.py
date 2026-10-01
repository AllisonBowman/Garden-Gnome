"""The skip gate has to see the table, not only the tranche.

seed() inserts any new catalog entry before the sync on every boot, and
POST /species adds a row at any time. Neither changes a tranche byte, so a
gate that digested the batch files alone would skip -- and the new row would
sit unlinked and unresolved, care_data_status null, until the tranche or a
version happened to move. A row nothing has resolved carries no resolver
version, and that is the second thing a skip checks.
"""
from sqlmodel import Session

from app.data.claims.recompute import RESOLVER_VERSION
from app.data.claims.sync import sync_catalog
from tests.test_claim_sync import (  # noqa: F401  (db is a fixture)
    db, legacy_species, record, rows, write_batch,
)


def test_a_row_added_after_the_sync_is_not_hidden_by_an_unchanged_tranche(db, tmp_path):
    engine, work = db
    tranche = tmp_path / "tranche"
    # Genus-level evidence only: nothing to mint, but something a congener
    # added later should inherit -- if the sync ever looks at it again.
    write_batch(tranche, "b1-test.json",
                [record("Amaryllis", "Hippeastrum", humidity_need="average")])
    with Session(engine) as s:
        first = sync_catalog(s, directory=tranche)
    assert first.skipped is False and first.species_created == 0

    with Session(engine) as s:
        s.add(legacy_species("Hippeastrum papilio", "Butterfly Amaryllis"))
        s.commit()
    with Session(engine) as s:
        second = sync_catalog(s, directory=tranche)

    assert second.skipped is False
    assert second.species_created == 0 and second.species_linked == 0
    assert second.recompute.species_updated == 1
    congener, = rows(engine, "Hippeastrum papilio")
    assert congener.resolver_version == RESOLVER_VERSION
    assert congener.humidity_need == "average"
    assert congener.care_provenance["humidity_need"] == "genus_inferred"

    # Now every row is in step, and the unchanged tranche is a skip again.
    before = work.read_bytes()
    with Session(engine) as s:
        third = sync_catalog(s, directory=tranche)
    assert third.skipped is True
    assert work.read_bytes() == before
