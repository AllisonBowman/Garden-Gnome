"""observed_cell_season — observed freezes from open government data

Revision ID: 0027_observed_cell_season
Revises: 0026_forecast_cache
Create Date: 2026-11-15

One concern: `observed_cell_season` (PLAN.md section 5), what was observed in
a cell or at a station over one season (first freeze, killing freeze).
Open government data only: a check constraint refuses any row whose source
names Apple or WeatherKit, because Apple's terms bar a stored history (D10).

Downgrade drops the table; every row can be fetched again.
"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op


revision: str = "0027_observed_cell_season"
down_revision: Union[str, Sequence[str], None] = "0026_forecast_cache"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "observed_cell_season",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cell_key", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("station_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("source", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("season_year", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=False), nullable=False),
        sa.CheckConstraint(
            "lower(source) NOT LIKE '%apple%' AND "
            "lower(source) NOT LIKE '%weatherkit%'",
            name="ck_observed_cell_season_not_apple"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cell_key", "station_id", "source", "season_year"),
    )
    op.create_index(op.f("ix_observed_cell_season_cell_key"),
                    "observed_cell_season", ["cell_key"], unique=False)
    op.create_index(op.f("ix_observed_cell_season_station_id"),
                    "observed_cell_season", ["station_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_observed_cell_season_station_id"),
                  table_name="observed_cell_season")
    op.drop_index(op.f("ix_observed_cell_season_cell_key"),
                  table_name="observed_cell_season")
    op.drop_table("observed_cell_season")
