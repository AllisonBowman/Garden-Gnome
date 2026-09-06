"""Materialising resolved values onto the catalog.

The last link: `claim` holds evidence, `species` holds the columns, and this is
what connects them. Values are derived here and never typed in (ADR 0001), so
the row records which rules produced it and how well-backed each field is.
"""
import json
import shutil
from pathlib import Path

import pytest
from sqlmodel import Session, create_engine, select

from app.data.claims.recompute import (
    ATTRIBUTABLE_FIELDS, RESOLVED_FIELDS, RESOLVER_VERSION, SERVER_ONLY_FIELDS,
    recompute_all,
)
from app.models.models import (
    Authority, CareDataStatus, CareLog, CareSchedule, Claim, Plant,
    Species, SpeciesTrait,
)

NCSU = "https://plants.ces.ncsu.edu/plants/x/"
NCSU_GENUS = "https://plants.ces.ncsu.edu/plants/dracaena/"
CLEMSON = "https://hgic.clemson.edu/factsheet/y/"


@pytest.fixture()
def session(migrated_db_url, tmp_path):
    """A private database per test.

    `recompute_all` walks every species in the catalog, so it is sensitive to
    whatever other test modules have committed into the shared session-scoped
    database -- and wiping that shared database instead would orphan their care
    schedules. A copy costs a few milliseconds and makes the counts mean
    something.
    """
    work = tmp_path / "recompute.db"
    shutil.copy(Path(migrated_db_url.removeprefix("sqlite:///")), work)
    engine = create_engine(f"sqlite:///{work.as_posix()}")
    with Session(engine) as s:
        for model in (Claim, Authority, CareLog, CareSchedule, SpeciesTrait,
                      Plant, Species):
            for row in s.exec(select(model)).all():
                s.delete(row)
        s.commit()
        yield s
    engine.dispose()


def make_species(session, scientific_name, common="Test Plant"):
    sp = Species(
        common_name=common, scientific_name=scientific_name,
        light_need="medium", humidity_pct_min=40, humidity_pct_max=60,
        temp_f_min=60, temp_f_max=80, soil_type="mix", toxic_to_pets=False)
    session.add(sp)
    session.commit()
    session.refresh(sp)
    return sp


def add_claim(session, subject, field, value, url=NCSU, name="NC State Extension"):
    authority = session.exec(
        select(Authority).where(Authority.name == name)).first()
    if authority is None:
        authority = Authority(name=name, tier=2, licence="x")
        session.add(authority)
        session.commit()
        session.refresh(authority)
    session.add(Claim(subject=subject, field=field, value_json=json.dumps(value),
                      authority_id=authority.id, citation_url=url,
                      citation_title=name, quote="q"))
    session.commit()


def reload(session, scientific_name):
    session.expire_all()
    return session.exec(
        select(Species).where(Species.scientific_name == scientific_name)).one()


def test_resolved_values_land_on_the_species_row(session):
    make_species(session, "Dracaena trifasciata", "Snake Plant")
    add_claim(session, "Dracaena trifasciata", "humidity_need", "low")
    add_claim(session, "Dracaena trifasciata", "chill_damage_f", 50)
    add_claim(session, "Dracaena trifasciata", "water_regime",
              "dry_thoroughly_between")

    report = recompute_all(session)

    sp = reload(session, "Dracaena trifasciata")
    assert sp.humidity_need == "low"
    assert sp.chill_damage_f == 50
    assert sp.water_regime == "dry_thoroughly_between"
    assert sp.care_data_status == CareDataStatus.sourced
    assert sp.care_provenance["humidity_need"] == "sourced"
    assert sp.resolver_version
    assert report.species_updated == 1


def test_an_inherited_value_is_labelled_and_downgrades_the_row(session):
    make_species(session, "Dracaena fragrans")
    add_claim(session, "Dracaena", "humidity_need", "average")

    recompute_all(session)

    sp = reload(session, "Dracaena fragrans")
    assert sp.humidity_need == "average"
    assert sp.care_provenance["humidity_need"] == "genus_inferred"
    # Nothing was said about this species itself, so the row cannot claim to
    # be sourced -- plan 3.4 gates the advice fact block on exactly this.
    assert sp.care_data_status == CareDataStatus.inferred


def test_a_species_with_no_evidence_says_so(session):
    make_species(session, "Ignotus obscurus")

    recompute_all(session)

    sp = reload(session, "Ignotus obscurus")
    assert sp.care_data_status == CareDataStatus.none
    assert sp.humidity_need is None


