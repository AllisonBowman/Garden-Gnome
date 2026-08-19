"""authority scope — trust the row, not the registry, for what an authority may claim

Revision ID: 0014_authority_scope
Revises: 0013_hardiness_zones
Create Date: 2026-08-18

USDA PLANTS Database is tier 1 but scoped to hardiness_zones alone -- it does
not track most of this catalog and its Characteristics schema measures
rangeland establishment, not potted care. `tranche.py` already refuses to
write a claim outside an authority's scope. This closes the matching gap at
read time: `authority.allowed_fields` is now a stored fact, checked when
claims are loaded for resolution, rather than a name re-looked-up against the
live `authorities.py` registry.

That distinction matters for the same reason tier and licence are stored
facts and not recalled from the registry (ADR 0001) -- `withdraw_authority`
works by deleting rows precisely because standing is what is in the database,
not what the registry currently says. Checking scope against the live
registry at read time would have made resolution silently depend on the
current state of a Python module instead of what was actually granted when
the row was created.

Additive. Null means unrestricted, so every existing Authority row keeps
today's behaviour with no repair.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0014_authority_scope"
down_revision: Union[str, Sequence[str], None] = "0013_hardiness_zones"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "authority", sa.Column("allowed_fields", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("authority", "allowed_fields")
