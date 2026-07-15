"""Phase 4 acceptance: provider verification with mocked JWKS.

An RSA keypair is generated in fixtures; JWKS fetches are monkeypatched so
zero real network calls happen. Covers: valid, wrong aud, wrong iss, expired,
bad nonce (Apple), unverified email (Google), unknown kid -> refetch path,
JWKS outage, and the Apple code exchange (mocked POST).
"""
import hashlib
import json
from datetime import datetime, timedelta

import jwt as pyjwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa

from app.config import get_settings
from app.services.oauth import apple, google
from app.services.oauth.errors import (
    JWKSUnavailable, NonceMismatch, ProviderTokenError, UnknownKeyId,
    UnverifiedEmail,
)

KID = "test-key-1"
KID2 = "rotated-key-2"


# --- Key material & JWKS fixtures ---------------------------------------------


@pytest.fixture(scope="module")
def rsa_keys():
    """Two RSA keypairs: the 'current' provider key and a 'rotated' one."""
    keys = {}
    for kid in (KID, KID2):
        private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        pem = private.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
        keys[kid] = (private, pem)
    return keys


def _jwk_for(rsa_keys, kid):
    public = rsa_keys[kid][0].public_key()
    jwk = json.loads(pyjwt.algorithms.RSAAlgorithm.to_jwk(public))
    jwk.update({"kid": kid, "use": "sig", "alg": "RS256"})
    return jwk


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


@pytest.fixture()
def patch_jwks(monkeypatch, rsa_keys):
    """Patch httpx.get inside the jwks module; returns a controller object."""
    calls = {"count": 0}
    responses = {"queue": None}

    def fake_get(url, timeout=None):
        calls["count"] += 1
        queue = responses["queue"]
        payload = queue.pop(0) if len(queue) > 1 else queue[0]
        if isinstance(payload, Exception):
            raise payload
        return FakeResponse(payload)

    from app.services.oauth import jwks as jwks_module
    monkeypatch.setattr(jwks_module.httpx, "get", fake_get)
    apple._jwks.clear()
    google._jwks.clear()

    class Controller:
        def set_keys(self, *kids):
            responses["queue"] = [
                {"keys": [_jwk_for(rsa_keys, k) for k in kids]}]

        def set_sequence(self, *payloads):
            responses["queue"] = list(payloads)

        @property
        def fetch_count(self):
            return calls["count"]

    ctl = Controller()
    ctl.set_keys(KID)
    return ctl


def _sign(rsa_keys, kid, claims):
    return pyjwt.encode(
        claims, rsa_keys[kid][1], algorithm="RS256", headers={"kid": kid})


def _apple_claims(nonce_raw="raw-nonce-123", **over):
    s = get_settings()
    now = datetime.utcnow()
    claims = {
        "iss": apple.APPLE_ISSUER,
        "aud": s.apple_bundle_id,
        "sub": "apple-sub-001",
        "iat": now,
        "exp": now + timedelta(minutes=10),
        "nonce": hashlib.sha256(nonce_raw.encode()).hexdigest(),
        "email": "relay@privaterelay.appleid.com",
        "email_verified": "true",
        "is_private_email": "true",
    }
    claims.update(over)
    return claims


def _google_claims(**over):
    s = get_settings()
    now = datetime.utcnow()
    claims = {
        "iss": "https://accounts.google.com",
        "aud": s.google_client_id,
        "sub": "google-sub-001",
        "iat": now,
        "exp": now + timedelta(minutes=10),
        "email": "user@gmail.com",
        "email_verified": True,
        "name": "Test User",
        "picture": "https://example.com/p.jpg",
    }
    claims.update(over)
    return claims


# --- Apple ---------------------------------------------------------------------


def test_apple_valid_token(patch_jwks, rsa_keys):
    token = _sign(rsa_keys, KID, _apple_claims())
    claims = apple.verify_apple_token(token, "raw-nonce-123")
    assert claims.sub == "apple-sub-001"
    assert claims.email == "relay@privaterelay.appleid.com"
    assert claims.email_verified is True
    assert claims.is_private_email is True


def test_apple_wrong_audience(patch_jwks, rsa_keys):
    token = _sign(rsa_keys, KID, _apple_claims(aud="com.someone.else"))
    with pytest.raises(ProviderTokenError):
        apple.verify_apple_token(token, "raw-nonce-123")


def test_apple_wrong_issuer(patch_jwks, rsa_keys):
    token = _sign(rsa_keys, KID, _apple_claims(iss="https://evil.example"))
    with pytest.raises(ProviderTokenError):
        apple.verify_apple_token(token, "raw-nonce-123")


def test_apple_expired(patch_jwks, rsa_keys):
    now = datetime.utcnow()
    token = _sign(rsa_keys, KID, _apple_claims(
        iat=now - timedelta(minutes=30), exp=now - timedelta(minutes=2)))
    with pytest.raises(ProviderTokenError):
        apple.verify_apple_token(token, "raw-nonce-123")


def test_apple_bad_nonce(patch_jwks, rsa_keys):
    token = _sign(rsa_keys, KID, _apple_claims(nonce_raw="the-real-nonce"))
    with pytest.raises(NonceMismatch):
        apple.verify_apple_token(token, "a-different-nonce")


# --- Google ----------------------------------------------------------------------


