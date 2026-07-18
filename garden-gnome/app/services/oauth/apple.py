"""Sign in with Apple: identity-token verification and code exchange.

verify_apple_token validates the client-supplied identity token against
Apple's JWKS (aud=our bundle id, iss=Apple, RS256, nonce binding).

exchange_apple_code trades the one-time authorization code for Apple's
refresh token — stored (Fernet-encrypted, by the caller) solely so account
deletion can revoke the user's Apple session per App Store 5.1.1(v).
"""
from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import httpx
import jwt

from app.config import get_settings
from app.services.oauth.errors import (
    NonceMismatch, ProviderConfigError, ProviderTokenError,
)
from app.services.oauth.jwks import JWKSCache

logger = logging.getLogger(__name__)

APPLE_ISSUER = "https://appleid.apple.com"
APPLE_JWKS_URL = "https://appleid.apple.com/auth/keys"
APPLE_TOKEN_URL = "https://appleid.apple.com/auth/token"
APPLE_REVOKE_URL = "https://appleid.apple.com/auth/revoke"
LEEWAY_SECONDS = 30

_jwks = JWKSCache(APPLE_JWKS_URL)


@dataclass
class AppleClaims:
    sub: str
    email: Optional[str]
    email_verified: bool
    is_private_email: bool


def _to_bool(value) -> bool:
    # Apple sends booleans sometimes as JSON bools, sometimes as "true"/"false"
    return value is True or value == "true"


def verify_apple_token(identity_token: str, raw_nonce: str) -> AppleClaims:
    s = get_settings()
    if not s.apple_bundle_id:
        raise ProviderConfigError(
            "APPLE_BUNDLE_ID is not configured (see plan Phase 0)")

    try:
        kid = jwt.get_unverified_header(identity_token).get("kid", "")
        key = _jwks.get_key(kid)
        payload = jwt.decode(
            identity_token,
            key.key,
            algorithms=["RS256"],
            audience=s.apple_bundle_id,
            issuer=APPLE_ISSUER,
            leeway=LEEWAY_SECONDS,
            options={"require": ["sub", "iss", "aud", "exp"]},
        )
    except jwt.InvalidTokenError as e:
        raise ProviderTokenError(f"Apple identity token invalid: {e}") from e

    # The client sends its raw nonce; Apple embedded sha256(raw_nonce).
    expected = hashlib.sha256(raw_nonce.encode("utf-8")).hexdigest()
    if payload.get("nonce") != expected:
        raise NonceMismatch("Apple identity token nonce mismatch")

    return AppleClaims(
        sub=payload["sub"],
        email=payload.get("email"),
        email_verified=_to_bool(payload.get("email_verified")),
        is_private_email=_to_bool(payload.get("is_private_email")),
    )


def _build_client_secret() -> str:
    """ES256 JWT that authenticates us to Apple's token endpoint."""
    s = get_settings()
    private_key = s.apple_private_key_pem()
    if not (s.apple_team_id and s.apple_key_id and s.apple_bundle_id
            and private_key):
        raise ProviderConfigError(
            "Apple key settings are not configured — set APPLE_TEAM_ID, "
            "APPLE_KEY_ID, APPLE_BUNDLE_ID, and either APPLE_PRIVATE_KEY "
            "(inline PEM) or APPLE_PRIVATE_KEY_PATH (see plan Phase 0)")

    now = datetime.utcnow()
    return jwt.encode(
        {
            "iss": s.apple_team_id,
            "iat": now,
            # Short-lived: built fresh per call (Apple caps exp at 6 months)
            "exp": now + timedelta(minutes=20),
            "aud": APPLE_ISSUER,
            "sub": s.apple_bundle_id,
        },
        private_key,
        algorithm="ES256",
        headers={"kid": s.apple_key_id},
    )


def exchange_apple_code(authorization_code: str) -> Optional[str]:
    """Exchange the authorization code for Apple's refresh token.

    Returns None on any failure — per plan, a failed exchange must not block
    sign-in (it only degrades account-deletion revocation later); the caller
    logs a warning and continues."""
    s = get_settings()
    try:
        resp = httpx.post(
            APPLE_TOKEN_URL,
            data={
                "client_id": s.apple_bundle_id,
                "client_secret": _build_client_secret(),
                "code": authorization_code,
                "grant_type": "authorization_code",
            },
            timeout=10.0,
        )
        resp.raise_for_status()
        return resp.json().get("refresh_token")
    except Exception as e:  # noqa: BLE001 — deliberately broad: never block sign-in
        logger.warning(
            "Apple code exchange failed; continuing sign-in without a stored "
            "refresh token (account-deletion revocation degraded): %s", e)
        return None


def revoke_apple_token(refresh_token: str) -> bool:
    """Revoke the user's Apple session (App Store 5.1.1(v), TN3194).

    Called during account deletion with the stored (decrypted) refresh token
    and a fresh client_secret. Any non-200 or network failure is logged as a
    retryable event and returns False — deletion MUST proceed regardless."""
    s = get_settings()
    try:
        resp = httpx.post(
            APPLE_REVOKE_URL,
            data={
                "client_id": s.apple_bundle_id,
                "client_secret": _build_client_secret(),
                "token": refresh_token,
                "token_type_hint": "refresh_token",
            },
            timeout=10.0,
        )
        if resp.status_code != 200:
            logger.warning(
                "RETRYABLE: Apple token revoke returned %s — deletion "
                "proceeds; retry the revoke out of band.", resp.status_code)
            return False
        return True
    except Exception as e:  # noqa: BLE001 — deliberately broad: never block deletion
        logger.warning(
            "RETRYABLE: Apple token revoke failed (%s) — deletion proceeds; "
            "retry the revoke out of band.", e)
        return False
