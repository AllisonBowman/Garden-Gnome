"""Migration 0021: `pending_apple_revocation`.

A new table and nothing else. What matters is its shape -- an encrypted token
and retry bookkeeping, with no column that could say whose token it was -- and
that a downgrade will not quietly forget a revoke a deleted account is owed.
"""
import sqlite3
from pathlib import Path

import pytest
from alembic import command

from tests.test_migration_0015 import _config
from tests.test_migrations import _upgrade

PREVIOUS = "0020_climbs"


def _columns(conn) -> dict:
    return {r[1]: r for r in conn.execute(
        "PRAGMA table_info(pending_apple_revocation)")}


def test_fresh_db_has_the_queue_and_nothing_in_it_names_a_user(tmp_path: Path):
    db = tmp_path / "fresh.db"
    _upgrade(f"sqlite:///{db.as_posix()}")
    conn = sqlite3.connect(db)
    cols = _columns(conn)
    assert set(cols) == {
        "id", "token_enc", "created_at", "attempts", "last_attempt_at"}
    assert cols["token_enc"][3] == 1 and cols["created_at"][3] == 1
    assert cols["last_attempt_at"][3] == 0
    # No foreign key: the row must outlive the user it came from.
    assert conn.execute(
        "PRAGMA foreign_key_list(pending_apple_revocation)").fetchall() == []
    conn.close()


def test_downgrade_refuses_while_a_revoke_is_waiting(tmp_path: Path, monkeypatch):
    db = tmp_path / "waiting.db"
    url = f"sqlite:///{db.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", url)
    cfg = _config(url)
    command.upgrade(cfg, "head")

    conn = sqlite3.connect(db)
    conn.execute(
        "INSERT INTO pending_apple_revocation (token_enc, created_at) "
        "VALUES ('gAAAA-encrypted', '2026-10-16 00:00:00')")
    conn.commit()
    conn.close()

    with pytest.raises(RuntimeError, match="still waiting"):
        command.downgrade(cfg, PREVIOUS)

    conn = sqlite3.connect(db)
    assert conn.execute(
        "SELECT count(*) FROM pending_apple_revocation").fetchone() == (1,)
    conn.execute("DELETE FROM pending_apple_revocation")
    conn.commit()
    conn.close()

    command.downgrade(cfg, PREVIOUS)
    conn = sqlite3.connect(db)
    assert _columns(conn) == {}
    conn.close()
    command.upgrade(cfg, "head")