def test_a_refused_field_is_left_null_rather_than_picked(session):
    make_species(session, "Testus conflictus")
    add_claim(session, "Testus conflictus", "chill_damage_f", 50)
    add_claim(session, "Testus conflictus", "chill_damage_f", 32,
              url=CLEMSON, name="Clemson Cooperative Extension")
    add_claim(session, "Testus conflictus", "humidity_need", "low")

    recompute_all(session)

    sp = reload(session, "Testus conflictus")
    assert sp.chill_damage_f is None
    assert "chill_damage_f" not in (sp.care_provenance or {})
    # The rest of the row still resolves; one refusal is not a row failure.
    assert sp.humidity_need == "low"


def test_only_allowlisted_fields_can_be_written(session):
    # A claim naming something that is not a resolved care field must not be
    # able to set an arbitrary column -- `scientific_name` least of all.
    make_species(session, "Dracaena trifasciata")
    add_claim(session, "Dracaena trifasciata", "scientific_name", "Hacked name")
    add_claim(session, "Dracaena trifasciata", "review_status", "verified")

    recompute_all(session)

    sp = reload(session, "Dracaena trifasciata")
    assert sp.scientific_name == "Dracaena trifasciata"
    assert sp.review_status != "verified"
    assert "scientific_name" not in RESOLVED_FIELDS


def test_running_it_twice_leaves_the_database_byte_identical(
        session, migrated_db_url, tmp_path):
    """The promise made when the claim tables were first designed.

    Resolution is a pure function of the claims that exist, so a second pass
    over unchanged evidence must be a no-op -- not merely produce equal values,
    but not write at all. Anything else means the catalog quietly churns every
    time this runs, and `resolver_version` stops meaning anything.

    The species wins values from two authorities and from two NC State pages
    (one about the genus), so `care_sources` has to group and sort the same
    way every time for the second pass to write nothing.
    """
    work = tmp_path / "recompute2.db"
    shutil.copy(Path(migrated_db_url.removeprefix("sqlite:///")), work)
    engine = create_engine(f"sqlite:///{work.as_posix()}")

    with Session(engine) as s:
        for model in (Claim, Authority, CareLog, CareSchedule, SpeciesTrait,
                      Plant, Species):
            for row in s.exec(select(model)).all():
                s.delete(row)
        s.commit()
        make_species(s, "Dracaena trifasciata", "Snake Plant")
        add_claim(s, "Dracaena trifasciata", "humidity_need", "low")
        add_claim(s, "Dracaena trifasciata", "chill_damage_f", 50)
        add_claim(s, "Dracaena trifasciata", "soil_ph_min", 6.0,
                  url=CLEMSON, name="Clemson Cooperative Extension")
        add_claim(s, "Dracaena", "soil_drainage", "fast", url=NCSU_GENUS)
        first = recompute_all(s)

    before = work.read_bytes()

    with Session(engine) as s:
        second = recompute_all(s)
        sp = reload(s, "Dracaena trifasciata")
        # One entry per (authority, page), fields sorted, list sorted, and the
        # genus page marked as such -- never the quote, never a title.
        assert sp.care_sources == [
            {"authority": "Clemson Cooperative Extension", "url": CLEMSON,
             "fields": ["soil_ph_min"], "inferred": False},
            {"authority": "NC State Extension", "url": NCSU_GENUS,
             "fields": ["soil_drainage"], "inferred": True},
            {"authority": "NC State Extension", "url": NCSU,
             "fields": ["chill_damage_f", "humidity_need"], "inferred": False},
        ]
        assert sp.resolver_version == RESOLVER_VERSION
    engine.dispose()

    assert first.species_updated == 1
    assert second.species_updated == 0
    assert work.read_bytes() == before


def test_withdrawing_an_authority_and_recomputing_clears_its_values(session):
    """The licence drill, end to end.

    ADR 0001 promises that dropping an unusable source is a query. That is only
    true if the values it was supporting actually go away afterwards.
    """
    from app.data.claims.store import withdraw_authority

    make_species(session, "Dracaena trifasciata")
    add_claim(session, "Dracaena trifasciata", "humidity_need", "low")
    add_claim(session, "Dracaena trifasciata", "soil_drainage", "fast")
    recompute_all(session)
    assert reload(session, "Dracaena trifasciata").humidity_need == "low"

    withdraw_authority(session, "NC State Extension")
    recompute_all(session)

    sp = reload(session, "Dracaena trifasciata")
    assert sp.humidity_need is None
    assert sp.soil_drainage is None
    assert sp.care_data_status == CareDataStatus.none


