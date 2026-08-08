"""aloe vera — three errors in one name

Revision ID: 0009_aloe_vera
Revises: 0008_care_outcome
Create Date: 2026-08-08

`Aloe barbadensis miller` gets the species wrong (barbadensis is a synonym),
the rank wrong (miller is Philip Miller, the botanist authority, not a
variety), and the capitalisation wrong (an authority would be capitalised).
The accepted name is `Aloe vera` — WFO and every extension source agree.

The seed JSON is fixed in the same commit, but the seeder skips rows that
already exist, so the deployed row is fixed here. The rename is guarded: if
an `Aloe vera` row somehow already exists (the Perenual import could have
minted one), renaming would create the ambiguous-name collision that
apply_review now refuses — in that case the misnamed row is left for the
catalog-shrink pass to reconcile, which can look at both rows' data.

Downgrade is a no-op: restoring a wrong name serves nobody.
"""
from typing import Sequence, Union

from alembic import op


revision: str = "0009_aloe_vera"
down_revision: Union[str, Sequence[str], None] = "0008_care_outcome"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "UPDATE species SET scientific_name = 'Aloe vera' "
        "WHERE scientific_name = 'Aloe barbadensis miller' "
        "AND NOT EXISTS (SELECT 1 FROM species s2 "
        "WHERE s2.scientific_name = 'Aloe vera')"
    )


def downgrade() -> None:
    pass
