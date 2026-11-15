"""Migrations 0023 to 0031: the land stewardship tables and zone columns.

The overhaul's schema rules (PLAN.md D3, build spec section 2) as tests: one
Alembic head; every change additive; plain ADD COLUMN on `growingarea` with
`property_id` an indexed integer and no database foreign key; and every step
down and back up again on a database shaped like production, with the
automatic "My Home" area, null surfaces and rows from before the auth and
real-estate changes, so nothing an existing person has is touched.
"""
import sqlite3
from pathlib import Path

from alembic import command
from alembic.script import ScriptDirectory

from tests.test_migration_0015 import _config

BEFORE = "0022_backfill_acquired_on"
REVISIONS = [
    "0023_property", "0024_growing_area_zones", "0025_site_reading",
    "0026_forecast_cache", "0027_observed_cell_season",
    "0028_season_event_state", "0029_provider_usage", "0030_geodata_tile",
    "0031_site_override",
]
NEW_TABLES = {
    "property", "site_reading", "forecast_cache", "observed_cell_season",
    "season_event_state", "provider_usage", "geodata_tile", "site_override",
}
ZONE_COLUMNS = {"property_id", "vegetation_type", "boundary_geojson",
                "boundary_source", "is_whole_lot", "leaf_habit", "sun_source"}


def _tables(conn) -> set[str]:
    return {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}


def _area_columns(conn) -> set[str]:
    return {r[1] for r in conn.execute("PRAGMA table_info(growingarea)")}


def _snapshot(conn) -> dict:
    """Every row the 1.1.x app can read, for before-and-after comparison."""
    out = {}
    for table in ("user", "growingarea", "plant", "carelog", "stewardshiprecord"):
        cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})")
                if r[1] not in ZONE_COLUMNS]
        out[table] = conn.execute(
            f"SELECT {', '.join(cols)} FROM {table} ORDER BY rowid").fetchall()
    return out


def _insert(conn, table: str, row: dict) -> None:
    """Insert, giving any other NOT NULL column without a default a neutral
    value of its type, so the test does not depend on every catalog column."""
    row = dict(row)
    for r in conn.execute(f"PRAGMA table_info({table})"):
        name, kind, notnull, default, pk = r[1], (r[2] or "").upper(), r[3], r[4], r[5]
        if name in row or pk or not notnull or default is not None:
            continue
        row[name] = 0 if any(t in kind for t in ("INT", "FLOAT", "REAL", "BOOL", "NUM")) else ""
    conn.execute(
        f"INSERT INTO {table} ({', '.join(row)}) VALUES "
        f"({', '.join('?' for _ in row)})", list(row.values()))


def _seed_production_shape(conn) -> None:
    """Rows as production holds them at 0022."""
    conn.executescript("""
        INSERT INTO user (id, email, display_name, created_at, census_opt_in)
          VALUES ('u-1', 'one@example.com', 'One', '2026-07-20 10:00:00', 0),
                 ('u-2', NULL, NULL, '2026-08-01 09:00:00', 1);
        -- The automatic "My Home" each account gets, with every real-estate
        -- column null, and a legacy area from before 0018 with defaults.
        INSERT INTO growingarea (id, uuid, name, type, user_id, city, region,
            country, lat, lng, shelter, temp_exposure, sun_exposure, surface,
            area_sqft, headroom_in, soil_depth_in, goals, created_at)
          VALUES (1, 'ga-1', 'My Home', 'home', 'u-1', '', '', '', NULL, NULL,
                  'sheltered', 'indoor', 'partial_sun', NULL, NULL, NULL, NULL,
                  NULL, '2026-07-20 10:00:00'),
                 (2, 'ga-2', 'Back porch', 'balcony', 'u-1', 'Austin', 'TX',
                  'US', 30.27, -97.74, 'partial', 'outdoor', 'full_sun', NULL,
                  NULL, NULL, NULL, NULL, '2026-08-02 10:00:00'),
                 (3, 'ga-3', 'My Home', 'home', 'u-2', '', '', '', NULL, NULL,
                  'sheltered', 'indoor', 'partial_sun', 'containers', 4.0,
                  NULL, NULL, '[]', '2026-08-01 09:00:00');
    """)
    species = conn.execute("SELECT id FROM species LIMIT 1").fetchone()
    if species is None:
        _insert(conn, "species", {"common_name": "Test fern",
                                  "scientific_name": "Testus fernus"})
        species = conn.execute("SELECT id FROM species LIMIT 1").fetchone()
    _insert(conn, "plant", {
        "plant_uuid": "p-1", "nickname": "Fern", "species_id": species[0],
        "growing_area_id": 1, "user_id": "u-1", "location": "",
        "maturity_stage": "juvenile", "created_at": "2026-07-21 10:00:00",
        "quantity": 1, "pest_observed_at_acquisition": 0,
        "intake_notes": "", "acquired_on": "2026-07-21"})
    conn.execute(
        "INSERT INTO carelog (plant_id, action, notes, logged_at) "
        "VALUES (1, 'water', '', '2026-07-22 10:00:00')")
    conn.execute(
        "INSERT INTO stewardshiprecord (plant_id, growing_area_id, "
        "installation_uuid, started_at, transfer_notes) "
        "VALUES (1, 1, '', '2026-07-21 10:00:00', '')")
    conn.commit()


