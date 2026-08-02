"""plant quantity — one row can stand for a planting, not just an individual

Revision ID: 0006_plant_quantity
Revises: 0005_environment_climate
Create Date: 2026-08-01

A houseplant owner names individuals; a gardener counts. "Twelve tomatoes along
the south fence" is one thing to the person who planted it, not twelve, and
storing it as twelve rows makes the plant list, the calendar and the to-do list
unreadable long before the database minds.

`quantity` backfills to 1 via server_default, so **every row that existed
before this migration keeps its exact previous meaning** — an individual, whose
plant_uuid identifies one physical plant and whose stewardship chain answers
"who has cared for *this* plant". Nothing about the houseplant experience
changes.

`split_from_uuid` exists because splitting is the one operation that breaks the
census's dedup assumption. Moving three of twelve tomatoes to another bed has
to mint a second plant_uuid for plants that were previously counted under one —
exactly the double-count plant_uuid was introduced to prevent. Recording where
the new row came from is what lets an aggregator recognise the pair. It is
indexed because that lookup is the whole point of storing it.

Both columns are additive and nullable-or-defaulted, per the SQLite constraint
that has shaped every migration here: you cannot add a NOT NULL column to
existing rows without one.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = "0006_plant_quantity"
down_revision: Union[str, Sequence[str], None] = "0005_environment_climate"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("plant", schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            "quantity", sa.Integer(), nullable=False, server_default="1"))
        batch_op.add_column(sa.Column(
            "split_from_uuid", sqlmodel.sql.sqltypes.AutoString(),
            nullable=True))
        batch_op.create_index(
            "ix_plant_split_from_uuid", ["split_from_uuid"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("plant", schema=None) as batch_op:
        batch_op.drop_index("ix_plant_split_from_uuid")
        batch_op.drop_column("split_from_uuid")
        batch_op.drop_column("quantity")
