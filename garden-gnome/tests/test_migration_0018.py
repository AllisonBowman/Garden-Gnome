"""Migration 0018: the growing area's real estate columns.

Five nullable columns, and the test that matters is the one about NULL. These
decide which species get recommended, so an area nobody has measured has to
come through the migration with nothing in them -- not a zero, not an empty
list, not a plausible default. A guessed dimension would read downstream as a
measurement somebody took.
"""
import sqlite3
from pathlib import Path

from alembic import command

from tests.test_migration_0015 import _config
from tests.test_migrations import _upgrade

PREVIOUS = "0017_growing_area"
REAL_ESTATE = ("surface", "area_sqft", "headroom_in", "soil_depth_in", "goals")

AREA_INSERT = (
    "INSERT INTO growingarea (uuid, name, type, city, region, country, "
    "shelter, temp_exposure, sun_exposure, created_at) VALUES "
    "('u-sill', 'Kitchen sill', 'home', '', '', '', 'sheltered', 'indoor', "
    "'partial_sun', '2026-01-01 00:00:00')")


def _columns(conn) -> dict:
    return {r[1]: r for r in conn.execute("PRAGMA table_info(growingarea)")}


def _assert_added(conn) -> None:
    info = _columns(conn)
    for col in REAL_ESTATE:
        assert col in info, f"{col} missing"
        assert info[col][3] == 0, f"{col} must be nullable"
        assert info[col][4] is None, f"{col} must have no default, got {info[col][4]!r}"
    assert info["area_sqft"][2] == "FLOAT"
    assert conn.execute("PRAGMA foreign_key_check").fetchall() == []


def test_fresh_db_has_the_real_estate_columns_and_no_defaults(tmp_path: Path):
    db = tmp_path / "fresh.db"
    _upgrade(f"sqlite:///{db.as_posix()}")

    conn = sqlite3.connect(db)
    _assert_added(conn)
    conn.close()


def test_an_existing_area_comes_through_unmeasured(tmp_path: Path, monkeypatch):
    """An area that predates the feature has not been asked, and must say so."""
    db = tmp_path / "at0017.db"
    url = f"sqlite:///{db.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", url)
    cfg = _config(url)
    command.upgrade(cfg, PREVIOUS)

    conn = sqlite3.connect(db)
    conn.execute(AREA_INSERT)
    conn.commit()
    conn.close()

    command.upgrade(cfg, "head")

    conn = sqlite3.connect(db)
    _assert_added(conn)
    row = conn.execute(
        f"SELECT {', '.join(REAL_ESTATE)} FROM growingarea "
        "WHERE name = 'Kitchen sill'").fetchone()
    assert row == (None,) * len(REAL_ESTATE), (
        "an unmeasured area must arrive unmeasured, not defaulted")
    conn.close()


def test_goals_keeps_never_asked_apart_from_asked_and_nothing(
        tmp_path: Path, monkeypatch):
    """NULL and [] are different answers and the column has to hold both."""
    db = tmp_path / "goals.db"
    url = f"sqlite:///{db.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", url)
    cfg = _config(url)
    command.upgrade(cfg, "head")

    conn = sqlite3.connect(db)
    conn.execute(AREA_INSERT)
    conn.execute(
        AREA_INSERT.replace("u-sill", "u-bed").replace("Kitchen sill", "Back bed"))
    conn.execute("UPDATE growingarea SET goals = '[]' WHERE name = 'Back bed'")
    conn.execute(
        "UPDATE growingarea SET surface = 'raised_bed', area_sqft = 32.0, "
        "headroom_in = 84.0, soil_depth_in = 12.0 WHERE name = 'Back bed'")
    conn.commit()

    assert conn.execute(
        "SELECT goals FROM growingarea WHERE name = 'Kitchen sill'"
    ).fetchone() == (None,)
    assert conn.execute(
        "SELECT goals FROM growingarea WHERE name = 'Back bed'").fetchone() == ("[]",)
    assert conn.execute(
        "SELECT surface, area_sqft FROM growingarea WHERE name = 'Back bed'"
    ).fetchone() == ("raised_bed", 32.0)
    conn.close()


def test_downgrade_drops_them_and_upgrade_puts_them_back(
        tmp_path: Path, monkeypatch):
    db = tmp_path / "roundtrip.db"
    url = f"sqlite:///{db.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", url)
    cfg = _config(url)
    command.upgrade(cfg, "head")

    conn = sqlite3.connect(db)
    conn.execute(AREA_INSERT)
    conn.execute("UPDATE growingarea SET surface = 'windowsill', headroom_in = 18.0")
    conn.commit()
    conn.close()

    command.downgrade(cfg, PREVIOUS)
    conn = sqlite3.connect(db)
    info = _columns(conn)
    assert not any(col in info for col in REAL_ESTATE)
    # The area itself survives -- only its measurements are gone.
    assert conn.execute(
        "SELECT name FROM growingarea").fetchone() == ("Kitchen sill",)
    conn.close()

    command.upgrade(cfg, "head")
    conn = sqlite3.connect(db)
    _assert_added(conn)
    assert conn.execute(
        "SELECT surface, headroom_in FROM growingarea").fetchone() == (None, None)
    conn.close()
