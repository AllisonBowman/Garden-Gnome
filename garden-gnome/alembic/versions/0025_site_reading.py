"""site_reading — what each public source said about a property

Revision ID: 0025_site_reading
Revises: 0024_growing_area_zones
Create Date: 2026-11-15

One concern: the append-only `site_reading` table (PLAN.md section 5). A newer
reading of a field sets `superseded_at` on the older one rather than
replacing it, so the public value can stay visible beside an owner's
correction. `zone_id` is a growing-area id with no database foreign key,
like `property_id`. `value`, `reason_codes` and `detail` are JSON.

Downgrade drops the table. Every reading can be fetched again from its
public source by refreshing the site profile.
"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op


revision: str = "0025_site_reading"
down_revision: Union[str, Sequence[str], None] = "0024_growing_area_zones"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "site_reading",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("property_id", sa.Integer(), nullable=False),
        sa.Column("zone_id", sa.Integer(), nullable=True),
        sa.Column("field", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("value", sa.JSON(), nullable=True),
        sa.Column("level", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("provenance", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("source_key", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("source_version", sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default=""),
        sa.Column("method", sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default=""),
        sa.Column("reason_codes", sa.JSON(), nullable=True),
        sa.Column("detail", sa.JSON(), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("superseded_at", sa.DateTime(timezone=False), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_site_reading_property_id"), "site_reading",
                    ["property_id"], unique=False)
    op.create_index(op.f("ix_site_reading_zone_id"), "site_reading",
                    ["zone_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_site_reading_zone_id"), table_name="site_reading")
    op.drop_index(op.f("ix_site_reading_property_id"), table_name="site_reading")
    op.drop_table("site_reading")
