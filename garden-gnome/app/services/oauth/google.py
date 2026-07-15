"""Google Sign-In: id_token verification against Google's JWKS."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import jwt

from app.config import get_settings
from app.services.oauth.errors import (
    ProviderConfigError, ProviderTokenError, UnverifiedEmail,
)
from app.services.oauth.jwks import JWKSCache

GOOGLE_ISSUERS = {"accounts.google.com", "https://accounts.google.com"}
GOOGLE_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
LEEWAY_SECONDS = 30

_jwks = JWKSCache(GOOGLE_JWKS_URL)


@dataclass
class GoogleClaims:
    sub: str
    email: str
    name: Optional[str]
    picture: Optional[str]


def verify_google_token(id_token: str) -> GoogleClaims:
    s = get_settings()
    if not s.google_client_id:
        raise ProviderConfigError(
            "GOOGLE_CLIENT_ID is not configured (see plan Phase 0)")

    try:
        kid = jwt.get_unverified_header(id_token).get("kid", "")
        key = _jwks.get_key(kid)
        payload = jwt.decode(
            id_token,
            key.key,
            algorithms=["RS256"],
            audience=s.google_client_id,
            leeway=LEEWAY_SECONDS,
            options={"require": ["sub", "iss", "aud", "exp"]},
        )
    except jwt.InvalidTokenError as e:
        raise ProviderTokenError(f"Google id_token invalid: {e}") from e

    # Two legitimate issuer spellings — checked here, not via jwt.decode
    if payload.get("iss") not in GOOGLE_ISSUERS:
        raise ProviderTokenError(
            f"Google id_token has unexpected issuer {payload.get('iss')!r}")

    if payload.get("email_verified") is not True and payload.get(
            "email_verified") != "true":
        raise UnverifiedEmail("Google account email is not verified")

    return GoogleClaims(
        sub=payload["sub"],
        email=payload["email"],
        name=payload.get("name"),
        picture=payload.get("picture"),
    )
