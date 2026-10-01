"""climbs — whether a species is a climber, so its height can mean reach

Revision ID: 0020_climbs
Revises: 0019_fit_fields
Create Date: 2026-10-01

0019 gave every species a mature height and spread. For a tree or a shrub
that number is its stature, and the fit engine compares it against a space's
headroom. For a climber the same published figure means something else: NC
State's "Height: 30 ft. 0 in. - 50 ft. 0 in." for Virginia Creeper is how far
the vine runs along whatever it is given, not how tall it stands on its own.

The size backfill could not tell the two apart. Two auditors read the
identical field opposite ways on two vines, so from wave 1 chunk 4 onward a
climber took no size at all -- about fifty species left sizeless by rule,
including the wisterias, the ivies, the pothos group and the vegetable vines.
That was a holding position, and the gardener most in need of a size warning
is the one about to plant a 40 ft wisteria against a 7 ft fence.

So the field gets a qualifier rather than a second column. `climbs` is a
cited claim like any other fit field ("Habit/Form: Climbing", "a twining
vine"); where it is true, `mature_height_in_*` is the reach the source
publishes, and the fit engine and the care facts say "climbs to" instead of
"reaches". Nothing about the stored inches changes meaning for a non-climber.

Not harm-capable: a wrongly flagged climber is described with the wrong verb,
nothing worse. Nullable, no default, because a default of false would say
every unresearched plant stands on its own. Materialised from claims like the
rest, so a downgrade drops the column and loses nothing a recompute cannot
put back (ADR 0001). RESOLVER_VERSION goes to "5" in the same change.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0020_climbs"
down_revision: Union[str, Sequence[str], None] = "0019_fit_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("species", schema=None) as batch_op:
        batch_op.add_column(sa.Column("climbs", sa.Boolean(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("species", schema=None) as batch_op:
        batch_op.drop_column("climbs")