def test_google_valid_token(patch_jwks, rsa_keys):
    token = _sign(rsa_keys, KID, _google_claims())
    claims = google.verify_google_token(token)
    assert claims.sub == "google-sub-001"
    assert claims.email == "user@gmail.com"
    assert claims.name == "Test User"


def test_google_alternate_issuer_spelling(patch_jwks, rsa_keys):
    token = _sign(rsa_keys, KID, _google_claims(iss="accounts.google.com"))
    assert google.verify_google_token(token).sub == "google-sub-001"


def test_google_wrong_audience(patch_jwks, rsa_keys):
    token = _sign(rsa_keys, KID, _google_claims(aud="other-client"))
    with pytest.raises(ProviderTokenError):
        google.verify_google_token(token)


def test_google_wrong_issuer(patch_jwks, rsa_keys):
    token = _sign(rsa_keys, KID, _google_claims(iss="https://evil.example"))
    with pytest.raises(ProviderTokenError):
        google.verify_google_token(token)


def test_google_unverified_email(patch_jwks, rsa_keys):
    token = _sign(rsa_keys, KID, _google_claims(email_verified=False))
    with pytest.raises(UnverifiedEmail):
        google.verify_google_token(token)


# --- JWKS cache behavior -----------------------------------------------------------


def test_unknown_kid_triggers_single_refetch_then_succeeds(
        patch_jwks, rsa_keys):
    # First fetch returns only the old key; refetch returns the rotated one
    patch_jwks.set_sequence(
        {"keys": [_jwk_for(rsa_keys, KID)]},
        {"keys": [_jwk_for(rsa_keys, KID), _jwk_for(rsa_keys, KID2)]},
    )
    token = _sign(rsa_keys, KID2, _google_claims())
    assert google.verify_google_token(token).sub == "google-sub-001"
    assert patch_jwks.fetch_count == 2  # initial + exactly one refetch


def test_unknown_kid_after_refetch_fails(patch_jwks, rsa_keys):
    patch_jwks.set_keys(KID)  # never contains KID2
    token = _sign(rsa_keys, KID2, _google_claims())
    with pytest.raises(UnknownKeyId):
        google.verify_google_token(token)
    assert patch_jwks.fetch_count == 2  # refetched once, not in a loop


def test_jwks_outage(patch_jwks, rsa_keys, monkeypatch):
    import httpx

    from app.services.oauth import jwks as jwks_module

    def dead_get(url, timeout=None):
        raise httpx.ConnectError("no route to provider")

    monkeypatch.setattr(jwks_module.httpx, "get", dead_get)
    apple._jwks.clear()
    token = _sign(rsa_keys, KID, _apple_claims())
    with pytest.raises(JWKSUnavailable):
        apple.verify_apple_token(token, "raw-nonce-123")


# --- Apple code exchange ------------------------------------------------------------


@pytest.fixture()
def apple_signing_key(tmp_path, monkeypatch):
    """A P-256 .p8 key on disk + settings pointing at it."""
    private = ec.generate_private_key(ec.SECP256R1())
    pem = private.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    key_path = tmp_path / "AuthKey_TESTKEY123.p8"
    key_path.write_bytes(pem)
    monkeypatch.setenv("APPLE_PRIVATE_KEY_PATH", str(key_path))
    get_settings.cache_clear()
    yield private.public_key()
    get_settings.cache_clear()


def test_exchange_apple_code_success(apple_signing_key, monkeypatch):
    captured = {}

    def fake_post(url, data=None, timeout=None):
        captured["url"] = url
        captured["data"] = data
        return FakeResponse({"refresh_token": "apple-refresh-xyz",
                             "access_token": "ignored"})

    monkeypatch.setattr(apple.httpx, "post", fake_post)
    result = apple.exchange_apple_code("auth-code-123")

    assert result == "apple-refresh-xyz"
    assert captured["url"] == apple.APPLE_TOKEN_URL
    assert captured["data"]["grant_type"] == "authorization_code"
    assert captured["data"]["code"] == "auth-code-123"

    # The client_secret must be an ES256 JWT signed with our .p8 key,
    # carrying the Phase-0 identifiers.
    secret = captured["data"]["client_secret"]
    header = pyjwt.get_unverified_header(secret)
    assert header["alg"] == "ES256"
    assert header["kid"] == "TESTKEY123"
    claims = pyjwt.decode(
        secret, apple_signing_key, algorithms=["ES256"],
        audience=apple.APPLE_ISSUER)
    assert claims["iss"] == "TESTTEAM99"
    assert claims["sub"] == "com.allisonbowman.plantadvocate"


def test_exchange_apple_code_failure_returns_none(
        apple_signing_key, monkeypatch, caplog):
    import httpx

    def dead_post(url, data=None, timeout=None):
        raise httpx.ConnectError("apple is down")

    monkeypatch.setattr(apple.httpx, "post", dead_post)
    with caplog.at_level("WARNING"):
        assert apple.exchange_apple_code("auth-code-123") is None
    assert any("exchange failed" in r.message for r in caplog.records)


# --- Issuer rename (decision 2) ------------------------------------------------------


def test_our_jwt_issuer_is_plantadvocate():
    from app.services import tokens
    assert tokens.ISSUER == "plantadvocate"
