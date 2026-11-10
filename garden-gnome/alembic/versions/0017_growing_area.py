"""environment becomes growing area — the space, described

Revision ID: 0017_growing_area
Revises: 0016_outdoor_temp_min_f
Create Date: 2026-09-14

`Environment` was named for what it was: a container that scoped the care
calendar and told the weather service where to look. It answered "where does
this plant live", and nothing else ever asked it a question.

It is about to answer a different one. A growing area describes the real
estate someone has -- the surface, its dimensions, what they want out of it --
so the catalog can be filtered to species that fit it and the plants already
there can be told, specifically, how they do not. That is a description of a
place to grow, not an ambient condition, and `environment` is the wrong word
for it in a codebase that also says "environment variable" three times in the
same breath.

So the table is `growingarea` and the foreign keys are `growing_area_id`,
matching `GrowingArea` in the models. This is a rename and nothing else: no
column changes shape, no value moves, and the row count is identical on both
sides. The real estate columns arrive in 0018, once there is a name to hang
them on.

SQLite updates a foreign key's target in the referencing table's DDL when the
referenced table is renamed (3.25+, with `legacy_alter_table` off, which is
the default), so `plant` and `stewardshiprecord` point at `growingarea` before
batch mode rebuilds them to rename their own column. The upgrade checks that
it worked rather than trusting it -- a dangling reference here would orphan
every plant.

The link check runs twice, and the first time before any DDL. SQLite DDL is
not transactional under this Alembic setup ("Will assume non-transactional
DDL"), so a check that only ran at the end failed *after* the rename had
landed: the file was left half-renamed with `alembic_version` still at 0016,
and every later boot died on `no such table: environment`. A plant or
stewardship record that already pointed at a missing area is now refused up
front, naming the rows, while the file is still exactly 0016 -- fix the rows
and boot again. The check covers only the links this migration rewrites (the
two `environment_id` columns). A dangling reference elsewhere, say a care log
whose plant is gone, is not something a rename can make worse, and refusing
to boot over it would take the API down for nothing; production has never
enforced foreign keys, so such rows are possible. The second check, after the
DDL, proves the rename itself kept every link.

`ix_environment_user_id` is renamed alongside. An index that outlives the name
of its table is how the next person reading `PRAGMA index_list` concludes
something was left half-done.

Downgrade puts every name back. Nothing is lost in either direction; this
migration moves no data.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0017_growing_area"
down_revision: Union[str, Sequence[str], None] = "0016_outdoor_temp_min_f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# The two tables that carry a foreign key to the renamed one.
REFERRERS = ("plant", "stewardshiprecord")


def _assert_points_at(table: str, target: str) -> None:
    """Fail loudly if `table`'s foreign key no longer names `target`.

    Renaming a table is only safe here because SQLite rewrites the referencing
    DDL for us. If a future SQLite, or a Postgres move, ever stops doing that,
    the symptom would be every plant silently detaching from its area -- so
    this is checked, not assumed."""
    bind = op.get_bind()
    if bind.dialect.name != "sqlite":
        return  # Postgres updates the catalog entry itself; nothing to read back.
    refs = {row[2] for row in bind.execute(
        sa.text(f"PRAGMA foreign_key_list({table})"))}
    if target not in refs:
        raise RuntimeError(
            f"0017 renamed the table but {table}'s foreign key still points at "
            f"{refs or 'nothing'}, not {target}. Every plant would be orphaned; "
            "migrate no further.")


def _dangling_links(target: str) -> list[str]:
    """Each REFERRERS row whose area link names a `target` row that does not
    exist, as a sentence an operator can act on. Other foreign keys in those
    tables are not this migration's business and are not reported."""
    bind = op.get_bind()
    found = []
    for table in REFERRERS:
        columns = {row[0]: row[3] for row in bind.execute(
            sa.text(f"PRAGMA foreign_key_list({table})"))}
        for _, rowid, parent, fkid in bind.execute(
                sa.text(f"PRAGMA foreign_key_check({table})")):
            if parent != target:
                continue
            column = columns.get(fkid, "?")
            value = bind.execute(
                sa.text(f"SELECT {column} FROM {table} WHERE rowid = :r"),
                {"r": rowid}).scalar() if column != "?" else "?"
            found.append(f"{table} row {rowid} has {column} = {value}, "
                         f"but {target} has no row {value}")
    return found


def _refuse_dangling_links(target: str, verdict: str) -> None:
    """Raise, naming the rows, if any area link points at a missing `target`."""
    if op.get_bind().dialect.name != "sqlite":
        return  # Postgres enforces these; nothing can dangle.
    found = _dangling_links(target)
    if not found:
        return
    shown = "; ".join(found[:20])
    more = f" (and {len(found) - 20} more)" if len(found) > 20 else ""
    raise RuntimeError(
        f"0017: {len(found)} row(s) point at a missing {target}: "
        f"{shown}{more}. {verdict}")


#: What an operator reads when the first check refuses.
REFUSED_BEFORE_DDL = (
    "Nothing was changed: the database is still at 0016. Point each row at a "
    "real area (a plant's link may also be set to NULL, or a stewardship "
    "record deleted), then boot again.")


def upgrade() -> None:
    # Before any DDL: SQLite won't roll a rename back, so this is the last
    # moment a refusal leaves the file exactly as 0016 left it.
    _refuse_dangling_links("environment", REFUSED_BEFORE_DDL)

    op.rename_table("environment", "growingarea")
    for table in REFERRERS:
        _assert_points_at(table, "growingarea")

    with op.batch_alter_table("growingarea", schema=None) as batch_op:
        batch_op.drop_index("ix_environment_user_id")
        batch_op.create_index(
            batch_op.f("ix_growingarea_user_id"), ["user_id"], unique=False)

    for table in REFERRERS:
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.alter_column(
                "environment_id", new_column_name="growing_area_id")

    _refuse_dangling_links(
        "growingarea", "The rename itself broke these links; migrate no further.")


def downgrade() -> None:
    _refuse_dangling_links(
        "growingarea", "Nothing was changed: the database is still at 0017.")
    for table in REFERRERS:
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.alter_column(
                "growing_area_id", new_column_name="environment_id")

    with op.batch_alter_table("growingarea", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_growingarea_user_id"))
        batch_op.create_index("ix_environment_user_id", ["user_id"], unique=False)

    op.rename_table("growingarea", "environment")
    for table in REFERRERS:
        _assert_points_at(table, "environment")