def test_one_head_and_the_overhaul_starts_at_0023():
    script = ScriptDirectory.from_config(_config("sqlite://"))
    heads = script.get_heads()
    assert heads == [REVISIONS[-1]], f"more than one Alembic head: {heads}"
    chain = [script.get_revision(r) for r in REVISIONS]
    assert chain[0].down_revision == BEFORE
    for previous, rev in zip(chain, chain[1:]):
        assert rev.down_revision == previous.revision


def test_upgrade_from_0022_and_back_keeps_every_existing_row(tmp_path: Path,
                                                             monkeypatch):
    db = tmp_path / "prodlike.db"
    url = f"sqlite:///{db.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", url)
    cfg = _config(url)
    command.upgrade(cfg, BEFORE)
    conn = sqlite3.connect(db)
    _seed_production_shape(conn)
    before = _snapshot(conn)
    conn.close()

    command.upgrade(cfg, "head")
    conn = sqlite3.connect(db)
    assert NEW_TABLES <= _tables(conn)
    assert ZONE_COLUMNS <= _area_columns(conn)
    assert _snapshot(conn) == before
    # Existing rows are not zones: no property, not the whole lot.
    assert conn.execute(
        "SELECT count(*) FROM growingarea WHERE property_id IS NOT NULL "
        "OR is_whole_lot != 0 OR vegetation_type IS NOT NULL").fetchone() == (0,)
    # property_id is indexed and has no database foreign key (D3).
    indexes = {r[1] for r in conn.execute("PRAGMA index_list(growingarea)")}
    assert "ix_growingarea_property_id" in indexes
    fks = {r[3] for r in conn.execute("PRAGMA foreign_key_list(growingarea)")}
    assert "property_id" not in fks
    # A property and a zone written at head, as the app would.
    conn.execute(
        "INSERT INTO property (uuid, user_id, name, pin_lat, pin_lng, "
        "pin_source, created_at) VALUES ('pr-1', 'u-1', 'My land', 38.9123, "
        "-76.9681, 'owner_pin', '2026-11-15 10:00:00')")
    conn.execute(
        "INSERT INTO growingarea (uuid, name, type, user_id, city, region, "
        "country, shelter, temp_exposure, sun_exposure, created_at, "
        "property_id, is_whole_lot, boundary_source) VALUES ('ga-z', "
        "'Whole lot', 'home', 'u-1', '', '', '', 'exposed', 'outdoor', "
        "'partial_sun', '2026-11-15 10:00:00', 1, 1, 'default')")
    conn.commit()
    conn.close()

    command.downgrade(cfg, BEFORE)
    conn = sqlite3.connect(db)
    assert not (NEW_TABLES & _tables(conn))
    assert not (ZONE_COLUMNS & _area_columns(conn))
    after = _snapshot(conn)
    # The zone row survives as a plain growing area; everything else is as it was.
    assert after["growingarea"][:3] == before["growingarea"]
    assert len(after["growingarea"]) == 4
    for table in ("user", "plant", "carelog", "stewardshiprecord"):
        assert after[table] == before[table], table
    links = conn.execute("PRAGMA foreign_key_list(plant)").fetchall()
    assert any(r[2] == "growingarea" for r in links)
    conn.close()

    command.upgrade(cfg, "head")


def test_each_step_goes_down_and_up_again(tmp_path: Path, monkeypatch):
    db = tmp_path / "steps.db"
    url = f"sqlite:///{db.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", url)
    cfg = _config(url)
    command.upgrade(cfg, "head")
    for previous in reversed([BEFORE] + REVISIONS[:-1]):
        command.downgrade(cfg, previous)
    command.upgrade(cfg, "head")
    for rev in reversed(REVISIONS):
        command.downgrade(cfg, "-1")
        command.upgrade(cfg, "+1")
        command.downgrade(cfg, "-1")
    command.upgrade(cfg, "head")


def test_models_match_the_migrations(tmp_path: Path, monkeypatch):
    """No drift between models.py and what the migrations build."""
    from alembic.autogenerate import compare_metadata
    from alembic.migration import MigrationContext
    from sqlalchemy import create_engine
    from sqlmodel import SQLModel

    import app.db.revocations  # noqa: F401
    import app.models.models  # noqa: F401

    db = tmp_path / "drift.db"
    url = f"sqlite:///{db.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", url)
    command.upgrade(_config(url), "head")
    engine = create_engine(url)
    with engine.connect() as conn:
        diff = compare_metadata(MigrationContext.configure(conn), SQLModel.metadata)
    engine.dispose()

    def touches_new(d) -> bool:
        text = repr(d)
        return any(t in text for t in NEW_TABLES) or any(
            c in text for c in ZONE_COLUMNS)

    assert [d for d in diff if touches_new(d)] == []


def test_observed_seasons_refuse_an_apple_source(tmp_path: Path, monkeypatch):
    import pytest

    db = tmp_path / "apple.db"
    url = f"sqlite:///{db.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", url)
    command.upgrade(_config(url), "head")
    conn = sqlite3.connect(db)
    conn.execute(
        "INSERT INTO observed_cell_season (cell_key, source, season_year, "
        "fetched_at) VALUES ('wx2_3891_-7697', 'ncei_ghcnd', 2026, "
        "'2026-11-15 00:00:00')")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO observed_cell_season (cell_key, source, season_year, "
            "fetched_at) VALUES ('wx2_3891_-7697', 'Apple WeatherKit', 2026, "
            "'2026-11-15 00:00:00')")
    conn.close()
