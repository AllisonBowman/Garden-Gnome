"""provider_usage — calls made to a metered provider each month

Revision ID: 0029_provider_usage
Revises: 0028_season_event_state
Create Date: 2026-11-15

One concern: `provider_usage` (PLAN.md section 5), the Apple WeatherKit call
counter, one row per provider per month ("2026-11").

Downgrade drops the table; the month's count starts again from zero.
"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op


revision: str = "0029_provider_usage"
down_revision: Union[str, Sequence[str], None] = "0028_season_event_state"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "provider_usage",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("provider", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("month", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("calls", sa.Integer(), nullable=False,
                  server_default=sa.text("0")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "month"),
    )


def downgrade() -> None:
    op.drop_table("provider_usage")
