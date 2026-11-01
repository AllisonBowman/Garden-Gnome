"""pending_apple_revocation — a failed Apple revoke can be tried again

Revision ID: 0021_pending_apple_revocation
Revises: 0020_climbs
Create Date: 2026-10-16

Deleting an account revokes its Sign in with Apple grant, and the only thing
that revoke needs is the encrypted refresh token stored on `authidentity`.
DELETE /me removed that row in the same transaction it tried the revoke in,
so when Apple was unreachable the log said "retry the revoke out of band"
about a token that no longer existed anywhere.

This table holds the token through the deletion instead: copied off the
identity, still encrypted, with no user id or email beside it, and deleted
the moment Apple accepts the revoke. `attempts` and `last_attempt_at` drive
the retry's backoff (app/routers/auth.py).

A new table and nothing else; no existing row is read or changed. Downgrade
drops it, and with it any revoke still waiting, which is why it refuses to
while one is.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0021_pending_apple_revocation"
down_revision: Union[str, Sequence[str], None] = "0020_climbs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "pending_apple_revocation",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("token_enc", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False,
                  server_default=sa.text("0")),
        sa.Column("last_attempt_at", sa.DateTime(timezone=False), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    waiting = op.get_bind().execute(sa.text(
        "SELECT count(*) FROM pending_apple_revocation")).scalar()
    if waiting:
        raise RuntimeError(
            f"0021 cannot be downgraded while {waiting} Apple revoke(s) are "
            "still waiting: dropping the table would forget grants a deleted "
            "account asked to have revoked")
    op.drop_table("pending_apple_revocation")
