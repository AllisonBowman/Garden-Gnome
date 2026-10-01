"""Migration 0017: `environment` becomes `growingarea`.

A pure rename, which is exactly why it needs testing: the one thing that can
go wrong is silent. SQLite rewrites a referencing table's foreign key when the
referenced table is renamed, and if it ever stopped doing that the symptom
would not be an error -- it would be every plant quietly detached from the
place it grows in. So the link is followed through the rename, in both
directions, with a real row on the other end.
"""
import sqlite3
from pathlib import Path

from alembic import command

from tests.test_migration_0015 import _config, _insert_plant_of
from tests.test_migrations import _upgrade, head_revision

PREVIOUS = "0016_outdoor_temp_min_f"

SPECIES_INSERT = (
    "INSERT INTO species (common_name, scientific_name, care_notes, source, "
    "source_ref, review_status, review_note) VALUES ('Hosta', "
    "'Hosta sieboldiana', '', 'claims', 'b1.json', 'approved', '')")


def _tables(conn) -> set:
    return {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}


def _columns(conn, table: str) -> set:
    return {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}


def _fk_targets(conn, table: str) -> set:
    return {r[2] for r in conn.execute(f"PRAGMA foreign_key_list({table})")}


def _indexes(conn, table: str) -> set:
    return {r[1] for r in conn.execute(f"PRAGMA index_list({table})")}


def _assert_renamed(conn) -> None:
    tables = _tables(conn)
    assert "growingarea" in tables and "environment" not in tables
    for referrer in ("plant", "stewardshiprecord"):
        cols = _columns(conn, referrer)
        assert "growing_area_id" in cols, f"{referrer} kept the old column"
        assert "environment_id" not in cols
        assert "growingarea" in _fk_targets(conn, referrer)
    assert "ix_growingarea_user_id" in _indexes(conn, "growingarea")
    assert "ix_environment_user_id" not in _indexes(conn, "growingarea")
    assert conn.execute("PRAGMA foreign_key_check").fetchall() == []


def _at_previous(tmp_path: Path, monkeypatch, name: str):
    db = tmp_path / name
    url = f"sqlite:///{db.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", url)
    cfg = _config(url)
    command.upgrade(cfg, PREVIOUS)
    return db, cfg


def _plant_in_an_area(conn) -> None:
    """A plant standing in a growing area, under the pre-rename names."""
    conn.execute(SPECIES_INSERT)
    species_id = conn.execute(
        "SELECT id FROM species WHERE scientific_name = 'Hosta sieboldiana'"
    ).fetchone()[0]
    conn.execute(
        "INSERT INTO environment (uuid, name, type, city, region, country, "
        "shelter, temp_exposure, sun_exposure, created_at) VALUES "
        "('u-bed', 'Back bed', 'home', '', '', '', 'exposed', 'outdoor', "
        "'full_sun', '2026-01-01 00:00:00')")
    env_id = conn.execute(
        "SELECT id FROM environment WHERE name = 'Back bed'").fetchone()[0]
    _insert_plant_of(conn, species_id)
    conn.execute("UPDATE plant SET environment_id = ? WHERE nickname = 'Wired'",
                 (env_id,))
    conn.execute(
        "INSERT INTO stewardshiprecord (plant_id, environment_id, "
        "installation_uuid, started_at, transfer_notes) SELECT id, ?, 'inst', "
        "'2026-01-01 00:00:00', '' FROM plant WHERE nickname = 'Wired'",
        (env_id,))
    conn.commit()


def test_fresh_db_has_growing_areas_and_no_environments(tmp_path: Path):
    db = tmp_path / "fresh.db"
    _upgrade(f"sqlite:///{db.as_posix()}")

    conn = sqlite3.connect(db)
    _assert_renamed(conn)
    conn.close()


def test_a_plant_keeps_its_area_across_the_rename(tmp_path: Path, monkeypatch):
    db, cfg = _at_previous(tmp_path, monkeypatch, "at0016.db")
    conn = sqlite3.connect(db)
    _plant_in_an_area(conn)
    conn.close()

    command.upgrade(cfg, "head")

    conn = sqlite3.connect(db)
    _assert_renamed(conn)
    assert conn.execute("SELECT version_num FROM alembic_version").fetchone() == (
        head_revision(),)
    # The join is the point: the plant still stands in the same named place.
    assert conn.execute(
        "SELECT g.name FROM plant p JOIN growingarea g ON g.id = p.growing_area_id "
        "WHERE p.nickname = 'Wired'").fetchone() == ("Back bed",)
    assert conn.execute(
        "SELECT g.name FROM stewardshiprecord s "
        "JOIN growingarea g ON g.id = s.growing_area_id").fetchone() == ("Back bed",)
    conn.close()


def test_downgrade_puts_every_name_back_with_the_link_intact(
        tmp_path: Path, monkeypatch):
    db, cfg = _at_previous(tmp_path, monkeypatch, "roundtrip.db")
    conn = sqlite3.connect(db)
    _plant_in_an_area(conn)
    conn.close()

    command.upgrade(cfg, "head")
    command.downgrade(cfg, PREVIOUS)

    conn = sqlite3.connect(db)
    tables = _tables(conn)
    assert "environment" in tables and "growingarea" not in tables
    assert "environment_id" in _columns(conn, "plant")
    assert "environment" in _fk_targets(conn, "plant")
    assert "ix_environment_user_id" in _indexes(conn, "environment")
    assert conn.execute(
        "SELECT e.name FROM plant p JOIN environment e ON e.id = p.environment_id "
        "WHERE p.nickname = 'Wired'").fetchone() == ("Back bed",)
    conn.close()

    # And forward again -- a rename that only survives one direction is a trap.
    command.upgrade(cfg, "head")
    conn = sqlite3.connect(db)
    _assert_renamed(conn)
    assert conn.execute("SELECT count(*) FROM growingarea").fetchone() == (1,)
    conn.close()
