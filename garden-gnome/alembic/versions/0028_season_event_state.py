"""season_event_state — what the owner said about each seasonal event

Revision ID: 0028_season_event_state
Revises: 0027_observed_cell_season
Create Date: 2026-11-15

One concern: `season_event_state` (PLAN.md section 5). The seasonal plan is
computed on every request; this table is what lets "done", "not needed" and
"it happened" survive that. `event_key` holds type, season year and stage.
Unique on property, zone and event key, through an index on
`coalesce(zone_id, 0)`: the plan writes whole-lot rows with a null zone, and
SQLite treats nulls as distinct, so a plain unique constraint would let two
rows for one event in. `observed_on` is the day the owner said it happened,
when they gave one (build spec section 4).

Downgrade drops the table, and with it every tick an owner made.
"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op


revision: str = "0028_season_event_state"
down_revision: Union[str, Sequence[str], None] = "0027_observed_cell_season"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "season_event_state",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("property_id", sa.Integer(), nullable=False),
        sa.Column("zone_id", sa.Integer(), nullable=True),
        sa.Column("event_key", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("band", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("provider_name", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("observed_on", sa.Date(), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_season_event_state_property_id"),
                    "season_event_state", ["property_id"], unique=False)
    op.create_index("uq_season_event_state_key", "season_event_state",
                    ["property_id", sa.text("coalesce(zone_id, 0)"), "event_key"],
                    unique=True)


def downgrade() -> None:
    op.drop_index("uq_season_event_state_key", table_name="season_event_state")
    op.drop_index(op.f("ix_season_event_state_property_id"),
                  table_name="season_event_state")
    op.drop_table("season_event_state")
