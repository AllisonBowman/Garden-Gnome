from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.db.database import get_session
from app.models.models import CareSchedule, Species, SpeciesTrait
from app.models.schemas import (
    SpeciesCreate, SpeciesDetail, SpeciesGenerateRequest,
)

router = APIRouter(prefix="/species", tags=["species"])

ALLOWED_PHOTO_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_PHOTO_BYTES = 8 * 1024 * 1024  # 8MB


def _load_with_relations(species_id: int, session: Session) -> Species:
    return session.exec(
        select(Species)
        .where(Species.id == species_id)
        .options(selectinload(Species.care_schedules), selectinload(Species.traits))
    ).first()


def _create_one(entry: SpeciesCreate, session: Session) -> Species:
    """Insert a single species with its schedules and traits. Caller commits."""
    species_data = entry.model_dump(exclude={"schedules", "traits"})
    species = Species(**species_data)
    session.add(species)
    session.flush()  # get the id before inserting children
    for sched in entry.schedules:
        session.add(CareSchedule(species_id=species.id, **sched.model_dump()))
    for trait in entry.traits:
        session.add(SpeciesTrait(species_id=species.id, **trait.model_dump()))
    return species


@router.get("/", response_model=list[Species])
def list_species(session: Session = Depends(get_session)):
    return session.exec(select(Species)).all()


@router.post("/", response_model=SpeciesDetail, status_code=201)
def create_species(payload: SpeciesCreate, session: Session = Depends(get_session)):
    """Add a single species with care schedules and traits.

    Returns 409 if the scientific name already exists — use
    POST /species/bulk to skip duplicates silently."""
    existing = session.exec(
        select(Species).where(Species.scientific_name == payload.scientific_name)
    ).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Species '{payload.scientific_name}' already exists (id={existing.id}). "
                   "Use POST /species/bulk to import with duplicate-skipping.",
        )
    species = _create_one(payload, session)
    session.commit()
    return _load_with_relations(species.id, session)


@router.post("/bulk", status_code=201)
def bulk_import_species(payload: list[SpeciesCreate], session: Session = Depends(get_session)):
    """Import multiple species from a JSON array.

    Skips entries whose scientific_name already exists — safe to re-run with
    the same data. This endpoint accepts the same structure as
    species_catalog.json, so you can POST the file contents directly."""
    added, skipped = [], []
    for entry in payload:
        if session.exec(
            select(Species).where(Species.scientific_name == entry.scientific_name)
        ).first():
            skipped.append(entry.scientific_name)
            continue
        s = _create_one(entry, session)
        added.append(s)
    session.commit()
    return {
        "added": len(added),
        "skipped": len(skipped),
        "added_ids": [s.id for s in added],
        "skipped_names": skipped,
    }


@router.post("/generate")
def generate_species(
    payload: SpeciesGenerateRequest,
    session: Session = Depends(get_session),
):
    """Use the configured LLM backend to generate a species profile draft.

    Returns a SpeciesCreate-compatible dict for review. Nothing is saved —
    POST the returned `draft` to POST /species/ after verifying the data.

    Requires ADVISOR_BACKEND=anthropic. The stub backend returns
    a placeholder template for manual filling."""
    from app.services.catalog import generate_species_profile
    try:
        draft = generate_species_profile(payload.name)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {
        "draft": draft,
        "instructions": (
            "Review the draft, then POST it to /species/ to save. "
            "Or edit species_catalog.json and restart the server to seed it automatically."
        ),
    }


@router.post("/identify-photo")
async def identify_species_photo(
    photo: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    """Identify which catalog species a photo most likely shows.

    Returns candidate species (most likely first) matched against the curated
    catalog, plus the model's observation text. Backend is selected by
    VISION_BACKEND (stub only — no hosted backend), same as photo diagnosis. The stub backend
    returns no candidates and a note explaining how to enable identification."""
    from app.services.vision import identify_species

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

    catalog = session.exec(select(Species)).all()
    try:
        result = await identify_species(image_bytes, catalog)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e

    by_id = {s.id: s for s in catalog}
    candidates = [
        {
            "id": sid,
            "common_name": by_id[sid].common_name,
            "scientific_name": by_id[sid].scientific_name,
        }
        for sid in result["candidate_ids"]
        if sid in by_id
    ]
    return {
        "backend": result["backend"],
        "observation": result["observation"],
        "candidates": candidates,
    }


@router.get("/{species_id}", response_model=SpeciesDetail)
def get_species(species_id: int, session: Session = Depends(get_session)):
    species = _load_with_relations(species_id, session)
    if not species:
        raise HTTPException(status_code=404, detail="Species not found")
    return species
