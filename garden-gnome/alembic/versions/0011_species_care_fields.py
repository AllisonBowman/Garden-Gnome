"""species care fields — measure the right quantities

Revision ID: 0011_species_care
Revises: 0010_claims
Create Date: 2026-08-17

Plan 2.1-2.7. The verified tranche was researched into a vocabulary this table
did not have: a watering *regime* rather than a day count, footcandles and
direct-beam hours rather than a single `light_need` label, day and night
temperatures rather than one flat band, a humidity *category* rather than a
fabricated percentage. Until these columns exist the evidence in `claim` has
nowhere to land, however well cited it is.

Purely additive, and every new column is nullable. The sparseness is the
honest part — `night_f_max` is stated by a source for 3 of the 40 researched
species — and a NOT NULL would put back the invented values Phase 1 removed.

The legacy columns are deliberately untouched. `light_need`, `humidity_pct_min`,
`humidity_pct_max`, `temp_f_min`, `temp_f_max` and `soil_type` are carried by
1,900 rows and read by the app today; retiring them belongs to the catalog
shrink in plan 3.4, not here. Two `humidity_pct_*` values in the tranche
therefore stay in `claim` for now rather than forcing a table rebuild on a
column the whole app reads.

Downgrade drops the new columns only.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0011_species_care"
down_revision: Union[str, Sequence[str], None] = "0010_claims"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (name, type). All nullable, no server default: absent means "no source said".
COLUMNS: list[tuple[str, sa.types.TypeEngine]] = [
    # Light — two independent axes plus the outdoor scale, kept apart so the
    # outdoor duration rating can never be mapped inward again.
    ("light_fc_min", sa.Integer()),
    ("light_fc_good", sa.Integer()),
    ("direct_sun_hours_max", sa.Float()),
    ("outdoor_sun_exposure", sa.JSON()),
    # Water — regime is the fact; the day counts are estimates and say so.
    ("water_regime", sa.String()),
    ("water_dry_down_target", sa.String()),
    ("water_check_depth_cm", sa.Float()),
    ("water_growing_days_est", sa.Integer()),
    ("water_dormant_days_est", sa.Integer()),
    ("water_estimate_basis", sa.String()),
    ("humidity_need", sa.String()),
    # Temperature — four concepts, not one band.
    ("day_f_min", sa.Integer()),
    ("day_f_max", sa.Integer()),
    ("night_f_min", sa.Integer()),
    ("night_f_max", sa.Integer()),
    ("chill_damage_f", sa.Integer()),
    ("cool_rest_note", sa.String()),
    # Soil — structured rather than a prose blob whose fallback string reads
    # like expertise.
    ("soil_base", sa.String()),
    ("soil_drainage", sa.String()),
    ("soil_ph_min", sa.Float()),
    ("soil_ph_max", sa.Float()),
    # Fertilize — a season, an interval inside it, and a dose.
    ("fertilize_active_months", sa.JSON()),
    ("fertilize_interval_days", sa.Integer()),
    ("fertilize_strength", sa.String()),
    ("toxicity_detail", sa.String()),
]


def upgrade() -> None:
    for name, type_ in COLUMNS:
        op.add_column("species", sa.Column(name, type_, nullable=True))


def downgrade() -> None:
    for name, _type in reversed(COLUMNS):
        op.drop_column("species", name)
