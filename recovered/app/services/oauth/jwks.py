"""Shared JWKS helper: fetch, cache ~6h, refetch once on unknown kid.

Providers rotate signing keys; the refetch-once behavior picks up a rotation
immediately without hammering the endpoint on genuinely bogus kids.
"""
from __future__ import annotations

import time

import httpx
from jwt import PyJWK

from app.services.oauth.errors import JWKSUnavailable, UnknownKeyId

CACHE_TTL_SECONDS = 6 * 60 * 60


class JWKSCache:
    def __init__(self, url: str, ttl_seconds: int = CACHE_TTL_SECONDS):
        self.url = url
        self.ttl = ttl_seconds
        self._keys: dict[str, PyJWK] = {}
        self._fetched_at: float = 0.0

    def clear(self) -> None:
        """Reset cached keys (used by tests)."""
        self._keys = {}
        self._fetched_at = 0.0

    def _fetch(self) -> None:
        try:
            resp = httpx.get(self.url, timeout=10.0)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPError as e:
            raise JWKSUnavailable(f"JWKS fetch from {self.url} failed: {e}") from e
        self._keys = {
            jwk["kid"]: PyJWK.from_dict(jwk)
            for jwk in data.get("keys", [])
            if "kid" in jwk
        }
        self._fetched_at = time.monotonic()

    def get_key(self, kid: str) -> PyJWK:
        stale = (time.monotonic() - self._fetched_at) > self.ttl
        if stale or not self._keys:
            self._fetch()
        if kid not in self._keys:
            # Unknown kid: refetch exactly once — provider may have rotated
            self._fetch()
        if kid not in self._keys:
            raise UnknownKeyId(f"kid {kid!r} not present in JWKS {self.url}")
        return self._keys[kid]
