"""Seed species and default growing_area from the JSON catalog.

Species data lives in species_catalog.json — add new plants there without
touching Python. The seed function is idempotent per scientific name:
existing species are skipped, new ones are inserted. Re-run after adding
entries to the catalog to pick up the new species on an existing database.

Run via `python -m app.data.seed`.
"""
import json
import os
import traceback
from pathlib import Path

from sqlmodel import Session, select

from app.db.database import engine, run_migrations
from app.models.models import (
    Species, CareSchedule, SpeciesTrait, LightNeed, CareType,
    GrowingArea, GrowingAreaType,
)


def _load_catalog() -> list[dict]:
    catalog_path = Path(__file__).parent / "species_catalog.json"
    with open(catalog_path, encoding="utf-8") as f:
        return json.load(f)


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
    """Seed species from species_catalog.json.

    Idempotent per scientific name — existing species are skipped, missing
    ones are added. Run after editing the catalog to pick up new entries
    on an existing database without wiping anything."""
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
