"""Migration 0020: `climbs` on `species`.

One nullable boolean. What matters is that it arrives null rather than false
-- false would say every species nobody researched stands on its own -- and
that it survives a downgrade and upgrade, since it is materialised from claims
(ADR 0001).
"""
import sqlite3
from pathlib import Path

from alembic import command

from tests.test_migration_0015 import _config
from tests.test_migration_0019 import SPECIES_INSERT, _columns
from tests.test_migrations import _upgrade

PREVIOUS = "0019_fit_fields"


def _assert_added(conn) -> None:
    info = _columns(conn)
    assert "climbs" in info
    assert info["climbs"][2] == "BOOLEAN"
    assert info["climbs"][3] == 0, "climbs must be nullable"
    assert info["climbs"][4] is None, "climbs must have no default"


def test_fresh_db_carries_climbs(tmp_path: Path):
    db = tmp_path / "fresh.db"
    _upgrade(f"sqlite:///{db.as_posix()}")
    conn = sqlite3.connect(db)
    _assert_added(conn)
    conn.close()


def test_an_existing_species_arrives_null_not_false(tmp_path: Path, monkeypatch):
    db = tmp_path / "at0019.db"
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
    assert conn.execute("SELECT climbs FROM species").fetchone() == (None,)
    conn.close()


def test_climbs_round_trips_through_downgrade(tmp_path: Path, monkeypatch):
    db = tmp_path / "roundtrip.db"
    url = f"sqlite:///{db.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", url)
    cfg = _config(url)
    command.upgrade(cfg, "head")

    conn = sqlite3.connect(db)
    conn.execute(SPECIES_INSERT)
    conn.execute("UPDATE species SET climbs = 1, mature_height_in_max = 600")
    conn.commit()
    conn.close()

    command.downgrade(cfg, PREVIOUS)
    conn = sqlite3.connect(db)
    assert "climbs" not in _columns(conn)
    # The height stays: only the qualifier goes, and a recompute restores it.
    assert conn.execute(
        "SELECT mature_height_in_max FROM species").fetchone() == (600.0,)
    conn.close()

    command.upgrade(cfg, "head")
    conn = sqlite3.connect(db)
    _assert_added(conn)
    conn.close()
