"""Auth API (Phase 5): social sign-in, token refresh, logout, profile.

Sign-in upsert (shared by both providers):
1. Known (provider, sub) identity -> that user; update last_login_at.
2. Verified email exactly matching an existing user -> link a new identity
   to that user. (Apple private-relay emails won't match by construction.)
3. Otherwise create the User, the identity, AND a default "My Home"
   growing area so every new account starts usable (decision 5).
"""
import logging
import threading
from datetime import datetime, timedelta
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from fastapi import (
    APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response,
)
from sqlalchemy.engine import Engine
from sqlmodel import Session, select

from app.config import get_settings
from app.db.database import get_session
from app.db.revocations import PendingAppleRevocation
from app.deps import get_current_user
from app.rate_limit import SIGNIN_LIMIT, TOKEN_LIMIT, limiter
from app.models.models import (
    AuthIdentity, AuthProvider, GrowingArea, GrowingAreaType, Plant, User,
)
from app.models.schemas import (
    AppleSignInRequest, AuthTokensOut, GoogleSignInRequest, LogoutRequest,
    RefreshRequest, UserOut, UserPatch,
)
from app.services import tokens
from app.services.oauth import (
    ProviderConfigError, ProviderTokenError, exchange_apple_code,
    revoke_apple_token, verify_apple_token, verify_google_token,
)

