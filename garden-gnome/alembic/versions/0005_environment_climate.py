"""environment climate characteristics — shelter / temp_exposure / sun_exposure

Revision ID: 0005_environment_climate
Revises: 0004_environment_owner
Create Date: 2026-07-23

Adds the three weather-feature characteristics to `environment`. Stored as
TEXT (SQLModel enums are stored as their string values, no CHECK constraint on
SQLite — same as EnvironmentType). Existing rows backfill to the safe
indoor/sheltered defaults via server_default.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = "0005_environment_climate"
down_revision: Union[str, Sequence[str], None] = "0004_environment_owner"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("environment", schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            "shelter", sqlmodel.sql.sqltypes.AutoString(),
            nullable=False, server_default="sheltered"))
        batch_op.add_column(sa.Column(
            "temp_exposure", sqlmodel.sql.sqltypes.AutoString(),
            nullable=False, server_default="indoor"))
        batch_op.add_column(sa.Column(
            "sun_exposure", sqlmodel.sql.sqltypes.AutoString(),
            nullable=False, server_default="partial_sun"))


def downgrade() -> None:
    with op.batch_alter_table("environment", schema=None) as batch_op:
        batch_op.drop_column("sun_exposure")
        batch_op.drop_column("temp_exposure")
        batch_op.drop_column("shelter")
