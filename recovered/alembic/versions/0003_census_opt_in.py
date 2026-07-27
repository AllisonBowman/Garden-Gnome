"""user.census_opt_in — per-user census consent, default false

Revision ID: 0003_census_opt_in
Revises: 0002_auth
Create Date: 2026-07-15

Privacy decision (2026-07-15): census participation is opt-in per user.
Existing rows (including dev@local) default to NOT opted in.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003_census_opt_in"
down_revision: Union[str, Sequence[str], None] = "0002_auth"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "census_opt_in",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("0"),
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_column("census_opt_in")
