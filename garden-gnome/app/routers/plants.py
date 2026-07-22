import os
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlmodel import Session, select

from app.db.database import get_session
from app.deps import get_current_user
from app.models.models import (
    CareLog, CareSchedule, CareType, Environment, EnvironmentType, Plant,
    Species, StewardshipRecord, User,
)
from app.models.schemas import (
    AdviceRequest, CareLogCreate, PlantCreate, PlantRead, PlantTransferRequest,
    StewardshipRecordRead, TimelineEntry, CareTypeSummary, PlantTimelineSummary,
)
from app.services.advisor import get_care_advice
from app.services.vision import diagnose_photo

router = APIRouter(prefix="/plants", tags=["plants"])

ALLOWED_PHOTO_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_PHOTO_BYTES = 8 * 1024 * 1024  # 8MB


def _installation_uuid() -> str:
    return os.getenv("INSTALLATION_UUID", "")


def _owned_plant(plant_id: int, user: User, session: Session) -> Plant:
    """Load a plant owned by the caller; 404 otherwise.

    404 (not 403) for other users' plants, so plant ids can't be probed."""
    plant = session.get(Plant, plant_id)
    if plant is None or plant.user_id != user.id:
        raise HTTPException(status_code=404, detail="Plant not found")
    return plant


def _owned_environment(env_id: int, user: User, session: Session) -> Environment:
    env = session.get(Environment, env_id)
    if env is None or env.user_id != user.id:
        raise HTTPException(status_code=404, detail="Environment not found")
    return env


