"""Migration 0016: `hardiness_zones` becomes `outdoor_temp_min_f`.

USDA PLANTS never published zones, so the column named for them was never
written. The rename has to hold on a fresh database and on one at 0015, has
to refuse -- before dropping anything -- if a value somehow did get written,
and has to downgrade back to the old shape without losing the row.
"""
import sqlite3
from pathlib import Path

import pytest
from alembic import command

from tests.test_migration_0015 import _config, _insert_plant_of
from tests.test_migrations import _upgrade

MINTED_INSERT = (
    "INSERT INTO species (common_name, scientific_name, care_notes, source, "
    "source_ref, review_status, review_note{extra_cols}) VALUES ('Rosemary', "
    "'Salvia rosmarinus', '', 'claims', 'b1.json', 'approved', ''{extra_vals})")


def _columns(conn) -> dict:
    return {r[1]: r for r in conn.execute("PRAGMA table_info(species)")}


def _tables(conn) -> set:
    return {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}


def _at_0015(tmp_path: Path, monkeypatch, name: str):
    db = tmp_path / name
    url = f"sqlite:///{db.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", url)
    cfg = _config(url)
    command.upgrade(cfg, "0015_species_claim_wiring")
    return db, cfg


def _assert_renamed(conn) -> None:
    info = _columns(conn)
    assert "hardiness_zones" not in info
    assert info["outdoor_temp_min_f"][2] == "FLOAT"
    assert info["outdoor_temp_min_f"][3] == 0, "outdoor_temp_min_f must be nullable"
    assert "_alembic_tmp_species" not in _tables(conn)
    assert conn.execute("PRAGMA foreign_key_check").fetchall() == []


def test_fresh_db_holds_a_minimum_temperature_and_no_zones(tmp_path: Path):
    db = tmp_path / "fresh.db"
    _upgrade(f"sqlite:///{db.as_posix()}")

    conn = sqlite3.connect(db)
    _assert_renamed(conn)
    conn.execute(MINTED_INSERT.format(
        extra_cols=", outdoor_temp_min_f", extra_vals=", -13.0"))
    conn.commit()
    assert conn.execute(
        "SELECT outdoor_temp_min_f FROM species").fetchone() == (-13.0,)
    conn.close()


def test_a_0015_db_is_renamed_and_downgrades_back(tmp_path: Path, monkeypatch):
    db, cfg = _at_0015(tmp_path, monkeypatch, "at0015.db")
    conn = sqlite3.connect(db)
    # A row that never had a zone list -- the only kind there has ever been --
    # and one whose ORM write left the JSON text 'null' rather than SQL NULL.
    conn.execute(MINTED_INSERT.format(extra_cols="", extra_vals=""))
    conn.execute(
        "INSERT INTO species (common_name, scientific_name, care_notes, source, "
        "source_ref, review_status, review_note, hardiness_zones) VALUES "
        "('Wired', 'Wired wiredus', '', 'claims', 'b1.json', 'approved', '', 'null')")
    species_id = conn.execute(
        "SELECT id FROM species WHERE scientific_name = 'Wired wiredus'").fetchone()[0]
    _insert_plant_of(conn, species_id)
    conn.commit()
    conn.close()

    command.upgrade(cfg, "head")

    conn = sqlite3.connect(db)
    _assert_renamed(conn)
    assert conn.execute("SELECT version_num FROM alembic_version").fetchone() == (
        "0016_outdoor_temp_min_f",)
    joined = conn.execute(
        "SELECT s.outdoor_temp_min_f FROM plant p JOIN species s ON s.id = p.species_id "
        "WHERE p.nickname = 'Wired'").fetchone()
    assert joined == (None,)
    conn.execute("UPDATE species SET outdoor_temp_min_f = -13.0 WHERE id = ?", (species_id,))
    conn.commit()
    conn.close()

    # Reversing the swap gives the old column back, empty, and keeps the row.
    command.downgrade(cfg, "0015_species_claim_wiring")
    conn = sqlite3.connect(db)
    info = _columns(conn)
    assert "outdoor_temp_min_f" not in info and info["hardiness_zones"][3] == 0
    assert "_alembic_tmp_species" not in _tables(conn)
    assert conn.execute(
        "SELECT s.hardiness_zones FROM plant p JOIN species s ON s.id = p.species_id "
        "WHERE p.nickname = 'Wired'").fetchone() == (None,)
    conn.close()

    command.upgrade(cfg, "head")
    conn = sqlite3.connect(db)
    _assert_renamed(conn)
    assert conn.execute("SELECT count(*) FROM species").fetchone() == (2,)
    conn.close()


def test_upgrade_refuses_before_dropping_a_column_something_wrote(
        tmp_path: Path, monkeypatch):
    """A zone list and a temperature are not the same fact, so a value in
    the old column cannot be carried over -- and a migration that threw it
    away would hide that something wrote a column nothing was allowed to."""
    db, cfg = _at_0015(tmp_path, monkeypatch, "written.db")
    conn = sqlite3.connect(db)
    conn.execute(MINTED_INSERT.format(
        extra_cols=", hardiness_zones", extra_vals=", '[7, 8, 9, 10]'"))
    conn.commit()
    conn.close()

    with pytest.raises(RuntimeError, match="hardiness_zones.*1 row"):
        command.upgrade(cfg, "head")

    conn = sqlite3.connect(db)
    assert conn.execute("SELECT version_num FROM alembic_version").fetchone() == (
        "0015_species_claim_wiring",)
    assert "_alembic_tmp_species" not in _tables(conn)
    assert conn.execute("SELECT hardiness_zones FROM species").fetchone() == (
        "[7, 8, 9, 10]",)
    # Once whoever wrote it has been dealt with, the same database goes on.
    conn.execute("UPDATE species SET hardiness_zones = NULL")
    conn.commit()
    conn.close()

    command.upgrade(cfg, "head")
    conn = sqlite3.connect(db)
    _assert_renamed(conn)
    conn.close()
