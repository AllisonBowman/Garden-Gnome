"""Migration 0015: the species table rebuilt for the claim wiring.

The batch rebuild of `species` is the first migration to rewrite that table
since the baseline, so three shapes have to come through it: a fresh
database, one at 0014, and the pre-Alembic shape the Fly volume actually has,
whose expansion columns carry server defaults that batch mode must reflect
rather than drop. And because a downgrade cannot restore NOT NULL over rows
the claims minted, it has to refuse without leaving the volume half-rebuilt.
"""
import sqlite3
from pathlib import Path

import pytest

from tests.conftest import ROOT
from tests.test_migrations import _upgrade

LEGACY_CARE = ("light_need", "humidity_pct_min", "humidity_pct_max",
               "temp_f_min", "temp_f_max", "soil_type", "toxic_to_pets")

PROVENANCE_JSON = '{"humidity_need": "sourced", "soil_drainage": "genus_inferred"}'
ZONES_JSON = "[7, 8, 9, 10]"
SUN_JSON = '["full_sun", "part_shade"]'

# `species` exactly as SQLModel's create_all built it before the catalog
# expansion -- the shape the Fly volume started from. Kept verbatim rather
# than derived from today's models, which have moved on; migrate_db() then
# adds the expansion columns the way it did on the volume.
PRE_EXPANSION_SPECIES = """
CREATE TABLE species (
    id INTEGER NOT NULL,
    common_name VARCHAR NOT NULL,
    scientific_name VARCHAR NOT NULL,
    light_need VARCHAR(15) NOT NULL,
    humidity_pct_min INTEGER NOT NULL,
    humidity_pct_max INTEGER NOT NULL,
    temp_f_min INTEGER NOT NULL,
    temp_f_max INTEGER NOT NULL,
    soil_type VARCHAR NOT NULL,
    toxic_to_pets BOOLEAN NOT NULL,
    care_notes VARCHAR NOT NULL,
    PRIMARY KEY (id)
)
"""


def _config(url: str):
    from alembic.config import Config

    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg


def _insert_plant_of(conn, species_id: int) -> None:
    conn.execute(
        "INSERT INTO plant (plant_uuid, nickname, species_id, location, "
        "maturity_stage, created_at, pest_observed_at_acquisition, "
        "intake_notes) VALUES ('u-wired', 'Wired', ?, '', 'juvenile', "
        "'2026-01-01 00:00:00', 0, '')", (species_id,))


def _assert_head_shape(conn) -> None:
    info = {r[1]: r for r in conn.execute("PRAGMA table_info(species)")}
    for col in LEGACY_CARE:
        assert info[col][3] == 0, f"{col} is still NOT NULL"
    assert "care_sources" in info and "scientific_name_accepted" in info
    indexes = {r[1] for r in conn.execute("PRAGMA index_list(species)")}
    assert {"ix_species_common_name", "ix_species_scientific_name",
            "ix_species_scientific_name_accepted"} <= indexes
    assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
    sync_cols = {r[1]: r for r in conn.execute("PRAGMA table_info(sync_state)")}
    assert sync_cols["key"][5] == 1 and sync_cols["value"][3] == 1
    # A claims-minted row: every legacy care column null, toxicity unknown.
    conn.execute(
        "INSERT INTO species (common_name, scientific_name, care_notes, "
        "source, source_ref, review_status, review_note) VALUES "
        "('Minted', 'Testus mintus', '', 'claims', 'b99.json', 'approved', '')")
    conn.commit()
    assert conn.execute(
        "SELECT toxic_to_pets, light_need FROM species "
        "WHERE scientific_name = 'Testus mintus'").fetchone() == (None, None)


def _assert_wired_row_survived(conn) -> None:
    joined = conn.execute(
        "SELECT s.scientific_name FROM plant p JOIN species s ON s.id = p.species_id "
        "WHERE p.nickname = 'Wired'").fetchone()
    assert joined == ("Wired wiredus",)


def test_fresh_db_has_the_claim_wiring(tmp_path: Path):
    db = tmp_path / "wiring.db"
    _upgrade(f"sqlite:///{db.as_posix()}")

    conn = sqlite3.connect(db)
    _assert_head_shape(conn)
    conn.close()


def test_a_0014_db_is_rebuilt_without_losing_a_byte_of_json(tmp_path: Path):
    import os

    from alembic import command

    db = tmp_path / "at0014.db"
    url = f"sqlite:///{db.as_posix()}"
    cfg = _config(url)
    prev = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = url
    try:
        command.upgrade(cfg, "0014_authority_scope")
        conn = sqlite3.connect(db)
        conn.execute(
            "INSERT INTO species (common_name, scientific_name, light_need, "
            "humidity_pct_min, humidity_pct_max, temp_f_min, temp_f_max, "
            "soil_type, toxic_to_pets, care_notes, source, source_ref, "
            "review_status, review_note, care_provenance, hardiness_zones, "
            "outdoor_sun_exposure) VALUES ('Wired', 'Wired wiredus', 'low', 40, "
            "60, 60, 80, 'mix', 0, '', 'curated', '', 'approved', '', ?, ?, ?)",
            (PROVENANCE_JSON, ZONES_JSON, SUN_JSON))
        species_id = conn.execute(
            "SELECT id FROM species WHERE scientific_name = 'Wired wiredus'"
        ).fetchone()[0]
        _insert_plant_of(conn, species_id)
        conn.execute(
            "INSERT INTO careschedule (species_id, care_type, interval_days_min, "
            "interval_days_max, notes) VALUES (?, 'water', 7, 10, '')", (species_id,))
        conn.execute(
            "INSERT INTO speciestrait (species_id, trait, value, unit) "
            "VALUES (?, 'growth_rate', 'slow', '')", (species_id,))
        conn.commit()
        conn.close()

        command.upgrade(cfg, "head")
    finally:
        if prev is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = prev

    conn = sqlite3.connect(db)
    _assert_head_shape(conn)
    assert conn.execute(
        "SELECT care_provenance, hardiness_zones, outdoor_sun_exposure "
        "FROM species WHERE scientific_name = 'Wired wiredus'"
    ).fetchone() == (PROVENANCE_JSON, ZONES_JSON, SUN_JSON)
    _assert_wired_row_survived(conn)
    assert conn.execute(
        "SELECT count(*) FROM careschedule cs JOIN species s ON s.id = cs.species_id"
    ).fetchone() == (1,)
    assert conn.execute(
        "SELECT count(*) FROM speciestrait t JOIN species s ON s.id = t.species_id"
    ).fetchone() == (1,)
    conn.close()


