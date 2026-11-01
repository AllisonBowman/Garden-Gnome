"""Migration 0023: `eaten_parts` on `species`.

One nullable JSON column. What matters is that it arrives null rather than
as an empty list -- an empty list would say nothing is eaten of every plant
nobody asked about -- and that it survives a downgrade and upgrade, since it
is materialised from claims (ADR 0001, ADR 0011).
"""
import sqlite3
from pathlib import Path

from alembic import command

from tests.test_migration_0015 import _config
from tests.test_migration_0019 import SPECIES_INSERT, _columns
from tests.test_migrations import _upgrade

PREVIOUS = "0022_backfill_acquired_on"


def _assert_added(conn) -> None:
    info = _columns(conn)
    assert "eaten_parts" in info
    assert info["eaten_parts"][2] == "JSON"
    assert info["eaten_parts"][3] == 0, "eaten_parts must be nullable"
    assert info["eaten_parts"][4] is None, "eaten_parts must have no default"


def test_fresh_db_carries_eaten_parts(tmp_path: Path):
    db = tmp_path / "fresh.db"
    _upgrade(f"sqlite:///{db.as_posix()}")
    conn = sqlite3.connect(db)
    _assert_added(conn)
    conn.close()


def test_an_existing_species_arrives_null_not_empty(tmp_path: Path, monkeypatch):
    db = tmp_path / "at0022.db"
    url = f"sqlite:///{db.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", url)
    cfg = _config(url)
    command.upgrade(cfg, PREVIOUS)

    conn = sqlite3.connect(db)
    conn.execute(SPECIES_INSERT)
    conn.commit()
    conn.close()

    command.upgrade(cfg, "head")
    conn = sqlite3.connect(db)
    _assert_added(conn)
    assert conn.execute("SELECT eaten_parts FROM species").fetchone() == (None,)
    conn.close()


def test_eaten_parts_round_trips_through_downgrade(tmp_path: Path, monkeypatch):
    db = tmp_path / "roundtrip.db"
    url = f"sqlite:///{db.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", url)
    cfg = _config(url)
    command.upgrade(cfg, "head")

    conn = sqlite3.connect(db)
    conn.execute(SPECIES_INSERT)
    conn.execute("UPDATE species SET eaten_parts = '[\"leaves\"]', is_edible = 1")
    conn.commit()
    conn.close()

    command.downgrade(cfg, PREVIOUS)
    conn = sqlite3.connect(db)
    assert "eaten_parts" not in _columns(conn)
    # The boolean stays: only the parts go, and a recompute restores them.
    assert conn.execute("SELECT is_edible FROM species").fetchone() == (1,)
    conn.close()

    command.upgrade(cfg, "head")
    conn = sqlite3.connect(db)
    _assert_added(conn)
    assert conn.execute("SELECT eaten_parts FROM species").fetchone() == (None,)
    conn.close()
