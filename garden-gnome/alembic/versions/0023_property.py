"""property — a piece of land, found by the pin its owner confirmed

Revision ID: 0023_property
Revises: 0022_backfill_acquired_on
Create Date: 2026-11-15

The first migration of the land stewardship overhaul (build spec section 1,
A12: the categorization branch is shelved, so this is 0023). One concern: the
`property` table from PLAN.md section 5.

No street address and no postal code column, on purpose (PLAN.md D8): the
pin the owner confirmed is the stored location. `city`, `region`, `country`
and `timezone` are filled on the server from public data for the pin.
`lot_contents`, `goals` and `profile_status` are JSON; `lot_contents` null
means the owner skipped "What's on your lot?".

Downgrade drops the table. That loses every pin and lot answer an owner
gave; nothing recomputes them. The zones that point at a property keep their
rows (they are growing areas), and 0024's downgrade removes their columns.
"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op


revision: str = "0023_property"
down_revision: Union[str, Sequence[str], None] = "0022_backfill_acquired_on"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "property",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("uuid", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("user_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default=""),
        sa.Column("pin_lat", sa.Float(), nullable=False),
        sa.Column("pin_lng", sa.Float(), nullable=False),
        sa.Column("pin_source", sqlmodel.sql.sqltypes.AutoString(), nullable=False,
                  server_default="owner_pin"),
        sa.Column("city", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("region", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("country", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("timezone", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("lot_contents", sa.JSON(), nullable=True),
        sa.Column("frost_bias", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("goals", sa.JSON(), nullable=True),
        sa.Column("profile_status", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uuid"),
    )
    op.create_index(op.f("ix_property_user_id"), "property", ["user_id"],
                    unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_property_user_id"), table_name="property")
    op.drop_table("property")
