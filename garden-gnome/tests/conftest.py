"""Shared test fixtures.

Each test session gets its own SQLite file brought to alembic head, so tests
exercise the real migrations rather than create_all. Required auth settings
are injected before any app module import.
"""
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Must be set before app.config / app.db.database are imported anywhere.
os.environ.setdefault(
    "JWT_SECRET", "test-secret-not-for-production-0123456789abcdef")
os.environ.setdefault(
    "FERNET_KEY", "3xNZZ39kIYYjBTGoTUdBjPIHpBTHQniku9UYc9pRcNo="  # test-only key
)
# Provider config for Phase 4 verification tests (mocked JWKS, no live calls)
os.environ.setdefault("APPLE_BUNDLE_ID", "com.allisonbowman.plantadvocate")
os.environ.setdefault("APPLE_TEAM_ID", "TESTTEAM99")
os.environ.setdefault("APPLE_KEY_ID", "TESTKEY123")
os.environ.setdefault("GOOGLE_CLIENT_ID", "test-client.apps.googleusercontent.com")


@pytest.fixture(autouse=True)
def _rate_limiting_off():
    """Rate limiting is exercised only by its dedicated test — everywhere
    else the shared 'testclient' IP would trip limits across test modules."""
    from app.rate_limit import limiter
    limiter.enabled = False
    yield
    limiter.enabled = False


@pytest.fixture(scope="session")
def migrated_db_url(tmp_path_factory) -> str:
    """A fresh SQLite database at alembic head, shared by the session."""
    db_path = tmp_path_factory.mktemp("db") / "test_garden_gnome.db"
    url = f"sqlite:///{db_path.as_posix()}"

    from alembic import command
    from alembic.config import Config

    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    # env.py prefers DATABASE_URL; pin it for the upgrade then restore.
    prev = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = url
    try:
        command.upgrade(cfg, "head")
    finally:
        if prev is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = prev
    return url


@pytest.fixture()
def session(migrated_db_url):
    """A SQLModel session on the migrated test database, rolled back per test."""
    from sqlmodel import Session, create_engine

    engine = create_engine(
        migrated_db_url, connect_args={"check_same_thread": False}
    )
    with Session(engine) as s:
        yield s
        s.rollback()
    engine.dispose()
