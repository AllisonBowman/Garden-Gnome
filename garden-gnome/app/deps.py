"""Shared FastAPI dependencies."""
from typing import Optional

from fastapi import Depends, Header, HTTPException
from sqlmodel import Session

from app.db.database import get_session
from app.models.models import User
from app.services.tokens import AuthTokenError, verify_access_token


def get_current_user(
    authorization: Optional[str] = Header(default=None),
    session: Session = Depends(get_session),
) -> User:
    """Resolve the Bearer access token to an active (non-deleted) User.

    Raises 401 in every failure mode — invalid, expired, unknown user,
    deleted account — without distinguishing them to the caller."""
    unauthorized = HTTPException(
        status_code=401,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not authorization or not authorization.lower().startswith("bearer "):
        raise unauthorized
    token = authorization.split(" ", 1)[1].strip()
    try:
        user_id = verify_access_token(token)
    except AuthTokenError:
        raise unauthorized from None
    user = session.get(User, user_id)
    if user is None or user.deleted_at is not None:
        raise unauthorized
    return user
