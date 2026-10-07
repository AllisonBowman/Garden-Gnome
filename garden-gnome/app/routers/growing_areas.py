"""Growing areas — the places a person has to grow in.

Routes are declared once on a prefix-less router and mounted twice: at
`/growing-areas`, and at the old `/environments` for one release. A TestFlight
build in someone's hand still calls the old path, and a rename is not a reason
to break an app that is already installed. Delete `legacy_router` (and its
mount in main.py) once the next build is the floor.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlmodel import Session, select

from app.db.database import get_session
from app.deps import get_current_user
from app.models.models import GrowingArea, Plant, Species, StewardshipRecord, User
from app.models.schemas import (
    GrowingAreaCreate, GrowingAreaPatch, GrowingAreaRead,
    FitFindingRead, CandidateRead, PlantMisfitRead, SpeciesFitRead,
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
    # Oldest first, by id: the order a picker shows, and the first entry is
    # the area a plant saved without one lands in (`plants._resolve_growing_
    # area_id`). Without an ORDER BY the database may hand an edited row back
    # last, and "the first one" stops meaning anything.
    areas = session.exec(
        select(GrowingArea)
        .where(GrowingArea.user_id == user.id)
        .order_by(GrowingArea.id.asc())
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
                           sentence=f.sentence, borrowed=f.borrowed,
                           authorities=list(f.authorities), goal=f.goal)
            for f in findings]


#: The header that says how many candidates there were before `limit` cut
#: the list. Listed in main.py's CORS `expose_headers` so the web preview can
#: read it too.
TOTAL_HEADER = "X-Total-Count"


@_routes.get("/{area_id}/candidates", response_model=list[CandidateRead])
def growing_area_candidates(
    area_id: int,
    response: Response,
    limit: int = Query(20, ge=0),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Species that suit this space, best-evidenced first.

    A candidate has zero contradictions against the area AND at least one
    axis the catalog actually confirmed. The second half is what stops an
    unresearched row -- nothing against it because nothing is known about it
    -- from being put forward as a recommendation (`fit.candidates`).

    So a short list here means the catalog is thin on the axes this space
    turns on, not that nothing will grow in it.

    The first `limit` are returned and the whole count goes in the
    X-Total-Count header: a screen showing twelve of 263 has to be able to
    say so, or twelve reads as the answer. A header rather than a wrapper
    object, because the body is the list every installed build parses.
    `limit` is never negative: a slice by -1 would quietly drop the last
    candidate instead of failing."""
    area = _owned(area_id, user, session)
    all_species = session.exec(select(Species)).all()
    ranked = fit.candidates(all_species, area)
    response.headers[TOTAL_HEADER] = str(len(ranked))
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


@_routes.get("/{area_id}/fit/{species_id}", response_model=SpeciesFitRead)
def growing_area_species_fit(
    area_id: int,
    species_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """One species against this area, every axis: what Add Plant asks
    before the plant is saved.

    Neither endpoint above can answer it. The misfit list speaks only for
    plants already standing here, and the candidate list only for species
    that cleared the area -- so "what would this spot have against the plant
    I'm about to put in it" had no answer until after it was planted, which
    is when it is worth least. Unknowns come back as unknowns: the client
    decides what to show, never what the verdict is."""
    area = _owned(area_id, user, session)
    species = session.get(Species, species_id)
    if species is None:
        raise HTTPException(status_code=404, detail="Species not found")
    findings = fit.assess(species, area)
    return SpeciesFitRead(
        species_id=species.id,
        common_name=species.common_name,
        scientific_name=species.scientific_name,
        score=fit.score(findings),
        candidate=fit.is_candidate(findings),
        findings=_as_findings(findings),
    )


router = APIRouter(prefix="/growing-areas", tags=["growing areas"])
router.include_router(_routes)

# The pre-rename path. Same handlers, marked deprecated in the OpenAPI schema
# so the next person reading it knows which one to build against.
legacy_router = APIRouter(prefix="/environments", tags=["growing areas"])
legacy_router.include_router(_routes, deprecated=True)
