"""outdoor minimum temperature — the number USDA PLANTS actually publishes

Revision ID: 0016_outdoor_temp_min_f
Revises: 0015_species_claim_wiring
Create Date: 2026-09-10

Migration 0013 added `hardiness_zones` as the one field USDA PLANTS Database
is trusted on. The name was wrong. USDA PLANTS does not publish hardiness
zones at all; those are the USDA ARS Plant Hardiness Zone Map's, a separate
product of a separate agency. What PLANTS' Characteristics data does state
is "Temperature, Minimum (°F)": the lowest outdoor temperature a species is
recorded as tolerating. A column named for a quantity its only permitted
writer never publishes would stay empty forever, or -- worse -- be filled by
hand from somewhere else under that authority's name.

So the column is renamed for what it holds: `outdoor_temp_min_f`, a nullable
Float in degrees Fahrenheit. It is not `chill_damage_f`. That field is the
point at which cold damage begins on a plant in cultivation, resolved from
the extension services like any other care value; this one is a survival
floor, stated by a single authority, and the two can sit tens of degrees
apart on the same species. USDA PLANTS stays scoped to this field alone
(authorities.py), exactly as it was to the old one.

Nothing has ever written `hardiness_zones`: no claim in the verified tranche
names it, and no other authority ever claimed it. The upgrade checks that
before dropping the column and refuses with a plain message if a value turns
up -- a zone list and a temperature are not the same fact, so there is
nothing to carry over, and discovering that something wrote the column by
silently discarding what it wrote is the wrong way to find out.

SQLite cannot drop a column in place under Alembic's batch mode, so this is
one rebuild of `species`, the same shape 0015 already proved safe. Downgrade
reverses the swap. Values in `outdoor_temp_min_f` go with the column, and
that loses nothing: the column is materialised from `claim` rows by the
recompute (ADR 0001), so upgrading again puts every value back.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0016_outdoor_temp_min_f"
down_revision: Union[str, Sequence[str], None] = "0015_species_claim_wiring"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SQLAlchemy's JSON type persists an explicit Python None as the text
    # 'null' rather than SQL NULL, so both spellings of nothing count as
    # nothing here.
    written = op.get_bind().execute(sa.text(
        "SELECT count(*) FROM species WHERE hardiness_zones IS NOT NULL "
        "AND hardiness_zones != 'null'")).scalar()
    if written:
        raise RuntimeError(
            f"0016 cannot drop species.hardiness_zones: {written} row(s) hold "
            "a value, and nothing was ever permitted to write one. Find out "
            "what did before migrating.")
    with op.batch_alter_table("species") as batch_op:
        batch_op.drop_column("hardiness_zones")
        batch_op.add_column(
            sa.Column("outdoor_temp_min_f", sa.Float(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("species") as batch_op:
        batch_op.drop_column("outdoor_temp_min_f")
        batch_op.add_column(
            sa.Column("hardiness_zones", sa.JSON(), nullable=True))
