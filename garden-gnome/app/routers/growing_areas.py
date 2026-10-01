"""Growing areas — the places a person has to grow in.

Routes are declared once on a prefix-less router and mounted twice: at
`/growing-areas`, and at the old `/environments` for one release. A TestFlight
build in someone's hand still calls the old path, and a rename is not a reason
to break an app that is already installed. Delete `legacy_router` (and its
mount in main.py) once the next build is the floor.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db.database import get_session
from app.deps import get_current_user
from app.models.models import GrowingArea, Plant, Species, StewardshipRecord, User
from app.models.schemas import (
    GrowingAreaCreate, GrowingAreaPatch, GrowingAreaRead,
    FitFindingRead, CandidateRead, PlantMisfitRead,
)
from app.services import fit
from app.services.weather import fetch_weather

_routes = APIRouter()


def _with_count(area: GrowingArea, session: Session) -> GrowingAreaRead:
    count = len(session.exec(
        select(Plant).where(Plant.growing_area_id == area.id)).all())
    return GrowingAreaRead(**area.model_dump(), plant_count=count)


def _owned(area_id: int, user: User, session: Session) -> GrowingArea:
    """404 (not 403) for other users' growing areas — no id probing."""
    area = session.get(GrowingArea, area_id)
    if area is None or area.user_id != user.id:
        raise HTTPException(status_code=404, detail="Growing area not found")
    return area


@_routes.post("/", response_model=GrowingAreaRead, status_code=201)
def create_growing_area(
    payload: GrowingAreaCreate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    area = GrowingArea(**payload.model_dump(), user_id=user.id)
    session.add(area)
    session.commit()
    session.refresh(area)
    return _with_count(area, session)


@_routes.get("/", response_model=list[GrowingAreaRead])
def list_growing_areas(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    areas = session.exec(
        select(GrowingArea).where(GrowingArea.user_id == user.id)
    ).all()
    return [_with_count(a, session) for a in areas]


@_routes.get("/{area_id}", response_model=GrowingAreaRead)
def get_growing_area(
    area_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return _with_count(_owned(area_id, user, session), session)


@_routes.get("/{area_id}/weather")
async def get_growing_area_weather(
    area_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Current + forecast Apple Weather for this growing area's coordinates.

    Weather is an enhancement: when the area has no location, or no weather
    backend is configured, this returns `available: false` with a friendly
    reason rather than an error, so the app degrades gracefully."""
    area = _owned(area_id, user, session)
    if area.lat is None or area.lng is None:
        return {
            "available": False,
            "detail": "Add this growing area's location to see local weather.",
            "weather": None,
        }
    weather = await fetch_weather(area.lat, area.lng)
    if weather is None:
        return {
            "available": False,
            "detail": "Weather isn't available right now.",
            "weather": None,
        }
    return {"available": True, "detail": "ok", "weather": weather}


@_routes.patch("/{area_id}", response_model=GrowingAreaRead)
def patch_growing_area(
    area_id: int,
    payload: GrowingAreaPatch,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    area = _owned(area_id, user, session)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(area, field, value)
    session.add(area)
    session.commit()
    session.refresh(area)
    return _with_count(area, session)


@_routes.delete("/{area_id}", status_code=204)
def delete_growing_area(
    area_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    area = _owned(area_id, user, session)
    plants = session.exec(
        select(Plant).where(Plant.growing_area_id == area.id)
    ).all()
    if plants:
        raise HTTPException(
            status_code=409,
            detail="Growing area still contains plants — move or delete them first.",
        )
    # Data-integrity guard beyond the plan: stewardship history references
    # growing areas; deleting one would orphan the chain-of-custody records.
    history = session.exec(
        select(StewardshipRecord)
        .where(StewardshipRecord.growing_area_id == area.id)
    ).first()
    if history is not None:
        raise HTTPException(
            status_code=409,
            detail="Growing area has stewardship history and can't be deleted.",
        )
    session.delete(area)
    session.commit()


def _as_findings(findings) -> list[FitFindingRead]:
    return [FitFindingRead(axis=f.axis.value, verdict=f.verdict.value,
                           sentence=f.sentence, borrowed=f.borrowed)
            for f in findings]


@_routes.get("/{area_id}/candidates", response_model=list[CandidateRead])
def growing_area_candidates(
    area_id: int,
    limit: int = 20,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Species that suit this space, best-evidenced first.

    A candidate has zero contradictions against the area AND at least one
    axis the catalog actually confirmed. The second half is what stops an
    unresearched row -- nothing against it because nothing is known about it
    -- from being put forward as a recommendation (`fit.candidates`).

    So a short list here means the catalog is thin on the axes this space
    turns on, not that nothing will grow in it."""
    area = _owned(area_id, user, session)
    all_species = session.exec(select(Species)).all()
    ranked = fit.candidates(all_species, area)
    return [
        CandidateRead(
            species_id=c.species.id,
            common_name=c.species.common_name,
            scientific_name=c.species.scientific_name,
            score=c.score,
            fits=_as_findings(fit.confirmed(c.findings)),
        )
        for c in ranked[:limit]
    ]


@_routes.get("/{area_id}/misfits", response_model=list[PlantMisfitRead])
def growing_area_misfits(
    area_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """For the plants already standing here, what specifically doesn't suit.

    Only plants with at least one contradiction appear. A plant the catalog
    cannot judge is absent rather than listed as fine -- this endpoint says
    what needs addressing, and "we don't know" is not something to address."""
    area = _owned(area_id, user, session)
    plants = session.exec(
        select(Plant)
        .where(Plant.growing_area_id == area.id)
        .where(Plant.user_id == user.id)
    ).all()

    out = []
    for plant in plants:
        species = session.get(Species, plant.species_id)
        if species is None:
            continue
        problems = fit.misfits(fit.assess(species, area))
        if not problems:
            continue
        out.append(PlantMisfitRead(
            plant_id=plant.id,
            nickname=plant.nickname,
            species_id=species.id,
            common_name=species.common_name,
            misfits=_as_findings(problems),
        ))
    # Worst first: the plant with the most wrong with it is the one to look at.
    out.sort(key=lambda m: (-len(m.misfits), m.nickname or ""))
    return out


router = APIRouter(prefix="/growing-areas", tags=["growing areas"])
router.include_router(_routes)

# The pre-rename path. Same handlers, marked deprecated in the OpenAPI schema
# so the next person reading it knows which one to build against.
legacy_router = APIRouter(prefix="/environments", tags=["growing areas"])
legacy_router.include_router(_routes, deprecated=True)
