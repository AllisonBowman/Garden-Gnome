"""claims and authorities — evidence gets a place to live

Revision ID: 0010_claims
Revises: 0009_aloe_vera
Create Date: 2026-08-16

Purely additive: two new tables, nothing existing altered. That is deliberate.
The Phase 2 field reshape is a large change to `species`, and this needs to be
able to land, be tested and be reasoned about without waiting on it or
conflicting with it.

`claim.subject` is a name rather than a foreign key to `species`. Genus-level
claims — Clemson's light table classifies whole genera — have no species row
to point at, and evidence can legitimately be collected before the species
exists in the catalog. Resolution matches on the name.

`authority.licence` is what makes a bad licence survivable: withdrawing a
source becomes a delete plus a recompute instead of an investigation into
which values came from where. ASPCA's terms are why we want that property.

Downgrade drops both tables. No data outside them depends on either yet.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0010_claims"
down_revision: Union[str, Sequence[str], None] = "0009_aloe_vera"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "authority",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("tier", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("licence", sa.String(), nullable=False, server_default=""),
        sa.Column("homepage_url", sa.String(), nullable=False, server_default=""),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_authority_name", "authority", ["name"])

    op.create_table(
        "claim",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("subject", sa.String(), nullable=False),
        sa.Column("field", sa.String(), nullable=False),
        sa.Column("value_json", sa.String(), nullable=False),
        sa.Column("authority_id", sa.Integer(), nullable=False),
        sa.Column("citation_title", sa.String(), nullable=False, server_default=""),
        sa.Column("citation_url", sa.String(), nullable=False, server_default=""),
        sa.Column("quote", sa.String(), nullable=False, server_default=""),
        sa.Column("collected_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["authority_id"], ["authority.id"]),
        sa.PrimaryKeyConstraint("id"),
        # One citation may assert a given field about a given subject once.
        # Re-running an extractor over the same page is then an upsert rather
        # than a pile of duplicates that would skew nothing but confuse audit.
        sa.UniqueConstraint("subject", "field", "citation_url"),
    )
    op.create_index("ix_claim_subject", "claim", ["subject"])
    op.create_index("ix_claim_field", "claim", ["field"])


def downgrade() -> None:
    op.drop_index("ix_claim_field", table_name="claim")
    op.drop_index("ix_claim_subject", table_name="claim")
    op.drop_table("claim")
    op.drop_index("ix_authority_name", table_name="authority")
    op.drop_table("authority")
