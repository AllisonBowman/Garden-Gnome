"""forecast_cache — a three-hour forecast cache that survives a restart

Revision ID: 0026_forecast_cache
Revises: 0025_site_reading
Create Date: 2026-11-15

One concern: `forecast_cache` (PLAN.md section 5). Today's weather cache is
in memory and lasts an hour (`services/weather.py`); this one is keyed by a
text cell key, never floating point, and each row expires after 3 hours. It
is the only Apple WeatherKit data the server may hold (D10), so nothing here
is accumulated into a history.

Downgrade drops the table; a cache loses nothing.
"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op


revision: str = "0026_forecast_cache"
down_revision: Union[str, Sequence[str], None] = "0025_site_reading"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "forecast_cache",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cell_key", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("provider", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=False), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cell_key", "provider"),
    )
    op.create_index(op.f("ix_forecast_cache_cell_key"), "forecast_cache",
                    ["cell_key"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_forecast_cache_cell_key"), table_name="forecast_cache")
    op.drop_table("forecast_cache")
