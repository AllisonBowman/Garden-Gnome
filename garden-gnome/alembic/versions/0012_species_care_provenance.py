"""species care provenance — say where a value came from, and when

Revision ID: 0012_care_provenance
Revises: 0011_species_care
Create Date: 2026-08-18

0011 gave the catalog columns for the things it measures. It did not give it
anywhere to say how well it knows them, and without that a resolved value is
just another unattributed number — which is the condition this whole plan
exists to end.

Three columns, all derived and all owned by the recompute:

`care_data_status` is the row-level answer to "should the app speak with
confidence about this plant": `sourced` when at least one value came from a
citation naming this species, `inferred` when every value it has was borrowed
from the genus, `none` when it has nothing. Plan 3.4 gates the advice fact
block, the reminders and the detail screen on it.

`care_provenance` is the per-field version, `{field: sourced|genus_inferred}`.
ADR 0002 requires an inherited value to be labelled wherever it is shown, and
an inherited value that looks measured is worse than no value at all. Storing
it here keeps the read path a single row fetch rather than a re-resolution.

`resolver_version` records which rules produced the row. Resolution rules will
change; when they do, the stale rows become a query rather than a guess, and
recompute can be re-run over exactly those.

Additive and nullable. Every existing row reads as "not yet resolved", which
is true.

Downgrade drops the three columns.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0012_care_provenance"
down_revision: Union[str, Sequence[str], None] = "0011_species_care"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

COLUMNS: list[tuple[str, sa.types.TypeEngine]] = [
    ("care_data_status", sa.String()),
    ("care_provenance", sa.JSON()),
    ("resolver_version", sa.String()),
]


def upgrade() -> None:
    for name, type_ in COLUMNS:
        op.add_column("species", sa.Column(name, type_, nullable=True))


def downgrade() -> None:
    for name, _type in COLUMNS:
        op.drop_column("species", name)
