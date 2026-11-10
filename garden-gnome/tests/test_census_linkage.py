"""Two census exports cannot be joined record for record.

A fresh salt per export kept the plant_ref from linking two exports, but the
records still did it themselves: they came out in row order, the same in
every export, and each carried its care dates, so the dates in one export were
the start of the dates in the next. A dozen watering days single out one plant
in a thousand. Export 4.1 shuffles the records and counts care per month.

What is still true, and what the consent copy says: a plant's monthly counts
can resemble the same plant's in the next export. The test below builds the
case where they cannot tell plants apart -- neighbours who planted the same
species the same month and water about as often -- because that is the case
a day-level export gave away and a monthly one does not.
"""
import json
import shutil
from datetime import date, datetime
from pathlib import Path

import pytest
from sqlmodel import Session, create_engine, select

from app.models.models import (
    CareLog, CareType, GrowingArea, GrowingAreaType, Plant, Species,
    StewardshipRecord, User,
)
from app.routers import census

CITY = "Linkville"
HOUSEHOLDS = 12


@pytest.fixture()
def street(migrated_db_url, tmp_path):
    """Twelve opted-in neighbours, one tomato bed each, in a private database."""
    work = tmp_path / "census.db"
    shutil.copy(Path(migrated_db_url.removeprefix("sqlite:///")), work)
    engine = create_engine(f"sqlite:///{work.as_posix()}")
    plant_ids = []
    with Session(engine) as s:
        species = Species(common_name="Linktest Tomato",
                          scientific_name="Solanum linktestii")
        s.add(species)
        s.flush()
        for i in range(HOUSEHOLDS):
            user = User(email=f"neighbour{i}@example.com", census_opt_in=True)
            s.add(user)
            s.flush()
            area = GrowingArea(name="Bed", type=GrowingAreaType.home,
                               user_id=user.id, city=CITY, region="ZZ",
                               country="US")
            s.add(area)
            s.flush()
            plant = Plant(species_id=species.id, growing_area_id=area.id,
                          user_id=user.id, acquired_on=date(2026, 4, 1 + i))
            s.add(plant)
            s.flush()
            # Added through the app, a plant's stewardship starts the day it
            # was added: a near-unique day, before any care is logged.
            s.add(StewardshipRecord(plant_id=plant.id, growing_area_id=area.id,
                                    started_at=datetime(2026, 4, 1 + i, 8, i)))
            # Three waterings in May, on days no two neighbours share.
            for day in (1 + i, 10 + i, 19 + (i % 9)):
                s.add(CareLog(plant_id=plant.id, action=CareType.water,
                              logged_at=datetime(2026, 5, day, 7, i)))
            plant_ids.append(plant.id)
        s.commit()
    yield engine, plant_ids
    engine.dispose()


def _export(engine) -> list[dict]:
    with Session(engine) as s:
        body = census.build_export(s)
    assert body["export_version"] == "4.1"
    return [r for r in body["plants"]
            if (r["growing_area"] or {}).get("city") == CITY]


def _static(record: dict) -> str:
    """Everything in a record that should not change between two exports
    taken a month apart, without its per-export refs."""
    area = dict(record["growing_area"])
    area.pop("ref")
    return json.dumps({
        "area": area,
        **{k: record[k] for k in (
            "quantity", "species_id", "maturity_stage", "acquired_month",
            "stewardship_chain", "stewardship_count", "initial_condition")},
        "split": record["split_from_ref"] is None,
    }, sort_keys=True)


def _could_be(earlier: dict, later: dict) -> bool:
    """Whether `later` is consistent with being `earlier`, a while on: the
    same static facts, and at least as much care in every month."""
    if _static(earlier) != _static(later):
        return False
    for action, months in earlier["care_history"].items():
        for month, count in months.items():
            if later["care_history"].get(action, {}).get(month, 0) < count:
                return False
    return True


def test_the_census_content_does_not_link_two_exports(street):
    engine, plant_ids = street
    first = _export(engine)
    # A month of care later: one more watering each, on different days.
    with Session(engine) as s:
        for i, plant_id in enumerate(plant_ids):
            s.add(CareLog(plant_id=plant_id, action=CareType.water,
                          logged_at=datetime(2026, 6, 2 + i, 7, 30)))
        s.commit()
    second = _export(engine)
    assert len(first) == len(second) == HOUSEHOLDS

    # No identifier is shared ...
    assert {r["plant_ref"] for r in first}.isdisjoint(
        {r["plant_ref"] for r in second})
    assert {r["growing_area"]["ref"] for r in first}.isdisjoint(
        {r["growing_area"]["ref"] for r in second})
    # ... no day is exported ...
    for record in first + second:
        assert record["care_history"] == {
            "water": {"2026-05": 3, **({"2026-06": 1} if record in second else {})}}
        assert record["stewardship_chain"] == [
            {"started_month": "2026-04", "ended_month": None}]
    # ... and so every record of the first export is as consistent with every
    # record of the second as with its own: none can be matched to one.
    for record in first:
        matches = [later for later in second if _could_be(record, later)]
        assert len(matches) == HOUSEHOLDS


def test_the_same_street_was_linkable_by_its_days(street):
    """The fixture has teeth: by the days 4.0 exported -- care dates and the
    stewardship start -- every one of these plants was unique."""
    engine, plant_ids = street
    with Session(engine) as s:
        fingerprints = set()
        for plant_id in plant_ids:
            days = sorted(log.logged_at.date().isoformat() for log in s.exec(
                select(CareLog).where(CareLog.plant_id == plant_id)))
            start = s.exec(select(StewardshipRecord).where(
                StewardshipRecord.plant_id == plant_id)).one().started_at.date()
            fingerprints.add((tuple(days), start))
    assert len(fingerprints) == HOUSEHOLDS


def test_records_go_out_in_a_fresh_order_each_export(street, monkeypatch):
    """Position was the database's row order, the same every time: record n
    of one export was record n of the next. The order is now drawn per
    export, so with the salt pinned (to see the same refs twice) the two
    orders differ -- by chance alike once in 12! exports."""
    engine, _ = street
    monkeypatch.setattr(census, "_new_export_salt", lambda: b"s" * 32)
    orders = [[r["plant_ref"] for r in _export(engine)] for _ in range(2)]
    assert sorted(orders[0]) == sorted(orders[1])
    assert orders[0] != orders[1]


def test_the_export_is_shuffled_by_the_system_random_source(street, monkeypatch):
    engine, _ = street
    seen = []
    monkeypatch.setattr(census, "_shuffle", lambda records: seen.append(len(records)))
    with Session(engine) as s:
        body = census.build_export(s)
    assert seen == [len(body["plants"])]
