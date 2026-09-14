"""Migration 0019: the seven fit fields on `species`.

Plain nullable columns, so the interesting assertions are not about the DDL.
They are that `is_houseplant` arrives nullable rather than defaulting to
false — a default there would tell a caretaker that every plant nobody
researched is an outdoor plant — and that all seven come through a downgrade
and back, because they are materialised from `claim` rows and losing them to
a downgrade must cost nothing but a recompute (ADR 0001).
"""
import sqlite3
from pathlib import Path

from alembic import command

from tests.test_migration_0015 import _config
from tests.test_migrations import _upgrade

PREVIOUS = "0018_growing_area_real_estate"
BOOLEANS = ("is_houseplant", "is_edible", "attracts_pollinators")
SIZES = ("mature_height_in_min", "mature_height_in_max",
         "mature_spread_in_min", "mature_spread_in_max")
FIT_FIELDS = BOOLEANS + SIZES

SPECIES_INSERT = (
    "INSERT INTO species (common_name, scientific_name, care_notes, source, "
    "source_ref, review_status, review_note) VALUES ('Hosta', "
    "'Hosta sieboldiana', '', 'claims', 'b1.json', 'approved', '')")


def _columns(conn) -> dict:
    return {r[1]: r for r in conn.execute("PRAGMA table_info(species)")}


def _assert_added(conn) -> None:
    info = _columns(conn)
    for col in FIT_FIELDS:
        assert col in info, f"{col} missing"
        assert info[col][3] == 0, f"{col} must be nullable"
        assert info[col][4] is None, f"{col} must have no default"
    for col in BOOLEANS:
        assert info[col][2] == "BOOLEAN"
    for col in SIZES:
        assert info[col][2] == "FLOAT"
    assert "_alembic_tmp_species" not in {
        r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}


def test_fresh_db_carries_all_seven(tmp_path: Path):
    db = tmp_path / "fresh.db"
    _upgrade(f"sqlite:///{db.as_posix()}")

    conn = sqlite3.connect(db)
    _assert_added(conn)
    conn.close()


def test_an_unresearched_species_is_null_not_false(tmp_path: Path, monkeypatch):
    """`is_houseplant` defaulting to false would say every unresearched plant
    belongs outdoors. Null says nobody looked, which is the truth."""
    db = tmp_path / "at0018.db"
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
    row = conn.execute(
        f"SELECT {', '.join(FIT_FIELDS)} FROM species "
        "WHERE scientific_name = 'Hosta sieboldiana'").fetchone()
    assert row == (None,) * len(FIT_FIELDS)
    conn.close()


def test_a_size_range_round_trips_through_downgrade(tmp_path: Path, monkeypatch):
    db = tmp_path / "roundtrip.db"
    url = f"sqlite:///{db.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", url)
    cfg = _config(url)
    command.upgrade(cfg, "head")

    conn = sqlite3.connect(db)
    conn.execute(SPECIES_INSERT)
    conn.execute(
        "UPDATE species SET is_houseplant = 0, is_edible = 0, "
        "attracts_pollinators = 1, mature_height_in_min = 18, "
        "mature_height_in_max = 36, mature_spread_in_min = 24, "
        "mature_spread_in_max = 48")
    conn.commit()
    assert conn.execute(
        "SELECT mature_height_in_min, mature_height_in_max FROM species"
    ).fetchone() == (18.0, 36.0)
    conn.close()

    command.downgrade(cfg, PREVIOUS)
    conn = sqlite3.connect(db)
    info = _columns(conn)
    assert not any(col in info for col in FIT_FIELDS)
    # The species survives; only the fit values go, and a recompute puts
    # them back from the claims.
    assert conn.execute(
        "SELECT common_name FROM species").fetchone() == ("Hosta",)
    conn.close()

    command.upgrade(cfg, "head")
    conn = sqlite3.connect(db)
    _assert_added(conn)
    assert conn.execute(
        "SELECT attracts_pollinators FROM species").fetchone() == (None,)
    conn.close()