logger = logging.getLogger(__name__)

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
        # Every new account starts with a usable default growing area
        session.add(GrowingArea(
            name=DEFAULT_ENV_NAME,
            type=GrowingAreaType.home,
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
@limiter.limit(SIGNIN_LIMIT)
def sign_in_with_apple(
    request: Request,
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
@limiter.limit(SIGNIN_LIMIT)
def sign_in_with_google(
    request: Request,
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
@limiter.limit(TOKEN_LIMIT)
def refresh(
    request: Request,
    payload: RefreshRequest,
    session: Session = Depends(get_session),
):
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
@limiter.limit(TOKEN_LIMIT)
def logout(
    request: Request,
    payload: LogoutRequest,
    session: Session = Depends(get_session),
):
    tokens.revoke_refresh_token(session, payload.refresh_token)
    return Response(status_code=204)


@router.get("/me", response_model=UserOut)
def get_me(user: User = Depends(get_current_user)):
    return UserOut(**user.model_dump())


#: Tries a queued Apple revoke gets on its own before it waits for an operator.
MAX_REVOKE_ATTEMPTS = 10
#: Wait after the first failure; doubles with each one after (5 min, 10, 20 ...
#: about 42 hours before the tenth), so a day-long Apple outage and a machine
#: that cold-starts every few minutes do not burn every attempt in an hour.
REVOKE_BACKOFF = timedelta(minutes=5)


def _revoke_due(row: PendingAppleRevocation, now: datetime) -> bool:
    if row.attempts >= MAX_REVOKE_ATTEMPTS:
        return False
    if row.last_attempt_at is None:
        return True
    return now - row.last_attempt_at >= REVOKE_BACKOFF * (2 ** (row.attempts - 1))


def revoke_pending_apple_grants(
    engine: Engine, ids: Optional[list[int]] = None,
) -> int:
    """Send Apple each queued revoke that is due; forget the ones it accepts.

    Runs after every account deletion (for that deletion's rows) and once at
    startup (for every row), so a revoke that failed while Apple was down is
    tried again on the next cold start, backing off as it keeps failing.
    Returns how many Apple accepted. Never raises: nothing here may break a
    deletion that has already happened, or a boot."""
    revoked = 0
    try:
        fernet = Fernet(get_settings().fernet_key.encode())
        with Session(engine) as session:
            query = select(PendingAppleRevocation)
            if ids is not None:
                query = query.where(PendingAppleRevocation.id.in_(ids))
            now = datetime.utcnow()
            for row in session.exec(query).all():
                if not _revoke_due(row, now):
                    continue
                row.attempts += 1
                row.last_attempt_at = now
                try:
                    accepted = bool(revoke_apple_token(
                        fernet.decrypt(row.token_enc.encode()).decode()))
                except InvalidToken:
                    # Encrypted under a key this server no longer has (the
                    # Fernet key was rotated). No retry can fix that; leave
                    # it for the operator.
                    row.attempts = MAX_REVOKE_ATTEMPTS
                    accepted = False
                    logger.error(
                        "Queued Apple revoke %s cannot be decrypted with this "
                        "server's encryption key; it will not be retried",
                        row.id)
                except Exception as e:  # noqa: BLE001 -- try again later
                    accepted = False
                    logger.warning(
                        "Queued Apple revoke %s failed (%s)", row.id, e)
                if accepted:
                    session.delete(row)
                    revoked += 1
                elif row.attempts >= MAX_REVOKE_ATTEMPTS:
                    session.add(row)
                    logger.error(
                        "Queued Apple revoke %s failed %s times and will not "
                        "be retried automatically; revoke it by hand or "
                        "delete the row", row.id, row.attempts)
                else:
                    session.add(row)
                    logger.warning(
                        "Queued Apple revoke %s failed (attempt %s of %s); "
                        "it will be retried", row.id, row.attempts,
                        MAX_REVOKE_ATTEMPTS)
                # One commit per row, so a crash part-way loses no outcome.
                session.commit()
    except Exception:  # noqa: BLE001 -- see docstring
        logger.exception("Retrying queued Apple revokes failed")
    return revoked


def start_queued_apple_revokes(engine: Engine) -> Optional[threading.Thread]:
    """At startup, retry every queued revoke that is due, off the boot path.

    A thread, so a slow Apple cannot hold up uvicorn binding its port (each
    call may wait out a 10 s timeout). Skipped when Sign in with Apple is not
    configured, where every try would fail and only use up attempts."""
    s = get_settings()
    if not (s.apple_team_id and s.apple_key_id and s.apple_bundle_id
            and s.apple_private_key_pem()):
        return None
    thread = threading.Thread(
        target=revoke_pending_apple_grants, args=(engine,),
        name="apple-revoke-retry", daemon=True)
    thread.start()
    return thread


@router.delete("/me", status_code=204)
def delete_me(
    background: BackgroundTasks,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Delete the account and everything it owns (App Store 5.1.1(v)).

    The Apple grant is revoked after the data is gone, not before, and its
    encrypted token outlives the identity it came from. Each stored token is
    copied into pending_apple_revocation in the same transaction that deletes
    the user, then sent to Apple once the response is on its way. A revoke
    that fails stays queued and is retried (revoke_pending_apple_grants), so
    a transient Apple error no longer leaves the grant active for good. A
    failed or slow revoke never blocks or delays the deletion."""
    identities = session.exec(
        select(AuthIdentity).where(AuthIdentity.user_id == user.id)
    ).all()
    queued: list[PendingAppleRevocation] = []
    for ident in identities:
        if ident.apple_refresh_token_enc:
            row = PendingAppleRevocation(token_enc=ident.apple_refresh_token_enc)
            session.add(row)
            queued.append(row)
        elif ident.provider == AuthProvider.apple:
            # The code exchange failed at sign-in, so Apple never gave this
            # server a grant to revoke. Said once here so it is not silent.
            logger.warning(
                "Deleted an Apple sign-in with no stored Apple grant: the "
                "sign-in code exchange had failed, so there is nothing to "
                "revoke; the user can remove the app in their Apple ID "
                "settings")

    tokens.revoke_all_for_user(session, user.id)

    # Plants first: ORM cascade removes their care logs and stewardship
    # records with them.
    plants = session.exec(
        select(Plant).where(Plant.user_id == user.id)).all()
    for plant in plants:
        session.delete(plant)
    session.flush()

    # GrowingAreas next. The router-level "has stewardship history" 409
    # guard is for user-initiated growing area deletes only — account
    # deletion wipes the history above, and must never be blocked.
    envs = session.exec(
        select(GrowingArea).where(GrowingArea.user_id == user.id)).all()
    for env in envs:
        session.delete(env)

    # Hard delete; ORM cascade removes AuthIdentity and RefreshToken rows.
    session.delete(user)
    session.commit()

    if queued:
        background.add_task(
            revoke_pending_apple_grants, session.get_bind(),
            [row.id for row in queued])
    return Response(status_code=204)


@router.patch("/me", response_model=UserOut)
def patch_me(
    payload: UserPatch,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if payload.display_name is not None:
        user.display_name = payload.display_name
    if payload.census_opt_in is not None:
        user.census_opt_in = payload.census_opt_in
    session.add(user)
    session.commit()
    session.refresh(user)
    return UserOut(**user.model_dump())
