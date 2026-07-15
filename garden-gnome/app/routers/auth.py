"""Auth API (Phase 5): social sign-in, token refresh, logout, profile.

Sign-in upsert (shared by both providers):
1. Known (provider, sub) identity -> that user; update last_login_at.
2. Verified email exactly matching an existing user -> link a new identity
   to that user. (Apple private-relay emails won't match by construction.)
3. Otherwise create the User, the identity, AND a default "My Home"
   environment so every new account starts usable (decision 5).
"""
from datetime import datetime
from typing import Optional

from cryptography.fernet import Fernet
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlmodel import Session, select

from app.config import get_settings
from app.db.database import get_session
from app.deps import get_current_user
from app.models.models import (
    AuthIdentity, AuthProvider, Environment, EnvironmentType, User,
)
from app.models.schemas import (
    AppleSignInRequest, AuthTokensOut, GoogleSignInRequest, LogoutRequest,
    RefreshRequest, UserOut, UserPatch,
)
from app.services import tokens
from app.services.oauth import (
    ProviderConfigError, ProviderTokenError, exchange_apple_code,
    verify_apple_token, verify_google_token,
)

router = APIRouter(tags=["auth"])

DEFAULT_ENV_NAME = "My Home"


def _sign_in(
    session: Session,
    provider: AuthProvider,
    sub: str,
    email: Optional[str],
    email_verified: bool,
    display_name_hint: Optional[str] = None,
) -> tuple[User, AuthIdentity]:
    now = datetime.utcnow()

    identity = session.exec(
        select(AuthIdentity)
        .where(AuthIdentity.provider == provider)
        .where(AuthIdentity.provider_sub == sub)
    ).first()

    if identity is not None:
        user = session.get(User, identity.user_id)
        if user is None or user.deleted_at is not None:
            # Identity orphaned by a deletion — treat as a fresh account
            session.delete(identity)
            session.commit()
            identity = None
        else:
            user.last_login_at = now
            if display_name_hint and not user.display_name:
                user.display_name = display_name_hint
            session.add(user)
            session.commit()
            session.refresh(user)
            return user, identity

    user = None
    if email and email_verified:
        user = session.exec(
            select(User)
            .where(User.email == email)
            .where(User.deleted_at == None)  # noqa: E711
        ).first()

    created = False
    if user is None:
        user = User(email=email, display_name=display_name_hint)
        session.add(user)
        session.flush()
        # Every new account starts with a usable default environment
        session.add(Environment(
            name=DEFAULT_ENV_NAME,
            type=EnvironmentType.home,
            user_id=user.id,
        ))
        created = True
    elif display_name_hint and not user.display_name:
        user.display_name = display_name_hint

    user.last_login_at = now
    identity = AuthIdentity(
        user_id=user.id,
        provider=provider,
        provider_sub=sub,
        email_at_signup=email,
    )
    session.add(user)
    session.add(identity)
    session.commit()
    session.refresh(user)
    session.refresh(identity)
    if created:
        pass  # env committed alongside the user
    return user, identity


def _token_response(session: Session, user: User) -> AuthTokensOut:
    refresh_plain, _ = tokens.issue_refresh_token(session, user.id)
    return AuthTokensOut(
        access_token=tokens.issue_access_token(user.id),
        refresh_token=refresh_plain,
        user=UserOut(**user.model_dump()),
    )


@router.post("/auth/apple", response_model=AuthTokensOut)
def sign_in_with_apple(
    payload: AppleSignInRequest,
    session: Session = Depends(get_session),
):
    try:
        claims = verify_apple_token(payload.identity_token, payload.raw_nonce)
    except ProviderTokenError:
        raise HTTPException(status_code=401, detail="Sign in with Apple failed")
    except ProviderConfigError:
        raise HTTPException(
            status_code=503,
            detail="Sign in with Apple isn't configured on this PlantAdvocate server")

    user, identity = _sign_in(
        session,
        AuthProvider.apple,
        claims.sub,
        claims.email,
        claims.email_verified,
        display_name_hint=payload.full_name,
    )

    # Exchange the one-time code for Apple's refresh token — needed only so
    # account deletion can revoke the Apple session (5.1.1(v)). Failure is
    # non-fatal by design.
    apple_refresh = exchange_apple_code(payload.authorization_code)
    if apple_refresh:
        fernet = Fernet(get_settings().fernet_key.encode())
        identity.apple_refresh_token_enc = fernet.encrypt(
            apple_refresh.encode()).decode()
        session.add(identity)
        session.commit()

    return _token_response(session, user)


@router.post("/auth/google", response_model=AuthTokensOut)
def sign_in_with_google(
    payload: GoogleSignInRequest,
    session: Session = Depends(get_session),
):
    try:
        claims = verify_google_token(payload.id_token)
    except ProviderTokenError:
        raise HTTPException(status_code=401, detail="Google sign-in failed")
    except ProviderConfigError:
        raise HTTPException(
            status_code=503,
            detail="Google sign-in isn't configured on this PlantAdvocate server")

    user, _ = _sign_in(
        session,
        AuthProvider.google,
        claims.sub,
        claims.email,
        email_verified=True,  # verifier enforces email_verified
        display_name_hint=claims.name,
    )
    return _token_response(session, user)


@router.post("/auth/refresh")
def refresh(payload: RefreshRequest, session: Session = Depends(get_session)):
    try:
        result = tokens.rotate_refresh_token(session, payload.refresh_token)
    except tokens.AuthTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    return {
        "access_token": result.access_token,
        "refresh_token": result.refresh_token,
        "token_type": "bearer",
    }


@router.post("/auth/logout", status_code=204)
def logout(payload: LogoutRequest, session: Session = Depends(get_session)):
    tokens.revoke_refresh_token(session, payload.refresh_token)
    return Response(status_code=204)


@router.get("/me", response_model=UserOut)
def get_me(user: User = Depends(get_current_user)):
    return UserOut(**user.model_dump())


@router.patch("/me", response_model=UserOut)
def patch_me(
    payload: UserPatch,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if payload.display_name is not None:
        user.display_name = payload.display_name
    session.add(user)
    session.commit()
    session.refresh(user)
    return UserOut(**user.model_dump())
