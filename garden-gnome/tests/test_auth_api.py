"""Phase 5 acceptance: auth API integration tests with mocked providers.

Covers first sign-in (user + identity + default environment created), repeat
sign-in, email-based identity linking, refresh rotation, logout, and 401s.
Provider verification is monkeypatched at the router's import site; the token
service and database run for real against the migrated test DB.
"""
from cryptography.fernet import Fernet
import pytest
from sqlmodel import Session, create_engine, select

from app.config import get_settings
from app.models.models import (
    AuthIdentity, Environment, User,
)
from app.services.oauth import ProviderTokenError
from app.services.oauth.apple import AppleClaims
from app.services.oauth.google import GoogleClaims


@pytest.fixture()
def api(migrated_db_url, monkeypatch):
    """TestClient wired to the migrated test DB (no lifespan → no migrations
    against the real dev DB), plus handles to the same engine for asserts."""
    from fastapi.testclient import TestClient

    from app.db.database import get_session
    from app.main import app

    engine = create_engine(
        migrated_db_url, connect_args={"check_same_thread": False})

    def override():
        with Session(engine) as s:
            yield s

    app.dependency_overrides[get_session] = override
    client = TestClient(app)

    class Api:
        def __init__(self):
            self.client = client
            self.engine = engine

        def db(self) -> Session:
            return Session(self.engine)

    yield Api()
    app.dependency_overrides.clear()
    engine.dispose()


def _mock_apple(monkeypatch, sub="apple-sub-1", email="a@example.com",
                verified=True, private=False, exchange="apple-rt-1"):
    from app.routers import auth as auth_router
    monkeypatch.setattr(
        auth_router, "verify_apple_token",
        lambda tok, nonce: AppleClaims(
            sub=sub, email=email, email_verified=verified,
            is_private_email=private))
    monkeypatch.setattr(
        auth_router, "exchange_apple_code", lambda code: exchange)


def _mock_google(monkeypatch, sub="google-sub-1", email="g@example.com",
                 name="Gee User"):
    from app.routers import auth as auth_router
    monkeypatch.setattr(
        auth_router, "verify_google_token",
        lambda tok: GoogleClaims(
            sub=sub, email=email, name=name, picture=None))


APPLE_BODY = {
    "identity_token": "mocked",
    "authorization_code": "mocked-code",
    "raw_nonce": "mocked-nonce",
    "full_name": "Allison B",
}


