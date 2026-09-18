"""growing area real estate — the surface, its size, and what it is for

Revision ID: 0018_growing_area_real_estate
Revises: 0017_growing_area
Create Date: 2026-09-14

0017 gave the concept its name; this gives it something to describe. Five
columns, and every one of them nullable on purpose.

`shelter`, `temp_exposure` and `sun_exposure` were added in 0005 with server
defaults, because a default there is harmless: an area whose owner never
touched the toggles really is indoors and sheltered more often than not, and
the worst case is a slightly wrong weather sentence. These five are different.
They are about to decide which species get recommended for a space, and a
default there would be an invented measurement -- "your bed is 1 square foot"
is not a safe guess, it is a wrong answer that looks like an answer. So an
area that has not been asked carries NULL, the fit engine reads NULL as
`unknown`, and `unknown` never counts as a fit.

  surface        what a plant would actually sit in: bed, container, sill.
                 TEXT holding a GrowingSurface value, same storage as the
                 0005 enums.
  area_sqft      the footprint available.
  headroom_in    how tall something may get here before it is a problem.
  soil_depth_in  bed or container depth -- the root run.
  goals          JSON list of GrowingGoal values. NULL means never asked;
                 [] means asked and the answer was "nothing in particular".
                 The two are not the same and the engine treats them
                 differently, so the column is not defaulted to [].

Downgrade drops all five. That loses what the owner typed, and nothing
recomputes it -- unlike a species column, which the claims can always
rematerialise (ADR 0001), this is somebody's description of their own garden.
Worth saying out loud before anyone runs it.
"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op


revision: str = "0018_growing_area_real_estate"
down_revision: Union[str, Sequence[str], None] = "0017_growing_area"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("growingarea", schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            "surface", sqlmodel.sql.sqltypes.AutoString(), nullable=True))
        batch_op.add_column(sa.Column("area_sqft", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("headroom_in", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("soil_depth_in", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("goals", sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("growingarea", schema=None) as batch_op:
        batch_op.drop_column("goals")
        batch_op.drop_column("soil_depth_in")
        batch_op.drop_column("headroom_in")
        batch_op.drop_column("area_sqft")
        batch_op.drop_column("surface")
