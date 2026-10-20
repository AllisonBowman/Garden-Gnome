"""The catalog's generation: a fresh token on every write to a catalog row.

Both catalog caches (the species list body, the parsed safety passages) key
on it, so a write that adds no row and moves no id -- a sync rewriting rows
in place, claims withdrawn -- is still seen. It is stamped by the ORM itself
(models.stamp_catalog_generation), so every path that writes the catalog
through a session stamps it, in any process, without remembering to.
"""
import shutil
from pathlib import Path

import pytest
from sqlmodel import Session, create_engine

from app.db.catalog_state import generation
from app.models.models import (
    CareLog, CareType, Plant, Species, SpeciesSource, User,
)


@pytest.fixture()
def engine(migrated_db_url, tmp_path):
    work = tmp_path / "generation.db"
    shutil.copy(Path(migrated_db_url.removeprefix("sqlite:///")), work)
    engine = create_engine(f"sqlite:///{work.as_posix()}")
    yield engine
    engine.dispose()


def _now(engine):
    with Session(engine) as s:
        return generation(s)


def _species(**over):
    return Species(**{"common_name": "Gen Fern", "scientific_name": "Generatia testus",
                      "source": SpeciesSource.claims, "source_ref": "b1-test.json",
                      "toxic_to_pets": None, "care_notes": "", **over})


def test_a_catalog_write_stamps_a_new_generation(engine):
    before = _now(engine)
    with Session(engine) as s:
        s.add(_species())
        s.commit()
    after = _now(engine)
    assert after and after != before


def test_an_in_place_change_stamps_it_and_a_no_op_does_not(engine):
    with Session(engine) as s:
        row = _species(scientific_name="Generatia rewritus")
        s.add(row)
        s.commit()
        sid = row.id
    stamped = _now(engine)
    with Session(engine) as s:
        row = s.get(Species, sid)
        row.common_name = row.common_name  # set, but nothing changed
        s.add(row)
        s.commit()
    assert _now(engine) == stamped
    with Session(engine) as s:
        row = s.get(Species, sid)
        row.care_data_status = "none"
        s.add(row)
        s.commit()
    assert _now(engine) != stamped


def test_writes_outside_the_catalog_leave_it(engine):
    stamped = _now(engine)
    with Session(engine) as s:
        user = User(email="generation@example.com")
        s.add(user)
        s.flush()
        s.add(_species(scientific_name="Generatia plantus"))
        s.commit()
    stamped = _now(engine)
    with Session(engine) as s:
        plant = Plant(nickname="Gen", species_id=1, user_id=None)
        s.add(plant)
        s.flush()
        s.add(CareLog(plant_id=plant.id, action=CareType.water))
        s.commit()
    assert _now(engine) == stamped


def test_a_rolled_back_write_leaves_the_committed_generation(engine):
    stamped = _now(engine)
    with Session(engine) as s:
        s.add(_species(scientific_name="Generatia abortus"))
        s.flush()
        assert generation(s) != stamped, "the writer sees its own stamp"
        s.rollback()
    assert _now(engine) == stamped
