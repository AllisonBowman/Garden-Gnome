"""care outcome — a check is a result, not a chore ticked off

Revision ID: 0008_care_outcome
Revises: 0007_shade_light
Create Date: 2026-08-08

The watering verb is becoming *check*: the reminder asks you to put a finger
in the soil, and "still damp" is a success, not a skipped task. That result
has to live somewhere, so care logs grow an `outcome` — watered /
checked_not_needed for water, repotted / top_dressed / checked_fine for the
seasonal repot inspection.

Nullable, and never backfilled: a null outcome means the row predates
outcomes and the action was simply done. Inventing outcomes for historical
rows would be fabricating records in a column whose whole reason to exist is
honesty about what actually happened.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0008_care_outcome"
down_revision: Union[str, Sequence[str], None] = "0007_shade_light"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("carelog", schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            "outcome",
            sa.Enum(
                "watered", "checked_not_needed", "repotted", "top_dressed",
                "checked_fine", name="careoutcome",
            ),
            nullable=True,
        ))


def downgrade() -> None:
    with op.batch_alter_table("carelog", schema=None) as batch_op:
        batch_op.drop_column("outcome")
