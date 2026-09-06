"""species claim wiring — rows the claims mint, and who said so

Revision ID: 0015_species_claim_wiring
Revises: 0014_authority_scope
Create Date: 2026-09-05

The claim graph was populated into a catalog that could not hold most of it:
342 of the tranche's 469 species have no row, and a row could not be minted
because seven columns demanded values no source ever stated. Making them
nullable is the schema half of ADR 0005. `toxic_to_pets` is among them for
the reason ADR 0002 gives -- a NOT NULL default of False on a species with no
toxicity claim is an invented safety verdict, and 34 of the unmatched species
carry a cited description of harm. No existing row is touched or backfilled;
the recompute's CANNOT_CLEAR keeps legacy flags exactly as they are.

Two columns join the row. `care_sources` is attribution, materialised by the
recompute from the claims that won: authority name, link, field names, and
whether the page spoke at genus scope. Never the quote (ADR 0003).
`scientific_name_accepted` lets a row the catalog holds under an older name
find claims keyed by the tranche's accepted name, without renaming what
users' plants and the toxicity table key on.

`sync_state` is one key/value row: the tranche fingerprint that turns the
per-boot sync into a skip when nothing changed.

SQLite cannot alter nullability in place, so this is one batch rebuild of
`species`. Batch mode reflects the live table -- including the server
defaults the Fly volume's expansion columns carry from migrate_db() -- copies
every row, and swaps the rebuilt table in with its indexes intact.

Downgrade restores NOT NULL, which is impossible while claims-minted rows
exist, and it refuses before touching anything rather than discovering that
halfway through: pysqlite commits each DDL statement as it runs, so a
rebuild that failed after `sync_state` was dropped would leave the volume at
this revision with no sync_state table and a stray _alembic_tmp_species --
every cold start logging "claim sync skipped" until someone hand-writes SQL.
The refusal is deliberate either way: a downgrade must not quietly delete
species that users' plants may reference.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0015_species_claim_wiring"
down_revision: Union[str, Sequence[str], None] = "0014_authority_scope"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# The columns a claims-minted row leaves null.
LEGACY_CARE = [
    "light_need", "humidity_pct_min", "humidity_pct_max",
    "temp_f_min", "temp_f_max", "soil_type", "toxic_to_pets",
]


def upgrade() -> None:
    with op.batch_alter_table("species") as batch_op:
        for name in LEGACY_CARE:
            batch_op.alter_column(name, nullable=True)
        batch_op.add_column(sa.Column("care_sources", sa.JSON(), nullable=True))
        batch_op.add_column(
            sa.Column("scientific_name_accepted", sa.String(), nullable=True))
        batch_op.create_index(
            "ix_species_scientific_name_accepted",
            ["scientific_name_accepted"], unique=False)

    op.create_table(
        "sync_state",
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("value", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("key"),
    )


def downgrade() -> None:
    minted = op.get_bind().execute(sa.text(
        "SELECT 1 FROM species WHERE source = 'claims' LIMIT 1")).first()
    if minted:
        raise RuntimeError(
            "0015 cannot be downgraded while claims-minted species rows exist")
    with op.batch_alter_table("species") as batch_op:
        batch_op.drop_index("ix_species_scientific_name_accepted")
        batch_op.drop_column("scientific_name_accepted")
        batch_op.drop_column("care_sources")
        for name in LEGACY_CARE:
            batch_op.alter_column(name, nullable=False)
    # Last, so a rebuild that fails for any other reason leaves the sync's
    # state table where the running app expects it.
    op.drop_table("sync_state")
