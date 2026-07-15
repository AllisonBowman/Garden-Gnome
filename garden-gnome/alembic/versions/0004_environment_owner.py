"""environment.user_id — per-user growing environments (decision 1)

Revision ID: 0004_environment_owner
Revises: 0003_census_opt_in
Create Date: 2026-07-15

Backfills existing environments to the dev@local user (creating it if the
database predates 0002's backfill, e.g. a fresh-then-seeded DB).

EnvironmentType also gains balcony/greenhouse/other in this release: no DDL
is needed on SQLite (enum values are stored as TEXT with no CHECK
constraint — SQLAlchemy's Enum defaults to create_constraint=False). At the
Postgres move this becomes ALTER TYPE ... ADD VALUE if a native enum is used.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = "0004_environment_owner"
down_revision: Union[str, Sequence[str], None] = "0003_census_opt_in"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("environment", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("user_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True))
        batch_op.create_index(
            batch_op.f("ix_environment_user_id"), ["user_id"], unique=False)
        batch_op.create_foreign_key(
            "fk_environment_user_id", "user", ["user_id"], ["id"])

    # Backfill ownership of pre-auth environments to dev@local.
    from datetime import datetime
    from uuid import uuid4

    conn = op.get_bind()
    orphans = conn.execute(
        sa.text("SELECT COUNT(*) FROM environment WHERE user_id IS NULL")
    ).scalar()
    if orphans:
        row = conn.execute(
            sa.text("SELECT id FROM user WHERE email = 'dev@local'")
        ).fetchone()
        if row:
            dev_id = row[0]
        else:
            dev_id = str(uuid4())
            conn.execute(
                sa.text(
                    "INSERT INTO user (id, email, display_name, created_at, "
                    "census_opt_in) VALUES (:id, 'dev@local', 'Dev User', "
                    ":now, 0)"
                ),
                {"id": dev_id, "now": datetime.utcnow().isoformat(sep=" ")},
            )
        conn.execute(
            sa.text("UPDATE environment SET user_id = :uid WHERE user_id IS NULL"),
            {"uid": dev_id},
        )


def downgrade() -> None:
    with op.batch_alter_table("environment", schema=None) as batch_op:
        batch_op.drop_constraint("fk_environment_user_id", type_="foreignkey")
        batch_op.drop_index(batch_op.f("ix_environment_user_id"))
        batch_op.drop_column("user_id")
