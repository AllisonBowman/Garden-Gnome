"""Curated prose follows species_catalog.json on every boot (ADR 0010).

seed() inserts a species once and never rewrites it. So the 25 mis-decoded
em dashes that sat in the file from the first commit, and the safety claims
and verdicts the care notes made until this pass, stay in any database seeded
before the file was mended -- production's among them -- however many
deploys follow. The refresh brings a curated row's care notes, soil and
schedule notes into line with the file on every boot, through the ORM so the
catalog generation moves, and touches nothing else.

The first test is the real case: a database seeded from the file as it stood
at 3f6d7da, the ship tip before the mending, then booted on today's. It reads
the old file out of git, so it needs a clone that has that commit; CI's
one-commit checkout does not, and the test skips there. The rest build their
own stale prose and run anywhere.
"""
import json
import shutil
import subprocess
from pathlib import Path

import pytest
from sqlmodel import Session, create_engine, delete, select

from app.db.catalog_state import generation
from app.models.models import (
    Authority, CareDataStatus, CareLog, CareSchedule, CareType, Claim, LightNeed,
    Plant, Species, SpeciesSource, SpeciesTrait, SyncState,
)
from tests.test_curated_notes import claims

REPO = Path(__file__).resolve().parents[2]
OLD_COMMIT = "3f6d7da"
#: An em dash's UTF-8 bytes read as cp1252 and saved again, as the old file had it.
GARBLED = "â€”"


@pytest.fixture()
def boot(migrated_db_url, tmp_path, monkeypatch, capsys):
    """A private database, and a cold start's seed() on it from a given file.

    `run(path)` seeds from `path` (the shipped file by default) and returns
    what the boot printed."""
    from app.data import seed as seed_module

    shipped = seed_module.CATALOG_PATH
    work = tmp_path / "refresh.db"
    shutil.copy(Path(migrated_db_url.removeprefix("sqlite:///")), work)
    engine = create_engine(f"sqlite:///{work.as_posix()}")
    with Session(engine) as s:
        # Whatever other tests left in the shared database, gone.
        for model in (Claim, Authority, CareLog, CareSchedule, SpeciesTrait,
                      Plant, Species, SyncState):
            s.exec(delete(model))
        s.commit()
    monkeypatch.setattr(seed_module, "engine", engine)
    monkeypatch.setattr(seed_module, "run_migrations", lambda: None)

    def run(path: Path | None = None) -> str:
        monkeypatch.setattr(seed_module, "CATALOG_PATH", path or shipped)
        capsys.readouterr()
        seed_module.seed()
        printed = capsys.readouterr()
        return printed.out + printed.err

    yield engine, run, shipped
    engine.dispose()


def _file_prose(path: Path) -> dict:
    """(scientific name, field) -> the file's text for every prose value."""
    prose = {}
    for entry in json.loads(path.read_text(encoding="utf-8")):
        name = entry["species"]["scientific_name"]
        prose[(name, "care_notes")] = entry["species"]["care_notes"]
        prose[(name, "soil_type")] = entry["species"]["soil_type"]
        for schedule in entry["schedules"]:
            prose[(name, f"schedules[{schedule['care_type']}].notes")] = schedule["notes"]
    return prose


def _db_prose(engine) -> dict:
    """The same, read off the curated rows in the database."""
    prose = {}
    with Session(engine) as s:
        for row in s.exec(select(Species).where(
                Species.source == SpeciesSource.curated)).all():
            prose[(row.scientific_name, "care_notes")] = row.care_notes
            prose[(row.scientific_name, "soil_type")] = row.soil_type
        for schedule, name in s.exec(
                select(CareSchedule, Species.scientific_name)
                .join(Species, CareSchedule.species_id == Species.id)
                .where(Species.source == SpeciesSource.curated)).all():
            prose[(name, f"schedules[{CareType(schedule.care_type).value}].notes")] = schedule.notes
    return prose


def _everything_else(engine) -> dict:
    """Every other column of every catalog row the refresh could reach."""
    def columns(row, skip=()):
        return {c.name: getattr(row, c.name) for c in row.__table__.columns
                if c.name not in skip}

    with Session(engine) as s:
        return {
            "species": sorted((columns(r, ("care_notes", "soil_type"))
                               for r in s.exec(select(Species)).all()),
                              key=lambda c: c["id"]),
            "schedules": sorted((columns(r, ("notes",))
                                 for r in s.exec(select(CareSchedule)).all()),
                                key=lambda c: c["id"]),
            "traits": sorted((columns(r) for r in s.exec(select(SpeciesTrait)).all()),
                             key=lambda c: c["id"]),
        }


def _generation(engine):
    with Session(engine) as s:
        return generation(s)


