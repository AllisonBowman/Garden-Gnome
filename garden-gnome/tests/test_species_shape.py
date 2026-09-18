"""The species table can hold what the claim graph resolves.

Plan 2.1–2.7. The tranche was researched into a vocabulary the table did not
have — `water_regime` instead of a day count, `light_fc_min` instead of a
`light_need` label, day and night temperatures instead of one flat band — which
is why nothing could load however good the evidence was.

These fields are additive and every one is nullable. The tranche fills them
sparsely on purpose (night_f_max on 3 of 40 records), and a column that forces
a value would put the fabrication back that Phase 1 spent its time removing.
"""
import pytest
from sqlmodel import select

from app.data.claims.ingest import ingest_tranche
from app.models.models import Claim, Species

# Recorded on the record but not claims about the plant: identity, the
# researcher's own assumptions, and bookkeeping. tranche.py excludes them.
NOT_MATERIALISED = {
    "common_name", "scientific_name_given", "scientific_name_accepted",
    "name_note", "is_houseplant", "water_estimate_basis", "cool_rest_note",
}


def test_every_field_the_tranche_resolves_has_a_species_column(session):
    """The Phase 2 gate, stated as an assertion.

    If a claim resolves to a field the table cannot store, that value is
    stranded — researched, cited, and invisible.
    """
    ingest_tranche(session)
    claim_fields = {c.field for c in session.exec(select(Claim)).all()}

    stranded = claim_fields - set(Species.model_fields) - NOT_MATERIALISED

    assert stranded == set(), (
        f"resolved values with no column to live in: {sorted(stranded)}")


def test_the_new_care_fields_are_all_optional():
    """Sparse evidence must stay sparse rather than being filled in."""
    sparse = Species(
        common_name="Test", scientific_name="Testus minimus",
        light_need="medium", humidity_pct_min=40, humidity_pct_max=60,
        temp_f_min=60, temp_f_max=80, soil_type="mix",
    )

    for field in ("water_regime", "light_fc_min", "humidity_need",
                  "day_f_min", "night_f_max", "chill_damage_f", "soil_base",
                  "soil_drainage", "fertilize_interval_days", "toxicity_detail"):
        assert getattr(sparse, field) is None, field


def test_a_researched_species_round_trips_through_the_table(session):
    rich = Species(
        common_name="Snake Plant", scientific_name="Dracaena trifasciata",
        light_need="low", humidity_pct_min=40, humidity_pct_max=60,
        temp_f_min=60, temp_f_max=80, soil_type="mix",
        light_fc_min=100, light_fc_good=200,
        water_regime="dry_thoroughly_between", water_dormant_days_est=45,
        humidity_need="low", soil_drainage="moderate", soil_ph_min=6.0,
        chill_damage_f=50, toxicity_detail="Saponins; low severity.",
    )
    session.add(rich)
    session.commit()
    session.refresh(rich)

    stored = session.exec(select(Species).where(
        Species.scientific_name == "Dracaena trifasciata")).one()
    assert stored.water_regime == "dry_thoroughly_between"
    assert stored.light_fc_min == 100
    assert stored.soil_ph_min == pytest.approx(6.0)
    assert stored.chill_damage_f == 50


def test_list_valued_fields_survive_as_lists(session):
    """`fertilize_active_months` and `outdoor_sun_exposure` are sets of values.

    Stored as JSON text, because a comma-joined string is a parsing problem
    waiting to happen and SQLite has no array type.
    """
    row = Species(
        common_name="Rosemary", scientific_name="Salvia rosmarinus",
        light_need="direct", humidity_pct_min=30, humidity_pct_max=50,
        temp_f_min=50, temp_f_max=90, soil_type="mix",
        fertilize_active_months=[3, 4, 5, 6, 7, 8],
        outdoor_sun_exposure=["full_sun", "part_shade"],
    )
    session.add(row)
    session.commit()
    session.refresh(row)

    stored = session.exec(select(Species).where(
        Species.scientific_name == "Salvia rosmarinus")).one()
    assert stored.fertilize_active_months == [3, 4, 5, 6, 7, 8]
    assert stored.outdoor_sun_exposure == ["full_sun", "part_shade"]
