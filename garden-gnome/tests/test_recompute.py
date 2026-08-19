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

from app.data.claims.recompute import RESOLVED_FIELDS, recompute_all
from app.models.models import (
    Authority, CareDataStatus, CareLog, CareSchedule, Claim, Plant,
    Species, SpeciesTrait,
)

NCSU = "https://plants.ces.ncsu.edu/plants/x/"
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
        add_claim(s, "Dracaena", "soil_drainage", "fast")
        first = recompute_all(s)

    before = work.read_bytes()

    with Session(engine) as s:
        second = recompute_all(s)
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
