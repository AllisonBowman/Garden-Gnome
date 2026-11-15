"""geodata_tile — public geodata for a grid-snapped block, shared

Revision ID: 0030_geodata_tile
Revises: 0029_provider_usage
Create Date: 2026-11-15

One concern: `geodata_tile` (PLAN.md section 5). Soil, elevation, land cover,
canopy and imagery answers for one grid-snapped block of about 500 metres
(D7), kept compressed and shared between neighbours. No user identifier.
`tile_key` is text and starts with the block key, which is how a tile is
known to be unused once no property maps to it. Unique on provider, dataset
version and tile key.

Downgrade drops the table; every tile can be fetched again.
"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op


revision: str = "0030_geodata_tile"
down_revision: Union[str, Sequence[str], None] = "0029_provider_usage"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "geodata_tile",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("provider", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("dataset_version", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("tile_key", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("payload", sa.LargeBinary(), nullable=False),
        sa.Column("bytes", sa.Integer(), nullable=False,
                  server_default=sa.text("0")),
        sa.Column("fetched_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=False), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "dataset_version", "tile_key"),
    )
    op.create_index(op.f("ix_geodata_tile_tile_key"), "geodata_tile",
                    ["tile_key"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_geodata_tile_tile_key"), table_name="geodata_tile")
    op.drop_table("geodata_tile")
