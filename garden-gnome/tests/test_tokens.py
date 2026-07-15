"""Phase 3 acceptance: token service unit tests.

Covers the plan's required cases: happy path, expiry, tamper, and the
reuse-detection family-revocation case — plus logout and revoke-all.
"""
from datetime import datetime, timedelta

import jwt as pyjwt
import pytest
from sqlmodel import select

from app.models.models import RefreshToken, User
from app.services import tokens
from app.services.tokens import (
    ExpiredAccessToken, ExpiredRefreshToken, InvalidAccessToken,
    InvalidRefreshToken, ReusedRefreshToken,
)


@pytest.fixture()
def user(session) -> User:
    u = User(email="tokens@example.com")
    session.add(u)
    session.commit()
    session.refresh(u)
    return u


# --- Access JWTs -------------------------------------------------------------

def test_access_token_round_trip(user):
    token = tokens.issue_access_token(user.id)
    assert tokens.verify_access_token(token) == user.id


def test_access_token_expired(user):
    # -2 minutes puts exp well beyond the 30 s leeway
    token = tokens.issue_access_token(user.id, ttl_min=-2)
    with pytest.raises(ExpiredAccessToken):
        tokens.verify_access_token(token)


def test_access_token_tampered(user):
    token = tokens.issue_access_token(user.id)
    header, payload, sig = token.split(".")
    forged = f"{header}.{payload}.{'A' * len(sig)}"
    with pytest.raises(InvalidAccessToken):
        tokens.verify_access_token(forged)


def test_access_token_wrong_secret(user):
    forged = pyjwt.encode(
        {"sub": user.id, "iat": datetime.utcnow(),
         "exp": datetime.utcnow() + timedelta(minutes=5), "iss": tokens.ISSUER},
        "not-the-real-secret", algorithm="HS256",
    )
    with pytest.raises(InvalidAccessToken):
        tokens.verify_access_token(forged)


def test_access_token_wrong_issuer(user):
    from app.config import get_settings
    forged = pyjwt.encode(
        {"sub": user.id, "iat": datetime.utcnow(),
         "exp": datetime.utcnow() + timedelta(minutes=5), "iss": "impostor"},
        get_settings().jwt_secret, algorithm="HS256",
    )
    with pytest.raises(InvalidAccessToken):
        tokens.verify_access_token(forged)


# --- Refresh tokens ----------------------------------------------------------

def test_refresh_rotation_happy_path(session, user):
    plaintext, row = tokens.issue_refresh_token(session, user.id)
    assert row.token_hash != plaintext  # only the hash is stored

    result = tokens.rotate_refresh_token(session, plaintext)
    assert result.user_id == user.id
    assert tokens.verify_access_token(result.access_token) == user.id
    assert result.refresh_token != plaintext

    # Old row revoked; new row active in the SAME family
    session.expire_all()
    old = session.exec(select(RefreshToken).where(
        RefreshToken.token_hash == tokens._hash(plaintext))).one()
    new = session.exec(select(RefreshToken).where(
        RefreshToken.token_hash == tokens._hash(result.refresh_token))).one()
    assert old.revoked_at is not None
    assert new.revoked_at is None
    assert new.family_id == old.family_id


def test_refresh_reuse_revokes_family(session, user):
    plaintext, _ = tokens.issue_refresh_token(session, user.id)
    first = tokens.rotate_refresh_token(session, plaintext)
    second = tokens.rotate_refresh_token(session, first.refresh_token)

    # Replaying the FIRST token (already rotated) = reuse -> kill the family
    with pytest.raises(ReusedRefreshToken):
        tokens.rotate_refresh_token(session, plaintext)

    session.expire_all()
    newest = session.exec(select(RefreshToken).where(
        RefreshToken.token_hash == tokens._hash(second.refresh_token))).one()
    assert newest.revoked_at is not None  # innocent-looking newest token too

    with pytest.raises(ReusedRefreshToken):
        tokens.rotate_refresh_token(session, second.refresh_token)


def test_refresh_unknown_token(session):
    with pytest.raises(InvalidRefreshToken):
        tokens.rotate_refresh_token(session, "never-issued")


def test_refresh_expired(session, user):
    plaintext, row = tokens.issue_refresh_token(session, user.id)
    row.expires_at = datetime.utcnow() - timedelta(seconds=1)
    session.add(row)
    session.commit()
    with pytest.raises(ExpiredRefreshToken):
        tokens.rotate_refresh_token(session, plaintext)


def test_logout_revokes_single_token_idempotently(session, user):
    plaintext, _ = tokens.issue_refresh_token(session, user.id)
    tokens.revoke_refresh_token(session, plaintext)
    tokens.revoke_refresh_token(session, plaintext)  # second call: no error
    tokens.revoke_refresh_token(session, "never-issued")  # unknown: no error

    with pytest.raises(ReusedRefreshToken):
        # revoked-but-presented goes down the reuse path by design
        tokens.rotate_refresh_token(session, plaintext)


def test_revoke_all_for_user(session, user):
    p1, _ = tokens.issue_refresh_token(session, user.id)
    p2, _ = tokens.issue_refresh_token(session, user.id)
    count = tokens.revoke_all_for_user(session, user.id)
    assert count == 2
    for p in (p1, p2):
        with pytest.raises(ReusedRefreshToken):
            tokens.rotate_refresh_token(session, p)
