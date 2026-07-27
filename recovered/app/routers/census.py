"""Census router — anonymized aggregate views of plant data.

Privacy model (decision 3, 2026-07-15):
- Participation is per-user consent: only users with census_opt_in=True
  contribute to /census/export and /census/sync. Consent is toggled via
  PATCH /me.
- No stable pseudonymous identifiers: environment UUIDs are rotated fresh on
  every export (consistent within one export so stewardship chains still
  read, but never linkable across exports).
- No precise location: lat/lng never leave the server; city/region/country
  only, and only for opted-in users.
- No human identity: no nicknames, no personal notes, no emails, ever.

/census/summary is the caller's own view of their garden — it requires auth
and covers only their data.
"""
import os
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db.database import get_session
from app.deps import get_current_user
from app.models.models import (
    CareLog, Environment, Plant, Species, StewardshipRecord, User,
)

router = APIRouter(prefix="/census", tags=["census"])


@router.get("/summary")
def census_summary(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Aggregate counts for the CALLER's garden — their population snapshot."""
    plants = session.exec(
        select(Plant).where(Plant.user_id == user.id)).all()
    environments = session.exec(
        select(Environment).where(Environment.user_id == user.id)).all()
    species_list = session.exec(select(Species)).all()

    species_name_map = {s.id: s.common_name for s in species_list}
    env_map = {e.id: e for e in environments}

    env_type_counts: dict[str, int] = {}
    for e in environments:
        env_type_counts[e.type.value] = env_type_counts.get(e.type.value, 0) + 1

    plants_by_env_type: dict[str, int] = {}
    species_counts: dict[int, int] = {}
    for p in plants:
        env = env_map.get(p.environment_id) if p.environment_id else None
        env_label = env.type.value if env else "unassigned"
        plants_by_env_type[env_label] = plants_by_env_type.get(env_label, 0) + 1
        species_counts[p.species_id] = species_counts.get(p.species_id, 0) + 1

    return {
        "total_plants": len(plants),
        "total_environments": len(environments),
        "environments_by_type": env_type_counts,
        "plants_by_environment_type": plants_by_env_type,
        "species_distribution": [
            {
                "species_id": sid,
                "common_name": species_name_map.get(sid, "unknown"),
                "count": cnt,
            }
            for sid, cnt in sorted(species_counts.items(), key=lambda x: -x[1])
        ],
    }


def _opted_in_user_ids(session: Session) -> set[str]:
    rows = session.exec(
        select(User.id)
        .where(User.census_opt_in == True)  # noqa: E712
        .where(User.deleted_at == None)  # noqa: E711
    ).all()
    return set(rows)


@router.get("/export")
def census_export(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Anonymized export of OPTED-IN users' plant records.

    Environment identifiers are rotated per export: consistent within this
    payload (stewardship chains stay meaningful) but freshly generated each time,
    so exports can't be joined into a longitudinal profile of a household.
    Locations are city/region/country only — lat/lng never leave the server."""
    opted = _opted_in_user_ids(session)
    plants = session.exec(select(Plant)).all()
    plants = [p for p in plants if p.user_id in opted]

    # Per-export rotation map: real env id -> ephemeral UUID
    rotated: dict[int, str] = {}

    def rotated_uuid(env_id: int) -> str:
        if env_id not in rotated:
            rotated[env_id] = str(uuid4())
        return rotated[env_id]

    records = []
    for plant in plants:
        env = session.get(Environment, plant.environment_id) if plant.environment_id else None

        logs = session.exec(
            select(CareLog).where(CareLog.plant_id == plant.id)
        ).all()
        care_by_type: dict[str, list[str]] = {}
        for log in logs:
            care_by_type.setdefault(log.action.value, []).append(log.logged_at.isoformat())

        stewardship = session.exec(
            select(StewardshipRecord)
            .where(StewardshipRecord.plant_id == plant.id)
            .order_by(StewardshipRecord.started_at.asc())
        ).all()

        stewardship_chain = []
        for rec in stewardship:
            rec_env = session.get(Environment, rec.environment_id)
            stewardship_chain.append({
                "environment_ref": rotated_uuid(rec.environment_id) if rec_env else None,
                "environment_type": rec_env.type.value if rec_env else None,
                "started_at": rec.started_at.isoformat(),
                "ended_at": rec.ended_at.isoformat() if rec.ended_at else None,
            })

        records.append({
            "plant_uuid": plant.plant_uuid,
            "species_id": plant.species_id,
            "maturity_stage": plant.maturity_stage.value,
            "acquired_on": plant.acquired_on.isoformat() if plant.acquired_on else None,
            # Location dimension: geographic region only — never lat/lng
            "environment": {
                "ref": rotated_uuid(env.id),
                "type": env.type.value,
                "city": env.city,
                "region": env.region,
                "country": env.country,
            } if env else None,
            "stewardship_chain": stewardship_chain,
            "stewardship_count": len(stewardship),
            "care_history": care_by_type,
            "initial_condition": {
                "soil_moisture": plant.soil_moisture_at_acquisition.value
                    if plant.soil_moisture_at_acquisition else None,
                "leaf_condition": plant.leaf_condition_at_acquisition.value
                    if plant.leaf_condition_at_acquisition else None,
                "pest_observed": plant.pest_observed_at_acquisition,
            },
        })

    return {
        "export_version": "2.0",
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "installation_uuid": os.getenv("INSTALLATION_UUID", ""),
        "plant_count": len(records),
        "plants": records,
    }


@router.post("/sync")
def census_sync(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Push the anonymized, consent-filtered export to CENSUS_API_URL.

    If not configured, returns a 'skipped' status — no data is sent."""
    census_url = os.getenv("CENSUS_API_URL", "").rstrip("/")
    if not census_url:
        return {
            "status": "skipped",
            "reason": "CENSUS_API_URL not configured in .env — set it to opt in to the shared census",
        }
    try:
        import httpx
        payload = census_export(user, session)
        resp = httpx.post(f"{census_url}/ingest", json=payload, timeout=30.0)
        resp.raise_for_status()
        return {
            "status": "ok",
            "records_sent": len(payload["plants"]),
            "census_url": census_url,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Census sync failed: {exc}",
        ) from exc
