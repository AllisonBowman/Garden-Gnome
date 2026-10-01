"""fit fields — what a species needs before a space can be matched to it

Revision ID: 0019_fit_fields
Revises: 0018_growing_area_real_estate
Create Date: 2026-09-14

0018 let a gardener describe the space. These are the columns on the other
side of that comparison — the facts about a species that decide whether it
belongs in it. Seven, in three groups.

`is_houseplant` is not new information. Every researcher has been recording
it since b1 and 507 of the 600 records carry a citation whose text names it,
but it sat in `NOT_A_FIELD` as bookkeeping, so nothing ever became a Claim and
no column ever held it. It is promoted here: the same string-containment
pairing that supports every other field already supports this one, and it is
the best-covered thing the catalog knows about where a plant can live. The 93
records whose citations do not name it simply stay null — that is the pairing
working, not failing.

`is_edible` and `attracts_pollinators` are new, and empty on arrival. The
extension services publish both on their species pages; nothing in the
existing corpus cites either, so these fill in as batches are re-researched.

`mature_height_in_*` and `mature_spread_in_*` are the size pair, and the
reason the whole feature needed a catalog pass. Nothing in the catalog has
ever recorded how big a plant gets. Min and max rather than one number,
because that is how the sources publish it -- "3 to 6 feet" -- and because
collapsing a range to a point makes the researcher choose an end and hides
that they did. Stored in inches; the tranche loader's STEMS entry lets one
citation reading `mature_height_in 36-72` support both bounds, exactly as
`day_f` already does for the temperature pair.

None of the seven is harm-capable. A wrong height crowds a border; it does not
kill an animal or leave a plant out on the freezing night. So they resolve
through disagreement by tier like any ordinary field, and they may be borrowed
from the genus -- which for mature size is not a concession but the right
default, since congeners are far more alike in size than in toxicity. A
borrowed value still carries its label wherever it is shown (ADR 0002).

Nullable, no defaults, no backfill. `RESOLVER_VERSION` goes to "4" in the same
change, so every row is rewritten once on the next sync and the new columns
fill from claims that already exist. Downgrade drops all seven and loses
nothing permanently: these are materialised from `claim` rows and upgrading
again puts every value back (ADR 0001).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0019_fit_fields"
down_revision: Union[str, Sequence[str], None] = "0018_growing_area_real_estate"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

BOOLEAN_FIELDS = ("is_houseplant", "is_edible", "attracts_pollinators")
SIZE_FIELDS = (
    "mature_height_in_min", "mature_height_in_max",
    "mature_spread_in_min", "mature_spread_in_max",
)


def upgrade() -> None:
    with op.batch_alter_table("species", schema=None) as batch_op:
        for name in BOOLEAN_FIELDS:
            batch_op.add_column(sa.Column(name, sa.Boolean(), nullable=True))
        for name in SIZE_FIELDS:
            batch_op.add_column(sa.Column(name, sa.Float(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("species", schema=None) as batch_op:
        for name in reversed(SIZE_FIELDS + BOOLEAN_FIELDS):
            batch_op.drop_column(name)
