"""shade light — no shade-adapted genus can need direct sun

Revision ID: 0007_shade_light
Revises: 0006_plant_quantity
Create Date: 2026-08-08

The Perenual import mapped "full sun" to `direct` and let genus-mates inherit
it, which left a large share of the imported catalog telling people to put
understorey plants in a south window. A Monstera, a Calathea, a ZZ — these are
shade-adapted by definition; no source that has actually looked at one calls
its light need "direct". The curated rows never had this problem (all fourteen
shade-genus entries sit at low/medium/bright_indirect), and the seeder skips
rows that already exist, so fixing the seed JSON would fix nothing. The rows
live here, so the fix does too.

One rule, no research: any species whose genus is on the shade-adapted list
and whose light_need is `direct` becomes `bright_indirect` — the strongest
light the genus can honestly be said to want. Everything else (the vegetable
garden's basil and corn, genuinely sun-hungry things) is untouched.

The match is case-insensitive on light_need out of caution: ORM-written rows
store the lowercase enum labels, but nothing in SQLite ever enforced that.

Downgrade is a deliberate no-op. The old values were wrong; a migration that
could put them back would only exist to re-break the catalog.
"""
from typing import Sequence, Union

from alembic import op


revision: str = "0007_shade_light"
down_revision: Union[str, Sequence[str], None] = "0006_plant_quantity"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SHADE_GENERA = [
    "Aglaonema",
    "Aspidistra",
    "Calathea",
    "Chamaedorea",
    "Dracaena",
    "Epipremnum",
    "Ficus",
    "Goeppertia",
    "Maranta",
    "Monstera",
    "Philodendron",
    "Schefflera",
    "Spathiphyllum",
    "Zamioculcas",
]


def _genus_predicate() -> str:
    clauses = [
        f"scientific_name = '{g}' OR scientific_name LIKE '{g} %'"
        for g in SHADE_GENERA
    ]
    return " OR ".join(clauses)


def upgrade() -> None:
    op.execute(
        "UPDATE species SET light_need = 'bright_indirect' "
        f"WHERE lower(light_need) = 'direct' AND ({_genus_predicate()})"
    )


def downgrade() -> None:
    pass