def test_dry_run_reports_without_writing(session):
    make_species(session, "Dracaena trifasciata")
    add_claim(session, "Dracaena trifasciata", "humidity_need", "low")

    report = recompute_all(session, dry_run=True)

    assert report.species_updated == 1
    assert reload(session, "Dracaena trifasciata").humidity_need is None


def test_a_usda_hardiness_claim_resolves_onto_the_species_row(session):
    """The scoped tier-1 authority feeds the same pipeline as everyone else.

    USDA PLANTS was investigated as a general care-data source and rejected --
    this is the one field it actually earned: hardiness zones, and only that.
    """
    make_species(session, "Salvia rosmarinus", "Rosemary")
    add_claim(session, "Salvia rosmarinus", "hardiness_zones", [7, 8, 9, 10],
              url="https://plants.usda.gov/plant-profile/SALRO2",
              name="USDA PLANTS Database")

    recompute_all(session)

    sp = reload(session, "Salvia rosmarinus")
    assert sp.hardiness_zones == [7, 8, 9, 10]
    assert sp.care_provenance["hardiness_zones"] == "sourced"


def test_care_sources_are_null_when_nothing_won(session):
    make_species(session, "Ignotus obscurus")

    recompute_all(session)

    assert reload(session, "Ignotus obscurus").care_sources is None


def test_a_page_is_credited_only_for_fields_a_client_can_see(session):
    """`toxicity_detail` and `water_dry_down_target` are verbatim passages,
    held as audit evidence and never shipped (ADR 0003). A page that settled
    only those would sit in the app's Sources card with nothing visible behind
    it and be named in "cited to ..." for a fact nobody can read -- attribution
    the reader has to take on faith. The value still lands on the row; the
    page is credited for what a reader can check, and for nothing else."""
    make_species(session, "Toxicodendron radicans", "Poison Ivy")
    add_claim(session, "Toxicodendron radicans", "toxicity_detail",
              "contact dermatitis prose", url=CLEMSON,
              name="Clemson Cooperative Extension")
    add_claim(session, "Toxicodendron radicans", "humidity_need", "average")
    add_claim(session, "Toxicodendron radicans", "water_dry_down_target",
              "verbatim passage")

    recompute_all(session)

    sp = reload(session, "Toxicodendron radicans")
    assert sp.toxicity_detail == "contact dermatitis prose"
    assert sp.water_dry_down_target == "verbatim passage"
    assert sp.care_sources == [
        {"authority": "NC State Extension", "url": NCSU,
         "fields": ["humidity_need"], "inferred": False},
    ]
    assert SERVER_ONLY_FIELDS <= RESOLVED_FIELDS
    assert not (SERVER_ONLY_FIELDS & ATTRIBUTABLE_FIELDS)


def test_resolution_keys_on_the_accepted_name_when_the_row_carries_one(session):
    """A catalog row keeps the name users and toxicity.lookup key on; the
    tranche researched it under its accepted name. The claims are keyed by
    the latter, and the row must still find them."""
    sp = make_species(session, "Sansevieria trifasciata", "Snake Plant")
    sp.scientific_name_accepted = "Dracaena trifasciata"
    session.add(sp)
    session.commit()
    add_claim(session, "Dracaena trifasciata", "humidity_need", "low")

    recompute_all(session)

    sp = reload(session, "Sansevieria trifasciata")
    assert sp.humidity_need == "low"
    assert sp.care_data_status == CareDataStatus.sourced


def test_an_unknown_toxicity_stays_unknown_rather_than_becoming_safe(session):
    """A minted row starts with toxic_to_pets null. With no toxicity claim the
    recompute must leave it null -- writing False there would be the invented
    safety verdict ADR 0002 forbids."""
    sp = Species(common_name="Minted", scientific_name="Testus mintus",
                 toxic_to_pets=None, care_notes="")
    session.add(sp)
    session.commit()
    add_claim(session, "Testus mintus", "humidity_need", "low")

    recompute_all(session)

    sp = reload(session, "Testus mintus")
    assert sp.toxic_to_pets is None
    assert sp.humidity_need == "low"
    assert sp.light_need is None


def test_commit_false_leaves_the_transaction_to_the_caller(session):
    make_species(session, "Dracaena trifasciata")
    add_claim(session, "Dracaena trifasciata", "humidity_need", "low")

    report = recompute_all(session, commit=False)

    assert report.species_updated == 1
    assert session.exec(select(Species).where(
        Species.scientific_name == "Dracaena trifasciata")).one().humidity_need == "low"
    session.rollback()
    assert reload(session, "Dracaena trifasciata").humidity_need is None
