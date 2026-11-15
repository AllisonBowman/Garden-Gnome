"""site_override — an owner's corrections, never touched by a refresh

Revision ID: 0031_site_override
Revises: 0030_geodata_tile
Create Date: 2026-11-15

One concern: `site_override` (PLAN.md section 5), append-only. Retracting a
correction sets `retracted_at`; a site profile refresh never writes here.
`method` is tap, measured or old_client_edit (a sun edit made through the
old growing-area routes). `zone_id` null means the whole property.

Downgrade drops the table, and with it every correction an owner made.
"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op


revision: str = "0031_site_override"
down_revision: Union[str, Sequence[str], None] = "0030_geodata_tile"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "site_override",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("property_id", sa.Integer(), nullable=False),
        sa.Column("zone_id", sa.Integer(), nullable=True),
        sa.Column("field", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("value", sa.JSON(), nullable=True),
        sa.Column("method", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("retracted_at", sa.DateTime(timezone=False), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_site_override_property_id"), "site_override",
                    ["property_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_site_override_property_id"), table_name="site_override")
    op.drop_table("site_override")
