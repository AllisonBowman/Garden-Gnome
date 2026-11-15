"""growing area zone columns — a zone is a growing area on a property

Revision ID: 0024_growing_area_zones
Revises: 0023_property
Create Date: 2026-11-15

PLAN.md D1: a zone is a `growingarea` row with `property_id` set, so plants,
weather, fit, census and account deletion keep working for it, and the 1.1.x
client sees a zone as an ordinary growing area. One concern: seven columns.

Every column is added with a plain `ALTER TABLE ... ADD COLUMN` (no table
rebuild, D3), and every one is nullable or defaulted, so each row that exists
today, including every automatic "My Home" area, reads exactly as before:

  property_id      indexed integer, and deliberately no database foreign key
                   (D3): adding one would rebuild the table on a database
                   whose structure changes are not transactional.
  vegetation_type  tree, shrub, grass, garden_bed, bare_hardscape.
  boundary_geojson the zone's box as a GeoJSON Polygon (longitude, latitude).
  boundary_source  "default" (the approximate square around the pin) or
                   "owner" (a box the owner drew).
  is_whole_lot     false for every existing row.
  leaf_habit       drops_leaves, evergreen, mixed.
  sun_source       "owner" once the owner has said what the sun is; null
                   means `sun_exposure` is still the column's default.

Downgrade removes them (through a batch rebuild, as 0018's downgrade does).
Zones then become plain growing areas and lose their boxes; their plants stay
where they are.
"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op


revision: str = "0024_growing_area_zones"
down_revision: Union[str, Sequence[str], None] = "0023_property"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


COLUMNS = ("property_id", "vegetation_type", "boundary_geojson",
           "boundary_source", "is_whole_lot", "leaf_habit", "sun_source")


def upgrade() -> None:
    # Plain op.add_column, not batch mode: SQLite adds a column in place.
    op.add_column("growingarea", sa.Column("property_id", sa.Integer(),
                                           nullable=True))
    op.add_column("growingarea", sa.Column(
        "vegetation_type", sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.add_column("growingarea", sa.Column(
        "boundary_geojson", sa.JSON(), nullable=True))
    op.add_column("growingarea", sa.Column(
        "boundary_source", sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.add_column("growingarea", sa.Column(
        "is_whole_lot", sa.Boolean(), nullable=False,
        server_default=sa.false()))
    op.add_column("growingarea", sa.Column(
        "leaf_habit", sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.add_column("growingarea", sa.Column(
        "sun_source", sqlmodel.sql.sqltypes.AutoString(), nullable=True))
    op.create_index(op.f("ix_growingarea_property_id"), "growingarea",
                    ["property_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_growingarea_property_id"), table_name="growingarea")
    with op.batch_alter_table("growingarea", schema=None) as batch_op:
        for column in reversed(COLUMNS):
            batch_op.drop_column(column)
