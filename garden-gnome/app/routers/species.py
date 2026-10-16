import gzip
import json
import threading
from dataclasses import dataclass

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import Response
from pydantic import TypeAdapter
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.db.catalog_state import catalog_key
from app.db.database import get_session
from app.deps import get_current_user
from app.models.models import CareSchedule, Species, SpeciesTrait
from app.models.schemas import (
    SpeciesCreate, SpeciesDetail, SpeciesGenerateRequest, SpeciesRead,
)

# Every species route requires a signed-in caller. Reads are only ever hit by
# the app post-login (it sends a bearer token), and the catalog is populated by
# direct DB writes (seed.py / the offline expansion pipeline), not HTTP — so the
# write routes have no anonymous caller to serve. Router-level dependency keeps
# this uniform: a new endpoint can't accidentally ship unauthenticated.
router = APIRouter(
    prefix="/species",
    tags=["species"],
    dependencies=[Depends(get_current_user)],
)

ALLOWED_PHOTO_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_PHOTO_BYTES = 8 * 1024 * 1024  # 8MB


def _load_with_relations(species_id: int, session: Session) -> Species:
    return session.exec(
        select(Species)
        .where(Species.id == species_id)
        .options(selectinload(Species.care_schedules), selectinload(Species.traits))
    ).first()


def _detail(species: Species) -> SpeciesDetail:
    """A never-recomputed row holds null where the schema promises a list."""
    return SpeciesDetail.model_validate(
        species, update={"care_sources": species.care_sources or []})


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


_CATALOG_ADAPTER = TypeAdapter(list[SpeciesRead])


@dataclass(frozen=True)
class _CatalogBody:
    key: tuple
    identity: bytes
    gzipped: bytes


# One built body per process, for the catalog version it was built from.
_catalog: _CatalogBody | None = None
_catalog_lock = threading.Lock()
# Bumped by every write route here, so this process never serves a body from
# before its own write even if the row count and ids could not show it.
_catalog_writes = 0


def _catalog_changed() -> None:
    global _catalog_writes
    with _catalog_lock:
        _catalog_writes += 1


def _build_catalog(session: Session) -> bytes:
    """The list exactly as the response model would serialize it.

    humidity_sourced is computed with one trait query rather than via the
    model property -- the property walks `species.traits`, which would
    lazy-load per row across the whole catalog. The bytes are what FastAPI's
    JSONResponse would render for the same content."""
    derived_ids = set(session.exec(
        select(SpeciesTrait.species_id)
        .where(SpeciesTrait.trait == "humidity_source")
    ).all())
    rows = [
        SpeciesRead.model_validate(
            sp, update={"humidity_sourced": sp.id not in derived_ids})
        for sp in session.exec(select(Species)).all()
    ]
    content = _CATALOG_ADAPTER.dump_python(rows, mode="json", exclude_none=True)
    return json.dumps(content, ensure_ascii=False, allow_nan=False,
                      indent=None, separators=(",", ":")).encode("utf-8")


def _catalog_body(session: Session) -> _CatalogBody:
    """The current catalog's body, built at most once per version.

    The lock makes ten phones opening the app at once after a cold start
    cost one build, not ten: the first builds, the rest wait and reuse it."""
    global _catalog
    # The database's URL too: production has one, but a process that talks
    # to two (the test suite) must never serve one's catalog for the other.
    key = (str(session.get_bind().url), *catalog_key(session), _catalog_writes)
    cached = _catalog
    if cached is not None and cached.key == key:
        return cached
    with _catalog_lock:
        cached = _catalog
        if cached is not None and cached.key == key:
            return cached
        identity = _build_catalog(session)
        cached = _CatalogBody(
            key=key, identity=identity,
            gzipped=gzip.compress(identity, compresslevel=9, mtime=0))
        _catalog = cached
        return cached


@router.get("/", response_model=list[SpeciesRead],
            response_model_exclude_none=True)
def list_species(request: Request, session: Session = Depends(get_session)):
    """The catalog as clients should see it.

    Deliberately SpeciesRead, not the table model: the raw model leaks the
    internal review trail (review_status, review_note, source, source_ref),
    which is operator state and no business of a client. SpeciesRead also
    carries the derived toxicity_description, so a list view can show the
    nuanced sentence rather than a flat 'toxic' flag.

    Absent values are absent keys: most rows carry a handful of the resolved
    columns and a claims-minted row carries no legacy ones, so nulls would
    be most of the payload. The mobile type declares every one optional.

    Built once per catalog version and served as cached bytes (gzip when the
    client takes it, which the phone does). Validating every row on every
    request took a 256 MB machine past 220 MB at ten requests at once; the
    catalog only changes at boot or through the write routes below, and
    catalog_key notices both."""
    body = _catalog_body(session)
    # The same test GZipMiddleware uses, so the two never disagree; a body
    # that already carries Content-Encoding passes the middleware untouched.
    if "gzip" in request.headers.get("accept-encoding", ""):
        return Response(
            body.gzipped, media_type="application/json",
            headers={"Content-Encoding": "gzip", "Vary": "Accept-Encoding"})
    return Response(body.identity, media_type="application/json")


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
    _catalog_changed()
    return _detail(_load_with_relations(species.id, session))


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
    _catalog_changed()
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
    return _detail(species)
