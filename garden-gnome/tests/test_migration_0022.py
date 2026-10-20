"""Migration 0022: every plant added before the server dated plants gets the
day it was added as its acquired_on.

Checked on a database shaped like production's: brought to 0021, filled the
way 1.1.2 left it (no plant with acquired_on), then upgraded.
"""
import sqlite3
from pathlib import Path

from alembic import command

from tests.test_migration_0015 import _config

PREVIOUS = "0021_pending_apple_revocation"


def _plant(conn, uuid: str, created_at: str, acquired_on=None, split_from=None):
    conn.execute(
        "INSERT INTO plant (plant_uuid, nickname, species_id, location, "
        "maturity_stage, created_at, pest_observed_at_acquisition, "
        "intake_notes, acquired_on, split_from_uuid) "
        "VALUES (?, ?, 1, '', 'juvenile', ?, 0, '', ?, ?)",
        (uuid, uuid, created_at, acquired_on, split_from))


def _acquired(conn) -> dict:
    return dict(conn.execute("SELECT plant_uuid, acquired_on FROM plant"))


def test_plants_from_before_the_server_dated_them_are_dated(tmp_path: Path,
                                                            monkeypatch):
    db = tmp_path / "shape-0021.db"
    url = f"sqlite:///{db.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", url)
    cfg = _config(url)
    command.upgrade(cfg, PREVIOUS)

    conn = sqlite3.connect(db)
    conn.execute(
        "INSERT INTO species (id, common_name, scientific_name, care_notes, "
        "source, source_ref, review_status, review_note) VALUES "
        "(1, 'Basil', 'Ocimum basilicum', '', 'curated', '', 'approved', '')")
    _plant(conn, "added-in-1.1.2", "2026-08-01 23:30:00.000000")
    _plant(conn, "dated-by-hand", "2026-08-02 09:00:00", acquired_on="2026-07-04")
    _plant(conn, "split-in-1.1.2", "2026-09-02 12:00:00",
           split_from="added-in-1.1.2")
    _plant(conn, "orphaned-split", "2026-09-03 12:00:00", split_from="gone")
    conn.commit()
    assert set(_acquired(conn).values()) == {None, "2026-07-04"}
    conn.close()

    command.upgrade(cfg, "head")

    conn = sqlite3.connect(db)
    assert _acquired(conn) == {
        # The day it was added, in UTC like every stored time.
        "added-in-1.1.2": "2026-08-01",
        # Someone's own date is theirs.
        "dated-by-hand": "2026-07-04",
        # A split carries its parent's date, as the split route does now.
        "split-in-1.1.2": "2026-08-01",
        "orphaned-split": "2026-09-03",
    }
    conn.close()

    # The downgrade changes no column and keeps the true dates; going up
    # again finds nothing left to date.
    command.downgrade(cfg, PREVIOUS)
    command.upgrade(cfg, "head")
    conn = sqlite3.connect(db)
    assert None not in _acquired(conn).values()
    conn.close()


def test_the_dated_plant_reads_as_a_date_through_the_model(tmp_path: Path,
                                                           monkeypatch):
    """What the API serializes: a date, not a string the model chokes on."""
    from datetime import date

    from sqlmodel import Session, create_engine, select

    from app.models.models import Plant

    db = tmp_path / "read-back.db"
    url = f"sqlite:///{db.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", url)
    cfg = _config(url)
    command.upgrade(cfg, PREVIOUS)
    conn = sqlite3.connect(db)
    conn.execute(
        "INSERT INTO species (id, common_name, scientific_name, care_notes, "
        "source, source_ref, review_status, review_note) VALUES "
        "(1, 'Basil', 'Ocimum basilicum', '', 'curated', '', 'approved', '')")
    _plant(conn, "read-me", "2026-08-01 10:00:00")
    conn.commit()
    conn.close()
    command.upgrade(cfg, "head")

    engine = create_engine(url)
    with Session(engine) as s:
        plant = s.exec(select(Plant).where(Plant.plant_uuid == "read-me")).one()
        assert plant.acquired_on == date(2026, 8, 1)
    engine.dispose()
