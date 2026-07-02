"""Census router — anonymized aggregate views of plant data across all environments.

The census layer is intentionally detached from human identity: no nicknames,
no personal notes, no installation-specific context. Plants are identified only
by their canonical plant_uuid (persistent across owner/environment transfers),
and locations are expressed as city/region/country — not precise addresses.

This makes the exported data suitable for environmental stewardship analysis
(species distribution, care health trends by geography and environment type)
without exposing personally identifiable information."""
import os
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db.database import get_session
from app.models.models import (
    CareLog, Environment, Plant, Species, StewardshipRecord,
)

router = APIRouter(prefix="/census", tags=["census"])


@router.get("/summary")
def census_summary(session: Session = Depends(get_session)):
    """Aggregate counts — total plants/environments, breakdown by environment
    type, species distribution. Useful for a quick population snapshot."""
    plants = session.exec(select(Plant)).all()
    environments = session.exec(select(Environment)).all()
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


@router.get("/export")
def census_export(session: Session = Depends(get_session)):
    """Full anonymized export of all plant records.

    Each plant is identified by its plant_uuid, which persists across transfers
    so a central aggregator won't double-count the same physical plant if it
    moves between installations. PII fields (nickname, personal care notes) are
    excluded. Location is city/region/country only."""
    plants = session.exec(select(Plant)).all()
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

        # Stewardship dimension: chain of custody without PII. Each record
        # links to an environment UUID (not a person or installation name).
        stewardship_chain = []
        for rec in stewardship:
            rec_env = session.get(Environment, rec.environment_id)
            stewardship_chain.append({
                "environment_uuid": rec_env.uuid if rec_env else None,
                "environment_type": rec_env.type.value if rec_env else None,
                "started_at": rec.started_at.isoformat(),
                "ended_at": rec.ended_at.isoformat() if rec.ended_at else None,
            })

        records.append({
            "plant_uuid": plant.plant_uuid,
            "species_id": plant.species_id,
            "maturity_stage": plant.maturity_stage.value,
            "acquired_on": plant.acquired_on.isoformat() if plant.acquired_on else None,
            # Location dimension: geographic region, not specific address
            "environment": {
                "uuid": env.uuid,
                "type": env.type.value,
                "city": env.city,
                "region": env.region,
                "country": env.country,
            } if env else None,
            # Stewardship dimension: chain of custody over time
            "stewardship_chain": stewardship_chain,
            "stewardship_count": len(stewardship),
            # Care history: timestamps by care type for frequency analysis
            "care_history": care_by_type,
            # Initial health snapshot for longitudinal health tracking
            "initial_condition": {
                "soil_moisture": plant.soil_moisture_at_acquisition.value
                    if plant.soil_moisture_at_acquisition else None,
                "leaf_condition": plant.leaf_condition_at_acquisition.value
                    if plant.leaf_condition_at_acquisition else None,
                "pest_observed": plant.pest_observed_at_acquisition,
            },
        })

    return {
        "export_version": "1.0",
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "installation_uuid": os.getenv("INSTALLATION_UUID", ""),
        "plant_count": len(records),
        "plants": records,
    }


@router.post("/sync")
def census_sync(session: Session = Depends(get_session)):
    """Push the anonymized export to the configured CENSUS_API_URL.

    Set CENSUS_API_URL in .env to opt in to contributing to the shared census.
    If not configured, returns a 'skipped' status — no data is sent."""
    census_url = os.getenv("CENSUS_API_URL", "").rstrip("/")
    if not census_url:
        return {
            "status": "skipped",
            "reason": "CENSUS_API_URL not configured in .env — set it to opt in to the shared census",
        }
    try:
        import httpx
        payload = census_export(session)
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