def _old_catalog(tmp_path: Path) -> Path:
    """species_catalog.json as it stood at 3f6d7da, saved under the temp dir."""
    try:
        shown = subprocess.run(
            ["git", "-C", str(REPO), "show",
             f"{OLD_COMMIT}:garden-gnome/app/data/species_catalog.json"],
            capture_output=True, check=False, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as exc:
        pytest.skip(f"git is not available to read {OLD_COMMIT}: {exc}")
    if shown.returncode != 0:
        pytest.skip(f"this clone does not have {OLD_COMMIT} (a one-commit "
                    f"checkout, as CI makes): {shown.stderr.decode()[:200]}")
    path = tmp_path / f"species_catalog_{OLD_COMMIT}.json"
    path.write_bytes(shown.stdout)
    return path


def test_a_database_seeded_from_3f6d7da_takes_todays_prose_on_the_next_boot(boot, tmp_path):
    engine, run, shipped = boot
    old_path = _old_catalog(tmp_path)

    out = run(old_path)
    assert "Seeded 129 new species from catalog." in out
    assert "curated text refreshed 0" in out
    before = _db_prose(engine)
    assert before == _file_prose(old_path)
    assert sum(text.count(GARBLED) for text in before.values()) == 25
    claimed = {key for key, text in before.items() if claims(text, key[0])}
    assert claimed, "the old notes made safety claims"
    stamped = _generation(engine)
    untouched = _everything_else(engine)

    today = _file_prose(shipped)
    changed = {key for key, text in before.items() if key in today and text != today[key]}
    assert claimed <= changed

    out = run()
    assert "Species catalog already up to date." in out
    assert f"curated text refreshed {len(changed)}" in out
    after = _db_prose(engine)
    assert set(after) == set(before)
    assert after == {key: today[key] for key in after}
    assert not any(GARBLED in text for text in after.values())
    assert not [key for key, text in after.items() if claims(text, key[0])]
    assert _generation(engine) != stamped, "phones must see the new text"
    assert _everything_else(engine) == untouched

    stamped = _generation(engine)
    out = run()
    assert "curated text refreshed 0" in out
    assert _db_prose(engine) == after
    assert _generation(engine) == stamped, "a boot that changes nothing stamps nothing"


def test_the_refresh_rewrites_curated_prose_and_nothing_else(boot):
    engine, run, shipped = boot
    run()
    today = _file_prose(shipped)
    with Session(engine) as s:
        spider = s.exec(select(Species).where(
            Species.scientific_name == "Chlorophytum comosum")).one()
        water = s.exec(select(CareSchedule).where(
            CareSchedule.species_id == spider.id,
            CareSchedule.care_type == CareType.water)).one()
        # Stale prose, the kind production holds.
        spider.care_notes = "Pet-safe. " + spider.care_notes
        spider.soil_type = spider.soil_type.replace("-", GARBLED)
        water.notes = "Old note."
        # What the refresh must leave alone, set to values the file does not
        # hold. The pet flag is harm-capable; the rest belong to the claim
        # sync, the migrations or the schedule itself.
        spider.toxic_to_pets = None
        spider.light_need = LightNeed.low
        spider.common_name = "Airplane Plant"
        spider.care_data_status = CareDataStatus.sourced
        spider.light_fc_min = 150
        water.interval_days_min, water.interval_days_max = 3, 4
        # Another pipeline's row under a curated name is not the file's.
        stray = Species(common_name="Spider Plant (import)",
                        scientific_name="Chlorophytum comosum",
                        source=SpeciesSource.perenual,
                        care_notes="Imported prose.", soil_type="Imported soil")
        s.add(stray)
        # A schedule the database lacks is not prose, and is not added back.
        pothos = s.exec(select(Species).where(
            Species.scientific_name == "Epipremnum aureum")).one()
        s.delete(s.exec(select(CareSchedule).where(
            CareSchedule.species_id == pothos.id,
            CareSchedule.care_type == CareType.prune)).one())
        s.commit()
        spider_id, water_id, stray_id, pothos_id = spider.id, water.id, stray.id, pothos.id
    stamped = _generation(engine)
    untouched = _everything_else(engine)

    out = run()

    assert "curated text refreshed 3" in out
    assert _generation(engine) != stamped
    with Session(engine) as s:
        spider = s.get(Species, spider_id)
        water = s.get(CareSchedule, water_id)
        assert spider.care_notes == today[("Chlorophytum comosum", "care_notes")]
        assert spider.soil_type == today[("Chlorophytum comosum", "soil_type")]
        assert water.notes == today[("Chlorophytum comosum", "schedules[water].notes")]
        assert spider.toxic_to_pets is None
        assert spider.light_need == LightNeed.low
        assert spider.common_name == "Airplane Plant"
        assert spider.care_data_status == CareDataStatus.sourced
        assert spider.light_fc_min == 150
        assert (water.interval_days_min, water.interval_days_max) == (3, 4)
        stray = s.get(Species, stray_id)
        assert (stray.care_notes, stray.soil_type) == ("Imported prose.", "Imported soil")
        assert not s.exec(select(CareSchedule).where(
            CareSchedule.species_id == pothos_id,
            CareSchedule.care_type == CareType.prune)).all()
    assert _everything_else(engine) == untouched

    stamped = _generation(engine)
    assert "curated text refreshed 0" in run()
    assert _generation(engine) == stamped


def test_a_failing_refresh_rolls_back_and_does_not_stop_the_boot(boot, monkeypatch):
    """seed() runs before uvicorn on every boot, so a defect here must cost a
    stale note, never the API, and must not leave half a refresh behind."""
    from app.data import seed as seed_module

    engine, run, shipped = boot

    def half_done(session, catalog):
        row = session.exec(select(Species)).first()
        row.care_notes = "half-done"
        session.flush()
        raise RuntimeError("simulated defect")

    monkeypatch.setattr(seed_module, "refresh_curated_text", half_done)
    out = run()
    assert "Seeded 129 new species from catalog." in out
    assert "RuntimeError: simulated defect" in out
    assert "curated text refresh skipped" in out
    with Session(engine) as s:
        assert len(s.exec(select(Species)).all()) == 129
        assert not s.exec(select(Species).where(Species.care_notes == "half-done")).all()
    assert _db_prose(engine) == _file_prose(shipped)