@router.post("/", response_model=PlantRead, status_code=201)
def create_plant(
    payload: PlantCreate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if not session.get(Species, payload.species_id):
        raise HTTPException(status_code=400, detail="species_id does not exist")

    # Resolve environment: a provided id must belong to the caller; otherwise
    # fall back to the caller's default (oldest) environment, creating "My
    # Home" if the account somehow has none. NEVER "first environment in the
    # DB" — that leaked across accounts once environments became user-owned.
    environment_id = payload.environment_id
    if environment_id is not None:
        _owned_environment(environment_id, user, session)
    else:
        default_env = session.exec(
            select(Environment)
            .where(Environment.user_id == user.id)
            .order_by(Environment.id.asc())
        ).first()
        if default_env is None:
            default_env = Environment(
                name="My Home", type=EnvironmentType.home, user_id=user.id)
            session.add(default_env)
            session.flush()
        environment_id = default_env.id

    data = payload.model_dump()
    data["environment_id"] = environment_id
    # Stamp ownership; keeps plant.user_id == environment.user_id invariant
    plant = Plant(**data, user_id=user.id)
    session.add(plant)
    session.commit()
    session.refresh(plant)

    # Open the first stewardship record for this plant
    if environment_id is not None:
        session.add(StewardshipRecord(
            plant_id=plant.id,
            environment_id=environment_id,
            installation_uuid=_installation_uuid(),
        ))
        session.commit()

    # If any intake condition was captured, log it as the plant's first
    # timeline entry so the day-zero baseline shows up in its history.
    if (
        plant.soil_moisture_at_acquisition
        or plant.leaf_condition_at_acquisition
        or plant.pest_observed_at_acquisition
        or plant.intake_notes
    ):
        parts = []
        if plant.soil_moisture_at_acquisition:
            parts.append(f"soil {plant.soil_moisture_at_acquisition.value}")
        if plant.leaf_condition_at_acquisition:
            parts.append(f"leaves {plant.leaf_condition_at_acquisition.value}")
        if plant.pest_observed_at_acquisition:
            parts.append("pests observed")
        if plant.intake_notes:
            parts.append(plant.intake_notes)
        session.add(CareLog(
            plant_id=plant.id,
            action=CareType.other,
            notes="Intake condition: " + "; ".join(parts),
            logged_at=plant.created_at,
        ))
        session.commit()

    return plant


@router.get("/", response_model=list[PlantRead])
def list_plants(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return session.exec(select(Plant).where(Plant.user_id == user.id)).all()


@router.get("/{plant_id}", response_model=PlantRead)
def get_plant(
    plant_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return _owned_plant(plant_id, user, session)


@router.delete("/{plant_id}", status_code=204)
def delete_plant(
    plant_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    plant = _owned_plant(plant_id, user, session)
    session.delete(plant)
    session.commit()


@router.post("/{plant_id}/transfer")
def transfer_plant(
    plant_id: int,
    payload: PlantTransferRequest,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Move a plant to a different environment, preserving its plant_uuid.

    Closes the current stewardship record and opens a new one. The plant's
    canonical UUID doesn't change, so the census treats it as the same
    physical plant — not a new entry. A transfer event is auto-logged to
    the plant's timeline.

    v1 rule (decision 4): BOTH sides must belong to the caller — the plant
    (and thus its current environment) and the destination. No cross-account
    transfers."""
    plant = _owned_plant(plant_id, user, session)
    if plant.environment_id is not None:
        # Belt-and-braces: the from-side must also be caller-owned even if
        # the plant/env ownership invariant ever drifted.
        _owned_environment(plant.environment_id, user, session)

    new_env = _owned_environment(payload.to_environment_id, user, session)

    # Close the active stewardship record
    current = session.exec(
        select(StewardshipRecord)
        .where(StewardshipRecord.plant_id == plant_id)
        .where(StewardshipRecord.ended_at == None)  # noqa: E711
    ).first()
    if current:
        current.ended_at = datetime.utcnow()
        session.add(current)

    # Open new stewardship in the destination environment
    session.add(StewardshipRecord(
        plant_id=plant_id,
        environment_id=payload.to_environment_id,
        installation_uuid=_installation_uuid(),
        transfer_notes=payload.transfer_notes,
    ))

    # Update the plant's current environment pointer
    plant.environment_id = payload.to_environment_id
    session.add(plant)
    session.commit()

    # Log the transfer event to the care timeline
    note_parts = [f"Transferred to '{new_env.name}' ({new_env.type.value})"]
    if payload.transfer_notes:
        note_parts.append(payload.transfer_notes)
    session.add(CareLog(
        plant_id=plant_id,
        action=CareType.other,
        notes="; ".join(note_parts),
    ))
    session.commit()
    session.refresh(plant)
    return plant


@router.get("/{plant_id}/stewardship", response_model=list[StewardshipRecordRead])
def get_plant_stewardship(
    plant_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Full chain-of-custody history for a plant."""
    _owned_plant(plant_id, user, session)
    return session.exec(
        select(StewardshipRecord)
        .where(StewardshipRecord.plant_id == plant_id)
        .order_by(StewardshipRecord.started_at.asc())
    ).all()


@router.post("/{plant_id}/logs", response_model=CareLog, status_code=201)
def add_care_log(
    plant_id: int,
    payload: CareLogCreate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    _owned_plant(plant_id, user, session)
    log = CareLog(plant_id=plant_id, **payload.model_dump())
    session.add(log)
    session.commit()
    session.refresh(log)
    return log


@router.get("/{plant_id}/logs", response_model=list[CareLog])
def list_care_logs(
    plant_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    _owned_plant(plant_id, user, session)
    return session.exec(
        select(CareLog).where(CareLog.plant_id == plant_id)
    ).all()


@router.get("/{plant_id}/timeline", response_model=list[TimelineEntry])
def get_plant_timeline(
    plant_id: int,
    since: Optional[date] = None,
    until: Optional[date] = None,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Chronological care history. Each entry's `days_since_previous` is the
    gap from the prior log of the *same* care type (computed over full
    history, even if since/until narrows what's returned) -- this is the
    season-over-season comparison primitive: call twice with different
    since/until windows to compare "this time last summer vs now"."""
    _owned_plant(plant_id, user, session)

    all_logs = session.exec(
        select(CareLog)
        .where(CareLog.plant_id == plant_id)
        .order_by(CareLog.logged_at.asc())
    ).all()

    last_seen: dict[CareType, datetime] = {}
    entries: list[TimelineEntry] = []
    for log in all_logs:
        prev = last_seen.get(log.action)
        gap = (log.logged_at - prev).days if prev else None
        last_seen[log.action] = log.logged_at

        if since and log.logged_at.date() < since:
            continue
        if until and log.logged_at.date() > until:
            continue

        entries.append(TimelineEntry(
            id=log.id,
            action=log.action,
            notes=log.notes,
            logged_at=log.logged_at,
            days_since_previous=gap,
        ))
    return entries


@router.get("/{plant_id}/timeline/summary", response_model=PlantTimelineSummary)
def get_plant_timeline_summary(
    plant_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Per-care-type stats (count, last logged, actual avg/min/max interval)
    compared against the species' scheduled interval. Includes scheduled care
    types with zero logs so the UI can flag "never logged" gaps."""
    plant = _owned_plant(plant_id, user, session)

    all_logs = session.exec(
        select(CareLog)
        .where(CareLog.plant_id == plant_id)
        .order_by(CareLog.logged_at.asc())
    ).all()

    schedules = {
        cs.care_type: cs
        for cs in session.exec(
            select(CareSchedule).where(CareSchedule.species_id == plant.species_id)
        ).all()
    }

    by_type: dict[CareType, list[CareLog]] = {}
    for log in all_logs:
        by_type.setdefault(log.action, []).append(log)

    summaries = []
    for care_type in set(schedules) | set(by_type):
        logs = by_type.get(care_type, [])
        intervals = [
            (logs[i].logged_at - logs[i - 1].logged_at).days
            for i in range(1, len(logs))
        ]
        sched = schedules.get(care_type)
        summaries.append(CareTypeSummary(
            care_type=care_type,
            count=len(logs),
            last_logged_at=logs[-1].logged_at if logs else None,
            avg_interval_days=round(sum(intervals) / len(intervals), 1) if intervals else None,
            min_interval_days=min(intervals) if intervals else None,
            max_interval_days=max(intervals) if intervals else None,
            scheduled_interval_days_min=sched.interval_days_min if sched else None,
            scheduled_interval_days_max=sched.interval_days_max if sched else None,
        ))

    summaries.sort(key=lambda s: s.care_type.value)
    return PlantTimelineSummary(plant_id=plant_id, nickname=plant.nickname, by_care_type=summaries)


@router.post("/{plant_id}/advice")
def advise_plant(
    plant_id: int,
    payload: Optional[AdviceRequest] = None,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Generate care advice for a plant by reasoning over its species care
    facts, care schedules (ground truth), and recent care history. Optionally
    accepts free-text `symptoms` in the body for conversational diagnosis."""
    symptoms = payload.symptoms if payload else ""

    plant = _owned_plant(plant_id, user, session)

    species = session.get(Species, plant.species_id)
    if not species:
        raise HTTPException(status_code=500, detail="Plant's species missing")

    recent_logs = session.exec(
        select(CareLog)
        .where(CareLog.plant_id == plant_id)
        .order_by(CareLog.logged_at.desc())
        .limit(10)
    ).all()

    care_schedules = session.exec(
        select(CareSchedule)
        .where(CareSchedule.species_id == species.id)
    ).all()

    try:
        result = get_care_advice(species, plant, recent_logs, care_schedules, symptoms)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e

    return {
        "plant_id": plant_id,
        "nickname": plant.nickname,
        "species": species.common_name,
        **result,
    }


@router.post("/{plant_id}/diagnose-photo")
async def diagnose_plant_photo(
    plant_id: int,
    photo: UploadFile = File(...),
    notes: str = Form(""),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Photo-based diagnosis (Phase 3). No hosted vision backend is
    configured (VISION_BACKEND knows only `stub`), so this answers with a
    friendly not-enabled message until a backend direction is chosen.
    The diagnosis is auto-logged to the plant's timeline."""
    plant = _owned_plant(plant_id, user, session)

    species = session.get(Species, plant.species_id)
    if not species:
        raise HTTPException(status_code=500, detail="Plant's species missing")

    if photo.content_type not in ALLOWED_PHOTO_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image type '{photo.content_type}'. Use JPEG, PNG, or WebP.",
        )

    image_bytes = await photo.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty photo upload.")
    if len(image_bytes) > MAX_PHOTO_BYTES:
        raise HTTPException(status_code=400, detail="Image too large (max 8MB).")

    care_schedules = session.exec(
        select(CareSchedule).where(CareSchedule.species_id == species.id)
    ).all()

    try:
        result = await diagnose_photo(species, plant, care_schedules, image_bytes, notes)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e

    # Only a real analysis belongs on the permanent timeline. The stub never
    # examined the photo, so logging its placeholder would both clutter the
    # plant's history and feed non-diagnosis text back into future advisor
    # prompts via recent care logs.
    if result["backend"] != "stub":
        session.add(CareLog(
            plant_id=plant_id,
            action=CareType.other,
            notes=f"Photo diagnosis: {result['diagnosis']}",
        ))
        session.commit()

    return {
        "plant_id": plant_id,
        "nickname": plant.nickname,
        "species": species.common_name,
        **result,
    }
