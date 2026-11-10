"""Seed species and default growing_area from the JSON catalog.

Species data lives in species_catalog.json — add new plants there without
touching Python. The seed function is idempotent per scientific name:
missing species are inserted, and a species already in the table is never
inserted again. Re-run after adding entries to the catalog to pick up the
new species on an existing database.

The file's prose is the exception to "never touched again". A curated row's
care notes, its soil and the notes on its schedules are the file's to say --
no claim backs them and the resolver never writes them -- so every run
brings them into line with the file (ADR 0010). Nothing else on an existing
row moves.

Run via `python -m app.data.seed`.
"""
import json
import os
import traceback
from pathlib import Path

from sqlmodel import Session, col, select

from app.db.database import engine, run_migrations
from app.models.models import (
    Species, CareSchedule, SpeciesTrait, LightNeed, CareType,
    GrowingArea, GrowingAreaType, SpeciesSource,
)

CATALOG_PATH = Path(__file__).parent / "species_catalog.json"

#: The Species columns whose text follows the file on every boot. With each
#: schedule's `notes`, the whole of the prose the file states and no source
#: does. Never a resolved column, never a harm-capable one: `toxic_to_pets`
#: and the legacy care values stay as the claim sync and the migrations
#: left them.
CURATED_TEXT = ("care_notes", "soil_type")


def _load_catalog() -> list[dict]:
    with open(CATALOG_PATH, encoding="utf-8") as f:
        return json.load(f)


def refresh_curated_text(session: Session, catalog: list[dict]) -> int:
    """Bring curated rows' prose into line with the file; how many values moved.

    seed() inserts a species once and never rewrites it, so an edit to a
    note in species_catalog.json -- 25 em dashes mis-decoded since the first
    commit, safety claims taken out -- never reached a database that already
    had the row. This closes that gap for the prose and nothing else
    (ADR 0010): `care_notes` and `soil_type` on each row the file created,
    and `notes` on that row's schedules, each set to the file's text
    wherever the two differ.

    A row the file created is a `curated` row under the entry's scientific
    name, the same exact-name match that decides whether seed() inserts. A
    row from another pipeline that happens to carry the name is not the
    file's, and a schedule the database lacks is not added: what gets
    scheduled is not prose. The writes go through the ORM, so the flush that
    commits them stamps a new catalog generation (models.CATALOG_ROWS) and
    the caches keyed on it rebuild; a run that changes nothing stamps none.
    """
    entries = {entry["species"]["scientific_name"]: entry for entry in catalog}
    rows = session.exec(select(Species).where(
        Species.source == SpeciesSource.curated,
        col(Species.scientific_name).in_(list(entries)),
    )).all()
    schedules = {}
    if rows:
        for schedule in session.exec(select(CareSchedule).where(
                col(CareSchedule.species_id).in_([row.id for row in rows]))).all():
            schedules[(schedule.species_id, CareType(schedule.care_type))] = schedule

    moved = 0
    for row in rows:
        entry = entries[row.scientific_name]
        for field in CURATED_TEXT:
            text = entry["species"].get(field)
            if (getattr(row, field) or "") != (text or ""):
                setattr(row, field, text)
                moved += 1
        for listed in entry["schedules"]:
            schedule = schedules.get((row.id, CareType(listed["care_type"])))
            text = listed.get("notes") or ""
            if schedule is not None and (schedule.notes or "") != text:
                schedule.notes = text
                moved += 1
    return moved


def seed_default_growing_area() -> None:
    """DEV-ONLY (decision 5, 2026-07-15): create a global default GrowingArea.

    In production, every account gets its own "My Home" growing area at
    sign-up (Phase 5) and plant creation self-heals a missing default — a
    global unowned growing area no longer makes sense. Set GG_DEV_SEED=1 to
    keep the old single-user dev convenience (attached to dev@local)."""
    if os.getenv("GG_DEV_SEED", "") != "1":
        return
    with Session(engine) as session:
        existing = session.exec(select(GrowingArea)).first()
        if existing:
            return
        env_name = os.getenv("DEFAULT_ENV_NAME", "My Garden")
        env_type_str = os.getenv("DEFAULT_ENV_TYPE", "home")
        try:
            env_type = GrowingAreaType(env_type_str)
        except ValueError:
            env_type = GrowingAreaType.home

        # Attach to dev@local so the growing area is owned even in dev
        from datetime import datetime

        from app.models.models import User
        dev = session.exec(
            select(User).where(User.email == "dev@local")).first()
        if dev is None:
            dev = User(email="dev@local", display_name="Dev User",
                       created_at=datetime.utcnow())
            session.add(dev)
            session.flush()
        env = GrowingArea(name=env_name, type=env_type, user_id=dev.id)
        session.add(env)
        session.commit()
        print(f"Created default growing_area: '{env_name}' ({env_type.value})")


def seed() -> None:
    """Seed species from species_catalog.json, and refresh curated prose.

    Idempotent per scientific name — existing species are skipped, missing
    ones are added. Run after editing the catalog to pick up new entries
    on an existing database without wiping anything.

    Then the curated rows' prose follows the file (refresh_curated_text).
    That step is fenced like the claim sync in main(): this runs before
    uvicorn on every boot, and a note left stale is recoverable where a
    container that will not start is not. Its line in the log says which
    happened: "curated text refreshed N", or "curated text refresh
    skipped" after a traceback."""
    # Alembic is the sole schema authority (Phase 1+). Bring the DB to head
    # BEFORE querying — the Dockerfile runs this seed before uvicorn, so it
    # must migrate itself. Using create_all here would build the auth tables
    # outside Alembic and collide with the migrations on the next boot.
    run_migrations()
    catalog = _load_catalog()
    added = 0
    with Session(engine) as session:
        for entry in catalog:
            sci_name = entry["species"]["scientific_name"]
            if session.exec(select(Species).where(Species.scientific_name == sci_name)).first():
                continue

            s_dict = dict(entry["species"])
            s_dict["light_need"] = LightNeed(s_dict["light_need"])
            species = Species(**s_dict)
            session.add(species)
            session.flush()

            for sched in entry["schedules"]:
                sd = dict(sched)
                sd["care_type"] = CareType(sd["care_type"])
                session.add(CareSchedule(species_id=species.id, **sd))

            for trait in entry.get("traits", []):
                session.add(SpeciesTrait(species_id=species.id, **trait))

            added += 1

        session.commit()

    if added:
        print(f"Seeded {added} new species from catalog.")
    else:
        print("Species catalog already up to date.")

    try:
        with Session(engine) as session:
            refreshed = refresh_curated_text(session, catalog)
            session.commit()
        print(f"curated text refreshed {refreshed}")
    except Exception:  # noqa: BLE001 -- a stale note must not stop the boot
        traceback.print_exc()
        print("curated text refresh skipped")


def main() -> None:
    """Everything a cold start needs: schema, catalog, growing_area, evidence.

    The claim sync is fenced. It reads every tranche file and rewrites the
    species table, and a defect in either must never become an API outage --
    the catalog serving stale care data is recoverable, a container that will
    not boot is not. So it logs and moves on, and this exits 0 regardless.
    """
    seed()
    seed_default_growing_area()
    try:
        from app.data.claims.sync import describe, sync_catalog

        with Session(engine) as session:
            report = sync_catalog(session)
        print(describe(report))
    except Exception:  # noqa: BLE001 -- surviving it is the whole point
        traceback.print_exc()
        print("claim sync skipped")


if __name__ == "__main__":
    main()
