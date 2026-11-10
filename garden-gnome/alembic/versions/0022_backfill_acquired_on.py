"""plant.acquired_on for the plants added before the server dated them

Revision ID: 0022_backfill_acquired_on
Revises: 0021_pending_apple_revocation
Create Date: 2026-10-20

The to-do list and the reminder planner anchor a check on the last care log
of its kind, then on `acquired_on`, then on "now" -- and "now" moves with
every recalculation, so a plant with neither never came due. Since 7dac70d
the server stamps `acquired_on` with the day a plant is added, but only for
plants added from then on. No app version has ever sent the field, so every
plant added through 1.1.2 or earlier has it null, and those plants still said
"All caught up" for any kind of care nobody had logged on them yet.

This gives each of them the day it was added, the same date the server now
stamps on a new plant: `created_at`'s date, in UTC, like every timestamp in
this schema. A plant split off another before the server dated plants takes
its parent's date, which is what the split route does today (it copies
`acquired_on` across); one whose parent is gone takes its own. A date
someone did set is never touched.

No column changes, so the downgrade leaves the dates where they are: the
column exists at 0021 too, and the date is the true day the plant was added.
"""
from typing import Sequence, Union

from alembic import op


revision: str = "0022_backfill_acquired_on"
down_revision: Union[str, Sequence[str], None] = "0021_pending_apple_revocation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    added = ("date(created_at)" if op.get_bind().dialect.name == "sqlite"
             else "CAST(created_at AS DATE)")
    # Plants that were not split off anything: the day each was added.
    op.execute(
        f"UPDATE plant SET acquired_on = {added} "
        "WHERE acquired_on IS NULL AND split_from_uuid IS NULL")
    # A split takes its parent's date, as the split route does.
    op.execute(
        "UPDATE plant SET acquired_on = (SELECT parent.acquired_on FROM plant "
        "AS parent WHERE parent.plant_uuid = plant.split_from_uuid) "
        "WHERE acquired_on IS NULL AND split_from_uuid IS NOT NULL")
    # Anything left -- a split whose parent is gone -- its own day.
    op.execute(f"UPDATE plant SET acquired_on = {added} WHERE acquired_on IS NULL")


def downgrade() -> None:
    # Nothing to undo: see the module docstring.
    pass
