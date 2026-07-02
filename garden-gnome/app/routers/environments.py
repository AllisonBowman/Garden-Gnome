from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db.database import get_session
from app.models.models import Environment, Plant
from app.models.schemas import EnvironmentCreate, EnvironmentRead

router = APIRouter(prefix="/environments", tags=["environments"])


def _with_count(env: Environment, session: Session) -> EnvironmentRead:
    count = len(session.exec(select(Plant).where(Plant.environment_id == env.id)).all())
    return EnvironmentRead(**env.model_dump(), plant_count=count)


@router.post("/", response_model=EnvironmentRead, status_code=201)
def create_environment(payload: EnvironmentCreate, session: Session = Depends(get_session)):
    env = Environment(**payload.model_dump())
    session.add(env)
    session.commit()
    session.refresh(env)
    return _with_count(env, session)


@router.get("/", response_model=list[EnvironmentRead])
def list_environments(session: Session = Depends(get_session)):
    envs = session.exec(select(Environment)).all()
    return [_with_count(e, session) for e in envs]


@router.get("/{env_id}", response_model=EnvironmentRead)
def get_environment(env_id: int, session: Session = Depends(get_session)):
    env = session.get(Environment, env_id)
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")
    return _with_count(env, session)