def test_the_pre_alembic_volume_shape_upgrades_to_head(tmp_path: Path, monkeypatch):
    """The Fly volume never saw 0001 run: its tables came from create_all, and
    migrate_db() bolted the expansion columns on with server defaults. Batch
    mode has to reflect those defaults into the rebuilt table, and the startup
    path (stamp baseline, then upgrade) has to carry the whole thing to head.
    """
    from alembic import command
    from sqlmodel import create_engine

    from app.db import database

    db = tmp_path / "volume.db"
    url = f"sqlite:///{db.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", url)

    # Every table but `species` is byte-for-byte what create_all produced at
    # the time -- 0001 is that snapshot. `species` predates the snapshot's
    # four expansion columns, so it is rebuilt in its older shape.
    command.upgrade(_config(url), "0001_baseline")
    conn = sqlite3.connect(db)
    conn.execute("DROP TABLE species")
    conn.execute(PRE_EXPANSION_SPECIES)
    conn.execute("CREATE INDEX ix_species_common_name ON species (common_name)")
    conn.execute("CREATE INDEX ix_species_scientific_name ON species (scientific_name)")
    conn.execute("DROP TABLE alembic_version")
    conn.commit()
    conn.close()

    engine = create_engine(url)
    monkeypatch.setattr(database, "engine", engine)
    database.migrate_db()   # the real one, defaults and all

    conn = sqlite3.connect(db)
    conn.execute(
        "INSERT INTO species (common_name, scientific_name, light_need, "
        "humidity_pct_min, humidity_pct_max, temp_f_min, temp_f_max, "
        "soil_type, toxic_to_pets, care_notes) VALUES ('Wired', "
        "'Wired wiredus', 'low', 40, 60, 60, 80, 'mix', 0, '')")
    species_id = conn.execute(
        "SELECT id FROM species WHERE scientific_name = 'Wired wiredus'"
    ).fetchone()[0]
    _insert_plant_of(conn, species_id)
    conn.commit()
    conn.close()

    database.run_migrations()   # stamps 0001_baseline, then upgrades to head
    engine.dispose()

    conn = sqlite3.connect(db)
    _assert_head_shape(conn)
    _assert_wired_row_survived(conn)
    info = {r[1]: r for r in conn.execute("PRAGMA table_info(species)")}
    assert info["source"][4] == "'curated'"
    assert info["review_status"][4] == "'approved'"
    assert conn.execute(
        "SELECT source, review_status FROM species "
        "WHERE scientific_name = 'Wired wiredus'").fetchone() == ("curated", "approved")
    assert conn.execute(
        "SELECT version_num FROM alembic_version").fetchone() == (
            "0015_species_claim_wiring",)
    conn.close()


def test_downgrade_refuses_before_touching_anything_while_minted_rows_exist(
        tmp_path: Path, monkeypatch):
    """pysqlite commits DDL as it goes, so a downgrade that failed halfway
    would leave the volume at 0015 with no sync_state table and a stray
    _alembic_tmp_species -- every cold start logging "claim sync skipped"
    until someone hand-writes SQL. The refusal has to come first, and the
    same database has to downgrade cleanly once the minted rows are gone."""
    from alembic import command

    db = tmp_path / "downgrade.db"
    url = f"sqlite:///{db.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", url)
    cfg = _config(url)
    command.upgrade(cfg, "head")
    conn = sqlite3.connect(db)
    _assert_head_shape(conn)   # inserts the claims-minted row
    conn.execute("INSERT INTO sync_state (key, value) VALUES ('tranche_fingerprint', 'f')")
    conn.commit()
    conn.close()

    with pytest.raises(RuntimeError, match="claims-minted"):
        command.downgrade(cfg, "0014_authority_scope")

    conn = sqlite3.connect(db)
    tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    assert "sync_state" in tables and "_alembic_tmp_species" not in tables
    assert conn.execute("SELECT value FROM sync_state").fetchone() == ("f",)
    assert conn.execute("SELECT version_num FROM alembic_version").fetchone() == (
        "0015_species_claim_wiring",)
    conn.execute("DELETE FROM species WHERE source = 'claims'")
    conn.commit()
    conn.close()

    command.downgrade(cfg, "0014_authority_scope")
    conn = sqlite3.connect(db)
    tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    assert "sync_state" not in tables and "_alembic_tmp_species" not in tables
    info = {r[1]: r for r in conn.execute("PRAGMA table_info(species)")}
    assert info["toxic_to_pets"][3] == 1 and "care_sources" not in info
    conn.close()

    command.upgrade(cfg, "head")
    conn = sqlite3.connect(db)
    _assert_head_shape(conn)
    conn.close()
