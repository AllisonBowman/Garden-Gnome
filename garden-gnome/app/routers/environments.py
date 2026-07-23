from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db.database import get_session
from app.deps import get_current_user
from app.models.models import Environment, Plant, StewardshipRecord, User
from app.models.schemas import (
    EnvironmentCreate, EnvironmentPatch, EnvironmentRead,
)
from app.services.weather import fetch_weather

router = APIRouter(prefix="/environments", tags=["environments"])


def _with_count(env: Environment, session: Session) -> EnvironmentRead:
    count = len(session.exec(select(Plant).where(Plant.environment_id == env.id)).all())
    return EnvironmentRead(**env.model_dump(), plant_count=count)


def _owned(env_id: int, user: User, session: Session) -> Environment:
    """404 (not 403) for other users' environments — no id probing."""
    env = session.get(Environment, env_id)
    if env is None or env.user_id != user.id:
        raise HTTPException(status_code=404, detail="Environment not found")
    return env


@router.post("/", response_model=EnvironmentRead, status_code=201)
def create_environment(
    payload: EnvironmentCreate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    env = Environment(**payload.model_dump(), user_id=user.id)
    session.add(env)
    session.commit()
    session.refresh(env)
    return _with_count(env, session)


@router.get("/", response_model=list[EnvironmentRead])
def list_environments(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    envs = session.exec(
        select(Environment).where(Environment.user_id == user.id)
    ).all()
    return [_with_count(e, session) for e in envs]


@router.get("/{env_id}", response_model=EnvironmentRead)
def get_environment(
    env_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return _with_count(_owned(env_id, user, session), session)


@router.get("/{env_id}/weather")
async def get_environment_weather(
    env_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Current + forecast Apple Weather for this environment's coordinates.

    Weather is an enhancement: when the environment has no location, or no
    weather backend is configured, this returns `available: false` with a
    friendly reason rather than an error, so the app degrades gracefully."""
    env = _owned(env_id, user, session)
    if env.lat is None or env.lng is None:
        return {
            "available": False,
            "detail": "Add this environment's location to see local weather.",
            "weather": None,
        }
    weather = await fetch_weather(env.lat, env.lng)
    if weather is None:
        return {
            "available": False,
            "detail": "Weather isn't available right now.",
            "weather": None,
        }
    return {"available": True, "detail": "ok", "weather": weather}


@router.patch("/{env_id}", response_model=EnvironmentRead)
def patch_environment(
    env_id: int,
    payload: EnvironmentPatch,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    env = _owned(env_id, user, session)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(env, field, value)
    session.add(env)
    session.commit()
    session.refresh(env)
    return _with_count(env, session)


@router.delete("/{env_id}", status_code=204)
def delete_environment(
    env_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    env = _owned(env_id, user, session)
    plants = session.exec(
        select(Plant).where(Plant.environment_id == env.id)
    ).all()
    if plants:
        raise HTTPException(
            status_code=409,
            detail="Environment still contains plants — move or delete them first.",
        )
    # Data-integrity guard beyond the plan: stewardship history references
    # environments; deleting one would orphan the chain-of-custody records.
    history = session.exec(
        select(StewardshipRecord)
        .where(StewardshipRecord.environment_id == env.id)
    ).first()
    if history is not None:
        raise HTTPException(
            status_code=409,
            detail="Environment has stewardship history and can't be deleted.",
        )
    session.delete(env)
    session.commit()
