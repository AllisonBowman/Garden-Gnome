"""eaten_parts — the parts a source names as eaten, so eating can be described

Revision ID: 0023_eaten_parts
Revises: 0022_backfill_acquired_on
Create Date: 2026-11-01

Until now the catalog said one thing about eating a plant: `is_edible`, a
boolean, with a sentence of conditions derived beside it. The growing-area
list that asked for "Something to eat" answered from that boolean, and the
line it drew was unclear: every food crop the toxicity table knows landed as
unknown, because a crop always carries a note; chives and oregano sat beside
monstera because a source flags them for pets; and "not grown to eat" meant
"a source calls it poisonous", which the hazard sentence already said.

ADR 0011 makes eating a cited description instead of a verdict. `eaten_parts`
holds the parts a source names as eaten, from a fixed vocabulary
(models.EatenPart: leaves, fruit, seeds, roots, flowers, stems). It is minted
from the edibility passages the tranche already quotes, so for most species
recorded as eaten the quote was there and no page was fetched. The candidate
list groups by it, and one line says the parts with their condition and the
hazards recorded beside them.

Harm-capable like `is_edible` (ADR 0008): never borrowed from the genus,
never resolved through a disagreement. Nullable, no default, because a
default of an empty list would say nothing is eaten of every plant nobody
asked about. JSON, like `outdoor_sun_exposure`, because a plant can be eaten
for more than one part. Materialised from claims like the rest, so a
downgrade drops the column and loses nothing a recompute cannot put back
(ADR 0001). RESOLVER_VERSION goes to "7" in the same change.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0023_eaten_parts"
down_revision: Union[str, Sequence[str], None] = "0022_backfill_acquired_on"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("species", schema=None) as batch_op:
        batch_op.add_column(sa.Column("eaten_parts", sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("species", schema=None) as batch_op:
        batch_op.drop_column("eaten_parts")
