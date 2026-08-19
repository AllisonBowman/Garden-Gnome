"""hardiness zones — the one thing USDA PLANTS is actually authoritative on

Revision ID: 0013_hardiness_zones
Revises: 0012_care_provenance
Create Date: 2026-08-18

USDA PLANTS Database was investigated as a general care-data source and
rejected: most of this catalog does not appear in it at all, and where a
species does, its Characteristics schema measures rangeland-establishment
traits, not potted-plant care. But it is a federal work (public domain, no
attribution constraint) and it is the authority on one thing this catalog
has never had a field for -- which USDA cold-hardiness zones a species
tolerates outdoors.

`hardiness_zones` is a JSON array of zone numbers, e.g. [7, 8, 9, 10]. Most
rows will stay null: the catalog is majority indoor houseplants, which have
no outdoor hardiness zone to speak of, and null here is the correct answer,
not a gap to fill.

Only USDA PLANTS Database may write this field -- enforced in
authorities.py's `authority_may_claim`, not by convention. A citation from
any other vetted publisher naming `hardiness_zones` is reported unsupported
rather than loaded, the same as an unvetted domain would be.

Purely additive. Downgrade drops the column only.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0013_hardiness_zones"
down_revision: Union[str, Sequence[str], None] = "0012_care_provenance"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "species", sa.Column("hardiness_zones", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("species", "hardiness_zones")
