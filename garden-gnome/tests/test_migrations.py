"""Migration acceptance tests.

Fresh-DB path: alembic upgrade head builds the full schema (Phase 1).
Pre-auth-DB path: a database with plants but no user table adopts the auth
migration and every plant is backfilled to the dev@local user (Phase 2).
"""
import sqlite3
from pathlib import Path

from tests.conftest import ROOT


def _upgrade(url: str) -> None:
    import os

    from alembic import command
    from alembic.config import Config

    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    prev = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = url
    try:
        command.upgrade(cfg, "head")
    finally:
        if prev is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = prev


def test_fresh_db_reaches_full_schema(tmp_path: Path):
    db = tmp_path / "fresh.db"
    _upgrade(f"sqlite:///{db.as_posix()}")

    conn = sqlite3.connect(db)
    tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"user", "authidentity", "refreshtoken", "plant", "species",
            "carelog", "careschedule", "environment", "speciestrait",
            "stewardshiprecord", "alembic_version"} <= tables

    plant_cols = {r[1] for r in conn.execute("PRAGMA table_info(plant)")}
    assert "user_id" in plant_cols
    conn.close()


def test_preauth_db_backfills_dev_user(tmp_path: Path):
    """Simulate the real cutover: a database stamped at baseline with existing
    plants, then upgraded to head — plants must land on the dev@local user."""
    import os

    from alembic import command
    from alembic.config import Config

    db = tmp_path / "preauth.db"
    url = f"sqlite:///{db.as_posix()}"

    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)

    prev = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = url
    try:
        # Build the pre-auth schema only, and give it data
        command.upgrade(cfg, "0001_baseline")
        conn = sqlite3.connect(db)
        conn.execute(
            "INSERT INTO species (common_name, scientific_name, light_need, "
            "humidity_pct_min, humidity_pct_max, temp_f_min, temp_f_max, "
            "soil_type, toxic_to_pets, care_notes, source, source_ref, "
            "review_status, review_note) VALUES ('S', 'S s', 'LOW', 40, 60, "
            "60, 80, 'mix', 0, '', 'CURATED', '', 'APPROVED', '')")
        conn.execute(
            "INSERT INTO plant (plant_uuid, nickname, species_id, location, "
            "maturity_stage, created_at, pest_observed_at_acquisition, "
            "intake_notes) VALUES ('u-1', 'Old Plant', 1, '', 'JUVENILE', "
            "'2026-01-01 00:00:00', 0, '')")
        conn.commit()
        conn.close()

        # The auth migration must adopt the existing rows
        command.upgrade(cfg, "head")
    finally:
        if prev is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = prev

    conn = sqlite3.connect(db)
    users = conn.execute("SELECT id, email FROM user").fetchall()
    assert len(users) == 1
    assert users[0][1] == "dev@local"

    owner = conn.execute(
        "SELECT user_id FROM plant WHERE nickname = 'Old Plant'").fetchone()[0]
    assert owner == users[0][0]
    conn.close()
