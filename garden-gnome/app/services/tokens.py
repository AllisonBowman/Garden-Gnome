"""Token service: access JWTs and rotating refresh tokens.

Access tokens are short-lived HS256 JWTs. Refresh tokens are opaque 256-bit
secrets; only their sha256 hash is stored. Rotation keeps a chain of tokens in
one family_id — presenting an already-revoked token is treated as theft
(reuse detection) and revokes the entire family, forcing a fresh sign-in.

All failures raise typed exceptions (below); the auth router (Phase 5) maps
them to 401 responses. This module never touches HTTP.
"""
from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import jwt
from sqlmodel import Session, select

from app.config import get_settings
from app.models.models import RefreshToken

ISSUER = "garden-gnome"
# Tolerated clock skew when validating exp/iat (plan cap: <= 60 s)
LEEWAY_SECONDS = 30


# --- Typed errors ------------------------------------------------------------

class AuthTokenError(Exception):
    """Base class for all token failures (maps to 401 in the API layer)."""


class InvalidAccessToken(AuthTokenError):
    """Signature/claims invalid, wrong issuer, or malformed."""


class ExpiredAccessToken(AuthTokenError):
    """Access JWT past exp (beyond leeway)."""


class InvalidRefreshToken(AuthTokenError):
    """Presented refresh token is unknown."""


class ExpiredRefreshToken(AuthTokenError):
    """Presented refresh token is past its expiry."""


class ReusedRefreshToken(AuthTokenError):
    """Presented refresh token was already rotated — its whole family has
    now been revoked."""


# --- Access tokens (JWT) -----------------------------------------------------

def issue_access_token(user_id: str, ttl_min: Optional[int] = None) -> str:
    s = get_settings()
    now = datetime.utcnow()
    minutes = s.access_token_ttl_min if ttl_min is None else ttl_min
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + timedelta(minutes=minutes),
        "iss": ISSUER,
    }
    return jwt.encode(payload, s.jwt_secret, algorithm=s.jwt_alg)


def verify_access_token(token: str) -> str:
    """Return the user id (sub) of a valid access token, else raise."""
    s = get_settings()
    try:
        payload = jwt.decode(
            token,
            s.jwt_secret,
            algorithms=[s.jwt_alg],
            issuer=ISSUER,
            leeway=LEEWAY_SECONDS,
            options={"require": ["sub", "iat", "exp", "iss"]},
        )
    except jwt.ExpiredSignatureError as e:
        raise ExpiredAccessToken(str(e)) from e
    except jwt.InvalidTokenError as e:  # signature, issuer, missing claims...
        raise InvalidAccessToken(str(e)) from e
    return payload["sub"]


# --- Refresh tokens (opaque, rotating) ---------------------------------------

def _hash(plaintext: str) -> str:
    return hashlib.sha256(plaintext.encode("ascii")).hexdigest()


def issue_refresh_token(
    session: Session,
    user_id: str,
    family_id: Optional[str] = None,
) -> tuple[str, RefreshToken]:
    """Create and persist a refresh token; return (plaintext, row).

    The plaintext is shown to the client exactly once and never stored.
    family_id is inherited when rotating; omitted for a fresh sign-in."""
    s = get_settings()
    plaintext = secrets.token_urlsafe(32)  # 256 bits of entropy
    row = RefreshToken(
        user_id=user_id,
        token_hash=_hash(plaintext),
        expires_at=datetime.utcnow() + timedelta(days=s.refresh_token_ttl_days),
        **({"family_id": family_id} if family_id else {}),
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return plaintext, row


@dataclass
class RotationResult:
    user_id: str
    access_token: str
    refresh_token: str  # new plaintext


def rotate_refresh_token(session: Session, plaintext: str) -> RotationResult:
    """Exchange a refresh token for a fresh access JWT + rotated refresh token.

    Reuse detection: a token that was already rotated (revoked_at set) being
    presented again means it leaked — revoke its entire family."""
    row = session.exec(
        select(RefreshToken).where(RefreshToken.token_hash == _hash(plaintext))
    ).first()

    if row is None:
        raise InvalidRefreshToken("unknown refresh token")

    if row.revoked_at is not None:
        _revoke_family(session, row.family_id)
        raise ReusedRefreshToken(
            "refresh token reuse detected; family revoked")

    if row.expires_at <= datetime.utcnow():
        raise ExpiredRefreshToken("refresh token expired")

    row.revoked_at = datetime.utcnow()
    session.add(row)
    new_plaintext, _new_row = issue_refresh_token(
        session, row.user_id, family_id=row.family_id
    )
    return RotationResult(
        user_id=row.user_id,
        access_token=issue_access_token(row.user_id),
        refresh_token=new_plaintext,
    )


def revoke_refresh_token(session: Session, plaintext: str) -> None:
    """Revoke a single token (logout). Unknown tokens are ignored on purpose —
    logout must be idempotent."""
    row = session.exec(
        select(RefreshToken).where(RefreshToken.token_hash == _hash(plaintext))
    ).first()
    if row is not None and row.revoked_at is None:
        row.revoked_at = datetime.utcnow()
        session.add(row)
        session.commit()


def revoke_all_for_user(session: Session, user_id: str) -> int:
    """Revoke every active refresh token for a user (account deletion,
    password-equivalent events). Returns the number revoked."""
    rows = session.exec(
        select(RefreshToken)
        .where(RefreshToken.user_id == user_id)
        .where(RefreshToken.revoked_at == None)  # noqa: E711
    ).all()
    now = datetime.utcnow()
    for row in rows:
        row.revoked_at = now
        session.add(row)
    session.commit()
    return len(rows)


def _revoke_family(session: Session, family_id: str) -> None:
    rows = session.exec(
        select(RefreshToken)
        .where(RefreshToken.family_id == family_id)
        .where(RefreshToken.revoked_at == None)  # noqa: E711
    ).all()
    now = datetime.utcnow()
    for row in rows:
        row.revoked_at = now
        session.add(row)
    session.commit()