def test_apple_first_sign_in_creates_everything(api, monkeypatch):
    _mock_apple(monkeypatch)
    r = api.client.post("/auth/apple", json=APPLE_BODY)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["access_token"] and body["refresh_token"]
    assert body["user"]["email"] == "a@example.com"
    assert body["user"]["display_name"] == "Allison B"  # persisted first-auth name
    assert body["user"]["census_opt_in"] is False

    with api.db() as s:
        user = s.get(User, body["user"]["id"])
        assert user.last_login_at is not None
        idents = s.exec(select(AuthIdentity).where(
            AuthIdentity.user_id == user.id)).all()
        assert len(idents) == 1
        # Apple refresh token stored encrypted, decryptable with our key
        fernet = Fernet(get_settings().fernet_key.encode())
        assert fernet.decrypt(
            idents[0].apple_refresh_token_enc.encode()).decode() == "apple-rt-1"
        envs = s.exec(select(Environment).where(
            Environment.user_id == user.id)).all()
        assert [(e.name, e.type.value) for e in envs] == [("My Home", "home")]

    # The issued access token works on /me
    me = api.client.get(
        "/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200
    assert me.json()["id"] == body["user"]["id"]


def test_apple_repeat_sign_in_reuses_account(api, monkeypatch):
    _mock_apple(monkeypatch, sub="apple-sub-repeat", email="r@example.com")
    first = api.client.post("/auth/apple", json=APPLE_BODY).json()
    second = api.client.post("/auth/apple", json=APPLE_BODY).json()
    assert first["user"]["id"] == second["user"]["id"]

    with api.db() as s:
        uid = first["user"]["id"]
        idents = s.exec(select(AuthIdentity).where(
            AuthIdentity.user_id == uid)).all()
        envs = s.exec(select(Environment).where(
            Environment.user_id == uid)).all()
        assert len(idents) == 1  # no duplicate identity
        assert len(envs) == 1    # no duplicate default environment


def test_google_links_to_existing_user_by_verified_email(api, monkeypatch):
    _mock_apple(monkeypatch, sub="apple-sub-link", email="link@example.com")
    apple_user = api.client.post("/auth/apple", json=APPLE_BODY).json()["user"]

    _mock_google(monkeypatch, sub="google-sub-link", email="link@example.com")
    google_user = api.client.post(
        "/auth/google", json={"id_token": "mocked"}).json()["user"]

    assert google_user["id"] == apple_user["id"]  # linked, not duplicated
    with api.db() as s:
        idents = s.exec(select(AuthIdentity).where(
            AuthIdentity.user_id == apple_user["id"])).all()
        assert sorted(i.provider.value for i in idents) == ["apple", "google"]
        envs = s.exec(select(Environment).where(
            Environment.user_id == apple_user["id"])).all()
        assert len(envs) == 1  # linking creates no second default env


def test_google_new_user_gets_default_environment(api, monkeypatch):
    _mock_google(monkeypatch, sub="google-sub-new", email="new-g@example.com")
    body = api.client.post("/auth/google", json={"id_token": "mocked"}).json()
    assert body["user"]["display_name"] == "Gee User"
    with api.db() as s:
        envs = s.exec(select(Environment).where(
            Environment.user_id == body["user"]["id"])).all()
        assert [(e.name, e.type.value) for e in envs] == [("My Home", "home")]


def test_refresh_rotation_and_reuse_401(api, monkeypatch):
    _mock_apple(monkeypatch, sub="apple-sub-rot", email="rot@example.com")
    signin = api.client.post("/auth/apple", json=APPLE_BODY).json()

    r1 = api.client.post(
        "/auth/refresh", json={"refresh_token": signin["refresh_token"]})
    assert r1.status_code == 200
    pair1 = r1.json()
    assert pair1["refresh_token"] != signin["refresh_token"]

    # Old token again → reuse detection → 401 (and family is dead)
    r2 = api.client.post(
        "/auth/refresh", json={"refresh_token": signin["refresh_token"]})
    assert r2.status_code == 401
    r3 = api.client.post(
        "/auth/refresh", json={"refresh_token": pair1["refresh_token"]})
    assert r3.status_code == 401  # newest token was revoked with the family


def test_logout_then_refresh_401(api, monkeypatch):
    _mock_apple(monkeypatch, sub="apple-sub-out", email="out@example.com")
    signin = api.client.post("/auth/apple", json=APPLE_BODY).json()
    out = api.client.post(
        "/auth/logout", json={"refresh_token": signin["refresh_token"]})
    assert out.status_code == 204
    r = api.client.post(
        "/auth/refresh", json={"refresh_token": signin["refresh_token"]})
    assert r.status_code == 401


def test_provider_rejection_is_401(api, monkeypatch):
    from app.routers import auth as auth_router

    def boom(tok, nonce):
        raise ProviderTokenError("bad token")

    monkeypatch.setattr(auth_router, "verify_apple_token", boom)
    r = api.client.post("/auth/apple", json=APPLE_BODY)
    assert r.status_code == 401


def test_me_requires_valid_token(api):
    assert api.client.get("/me").status_code == 401
    assert api.client.get(
        "/me", headers={"Authorization": "Bearer garbage"}).status_code == 401


def test_patch_me_updates_display_name(api, monkeypatch):
    _mock_apple(monkeypatch, sub="apple-sub-patch", email="p@example.com")
    signin = api.client.post("/auth/apple", json=APPLE_BODY).json()
    headers = {"Authorization": f"Bearer {signin['access_token']}"}
    r = api.client.patch(
        "/me", json={"display_name": "Plant Advocate"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["display_name"] == "Plant Advocate"


def test_apple_exchange_failure_does_not_block_sign_in(api, monkeypatch):
    _mock_apple(monkeypatch, sub="apple-sub-nox", email="nox@example.com",
                exchange=None)  # code exchange failed → None by contract
    r = api.client.post("/auth/apple", json=APPLE_BODY)
    assert r.status_code == 200
    with api.db() as s:
        ident = s.exec(select(AuthIdentity).where(
            AuthIdentity.provider_sub == "apple-sub-nox")).one()
        assert ident.apple_refresh_token_enc is None
