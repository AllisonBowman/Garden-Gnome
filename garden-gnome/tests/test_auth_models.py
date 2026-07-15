"""Phase 2 acceptance: model unit tests for User / AuthIdentity / RefreshToken.

Runs against a real migrated SQLite database (see conftest), so constraint
behavior is what production SQLite enforces, not create_all approximations.
"""
from datetime import datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.models.models import (
    AuthIdentity, AuthProvider, Plant, RefreshToken, Species, User,
)


def _mk_user(session, email="alice@example.com") -> User:
    user = User(email=email, display_name="Alice")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def test_user_defaults(session):
    user = _mk_user(session)
    assert user.id  # uuid string pk assigned client-side
    assert user.created_at is not None
    assert user.deleted_at is None
    assert user.last_login_at is None


def test_identity_links_to_user(session):
    user = _mk_user(session, email="bob@example.com")
    ident = AuthIdentity(
        user_id=user.id,
        provider=AuthProvider.google,
        provider_sub="google-sub-123",
        email_at_signup="bob@example.com",
    )
    session.add(ident)
    session.commit()

    loaded = session.exec(
        select(AuthIdentity).where(AuthIdentity.provider_sub == "google-sub-123")
    ).one()
    assert loaded.user.id == user.id
    assert loaded.provider is AuthProvider.google


def test_provider_sub_unique_per_provider(session):
    user = _mk_user(session, email="carol@example.com")
    session.add(AuthIdentity(
        user_id=user.id, provider=AuthProvider.apple, provider_sub="dup-sub"))
    session.commit()

    # Same (provider, sub) again — must violate unique(provider, provider_sub)
    session.add(AuthIdentity(
        user_id=user.id, provider=AuthProvider.apple, provider_sub="dup-sub"))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()

    # Same sub under the OTHER provider is fine (composite constraint)
    session.add(AuthIdentity(
        user_id=user.id, provider=AuthProvider.google, provider_sub="dup-sub"))
    session.commit()


def test_refresh_token_hash_unique(session):
    user = _mk_user(session, email="dave@example.com")
    expires = datetime.utcnow() + timedelta(days=90)
    session.add(RefreshToken(user_id=user.id, token_hash="h1", expires_at=expires))
    session.commit()

    session.add(RefreshToken(user_id=user.id, token_hash="h1", expires_at=expires))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_refresh_token_family_defaults(session):
    user = _mk_user(session, email="erin@example.com")
    expires = datetime.utcnow() + timedelta(days=90)
    t1 = RefreshToken(user_id=user.id, token_hash="h2", expires_at=expires)
    t2 = RefreshToken(user_id=user.id, token_hash="h3", expires_at=expires)
    session.add(t1)
    session.add(t2)
    session.commit()
    assert t1.family_id and t2.family_id
    assert t1.family_id != t2.family_id  # independent grants → new families
    assert t1.revoked_at is None


def test_plant_owned_by_user(session):
    user = _mk_user(session, email="fern@example.com")
    species = Species(
        common_name="Test Fern", scientific_name="Testus fernus",
        light_need="medium", humidity_pct_min=40, humidity_pct_max=60,
        temp_f_min=60, temp_f_max=80, soil_type="test mix",
    )
    session.add(species)
    session.commit()

    plant = Plant(nickname="Planty", species_id=species.id, user_id=user.id)
    session.add(plant)
    session.commit()
    session.refresh(plant)

    assert plant.user.email == "fern@example.com"
    assert [p.nickname for p in user.plants] == ["Planty"]


def test_orm_cascade_deletes_children(session):
    user = _mk_user(session, email="gone@example.com")
    session.add(AuthIdentity(
        user_id=user.id, provider=AuthProvider.apple, provider_sub="gone-sub"))
    session.add(RefreshToken(
        user_id=user.id, token_hash="gone-hash",
        expires_at=datetime.utcnow() + timedelta(days=1)))
    session.commit()

    session.delete(user)
    session.commit()

    assert session.exec(select(AuthIdentity).where(
        AuthIdentity.provider_sub == "gone-sub")).first() is None
    assert session.exec(select(RefreshToken).where(
        RefreshToken.token_hash == "gone-hash")).first() is None
