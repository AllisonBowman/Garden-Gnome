"""Phase 7 acceptance: DELETE /me.

Verifies: the deleted user's access and refresh tokens are rejected; every
row they owned is gone (plants, care logs, stewardship, growing_areas,
identities, refresh tokens, the user itself); Apple revoke is called exactly
once with the decrypted stored token; a Google-only account deletes with no
revoke call; a failed revoke never blocks deletion, and is kept (encrypted,
unattributed) and retried until Apple accepts it; and the census export is
unaffected by deleted users.
"""
from datetime import datetime, timedelta

import pytest
from sqlmodel import Session, create_engine, select

from app.db.revocations import PendingAppleRevocation
from app.models.models import (
    AuthIdentity, CareLog, GrowingArea, Plant, RefreshToken,
    StewardshipRecord, User,
)
from app.services.oauth.apple import AppleClaims
from app.services.oauth.google import GoogleClaims


@pytest.fixture()
def api(migrated_db_url, monkeypatch):
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

        def db(self):
            return Session(self.engine)

    yield Api()
    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture()
def revoke_spy(monkeypatch):
    """Spy on the Apple revoke call at the router's import site."""
    calls: list[str] = []

    from app.routers import auth as auth_router
    monkeypatch.setattr(
        auth_router, "revoke_apple_token",
        lambda token: calls.append(token) or True)
    return calls


def _apple_user(api, monkeypatch, sub, email, exchange="apple-rt-del"):
    from app.routers import auth as auth_router
    monkeypatch.setattr(
        auth_router, "verify_apple_token",
        lambda tok, nonce: AppleClaims(
            sub=sub, email=email, email_verified=True,
            is_private_email=False))
    monkeypatch.setattr(
        auth_router, "exchange_apple_code", lambda code: exchange)
    r = api.client.post("/auth/apple", json={
        "identity_token": "m", "authorization_code": "m", "raw_nonce": "m",
    })
    assert r.status_code == 200, r.text
    return r.json()


def _google_user(api, monkeypatch, sub, email):
    from app.routers import auth as auth_router
    monkeypatch.setattr(
        auth_router, "verify_google_token",
        lambda tok: GoogleClaims(sub=sub, email=email, name=None, picture=None))
    r = api.client.post("/auth/google", json={"id_token": "m"})
    assert r.status_code == 200, r.text
    return r.json()


def _species_id(api) -> int:
    with api.db() as s:
        from app.models.models import Species
        sp = s.exec(select(Species)).first()
        if sp is None:
            sp = Species(
                common_name="Del Fern", scientific_name="Deletus testus",
                light_need="medium", humidity_pct_min=40, humidity_pct_max=60,
                temp_f_min=60, temp_f_max=80, soil_type="mix")
            s.add(sp)
            s.commit()
            s.refresh(sp)
        return sp.id


def _populate_garden(api, signin) -> dict:
    """Create a plant (opens a stewardship record), log care, and transfer it
    (more stewardship + a transfer log) so deletion has real depth to wipe."""
    h = {"Authorization": f"Bearer {signin['access_token']}"}
    plant = api.client.post("/plants/", json={
        "nickname": "Doomed", "species_id": _species_id(api),
    }, headers=h).json()
    api.client.post(f"/plants/{plant['id']}/logs",
                    json={"action": "water"}, headers=h)
    env2 = api.client.post("/growing-areas/", json={
        "name": "Second", "type": "balcony"}, headers=h).json()
    api.client.post(f"/plants/{plant['id']}/transfer",
                    json={"to_growing_area_id": env2["id"]}, headers=h)
    return {"plant_id": plant["id"], "headers": h}


def test_delete_me_wipes_everything_and_revokes_apple_once(
        api, monkeypatch, revoke_spy):
    signin = _apple_user(api, monkeypatch, "del-sub-1", "doomed@example.com")
    garden = _populate_garden(api, signin)
    uid = signin["user"]["id"]
    plant_id = garden["plant_id"]

    r = api.client.delete("/me", headers=garden["headers"])
    assert r.status_code == 204

    # Apple revoke: exactly once, with the decrypted stored token
    assert revoke_spy == ["apple-rt-del"]

    with api.db() as s:
        assert s.get(User, uid) is None  # hard-deleted
        assert s.exec(select(AuthIdentity).where(
            AuthIdentity.user_id == uid)).all() == []
        assert s.exec(select(RefreshToken).where(
            RefreshToken.user_id == uid)).all() == []
        assert s.exec(select(Plant).where(
            Plant.user_id == uid)).all() == []
        assert s.exec(select(CareLog).where(
            CareLog.plant_id == plant_id)).all() == []
        assert s.exec(select(StewardshipRecord).where(
            StewardshipRecord.plant_id == plant_id)).all() == []
        assert s.exec(select(GrowingArea).where(
            GrowingArea.user_id == uid)).all() == []

    # Both token kinds now rejected
    assert api.client.get("/me", headers=garden["headers"]).status_code == 401
    assert api.client.post("/auth/refresh", json={
        "refresh_token": signin["refresh_token"]}).status_code == 401


def test_google_only_account_deletes_with_no_revoke_call(
        api, monkeypatch, revoke_spy):
    signin = _google_user(api, monkeypatch, "del-g-sub", "gdel@example.com")
    h = {"Authorization": f"Bearer {signin['access_token']}"}
    assert api.client.delete("/me", headers=h).status_code == 204
    assert revoke_spy == []  # no Apple identity -> no revoke attempt
    with api.db() as s:
        assert s.get(User, signin["user"]["id"]) is None


def test_failed_apple_revoke_never_blocks_deletion(api, monkeypatch):
    signin = _apple_user(api, monkeypatch, "del-sub-2", "doomed2@example.com")
    h = {"Authorization": f"Bearer {signin['access_token']}"}

    from app.routers import auth as auth_router

    def explode(token):
        raise RuntimeError("apple is down")

    monkeypatch.setattr(auth_router, "revoke_apple_token", explode)
    assert api.client.delete("/me", headers=h).status_code == 204
    with api.db() as s:
        assert s.get(User, signin["user"]["id"]) is None


# --- A failed revoke is kept, and tried again --------------------------------
#
# Deleting the identity used to delete the only copy of the Apple token in the
# same transaction, so "retry the revoke out of band" had nothing to retry
# with. The token now waits in pending_apple_revocation, encrypted and with
# nothing beside it that says whose it was, until Apple accepts the revoke.


def _queued(api) -> dict[str, PendingAppleRevocation]:
    """Every waiting revoke, by its decrypted token."""
    from cryptography.fernet import Fernet

    from app.config import get_settings
    fernet = Fernet(get_settings().fernet_key.encode())
    with api.db() as s:
        rows = s.exec(select(PendingAppleRevocation)).all()
        return {fernet.decrypt(r.token_enc.encode()).decode(): r for r in rows}


def _queue(api, token: str, **fields) -> int:
    from cryptography.fernet import Fernet

    from app.config import get_settings
    fernet = Fernet(get_settings().fernet_key.encode())
    with api.db() as s:
        row = PendingAppleRevocation(
            token_enc=fernet.encrypt(token.encode()).decode(), **fields)
        s.add(row)
        s.commit()
        return row.id


@pytest.mark.parametrize("apple_says", ["raises", "refuses"])
def test_a_failed_revoke_is_queued_with_nothing_that_names_the_user(
        api, monkeypatch, apple_says):
    token = f"apple-rt-{apple_says}"
    signin = _apple_user(api, monkeypatch, f"q-{apple_says}",
                         f"q-{apple_says}@example.com", exchange=token)
    h = {"Authorization": f"Bearer {signin['access_token']}"}

    from app.routers import auth as auth_router

    def down(_token):
        if apple_says == "raises":
            raise RuntimeError("apple is down")
        return False  # what revoke_apple_token returns on a non-200

    monkeypatch.setattr(auth_router, "revoke_apple_token", down)
    assert api.client.delete("/me", headers=h).status_code == 204

    # Deletion still happened in full...
    with api.db() as s:
        assert s.get(User, signin["user"]["id"]) is None
        assert s.exec(select(AuthIdentity).where(
            AuthIdentity.user_id == signin["user"]["id"])).all() == []
    # ...and the token survived it, tried once, holding no user id or email.
    row = _queued(api)[token]
    assert row.attempts == 1 and row.last_attempt_at is not None
    assert set(PendingAppleRevocation.model_fields) == {
        "id", "token_enc", "created_at", "attempts", "last_attempt_at"}

    # Apple comes back. Once the backoff has passed, the revoke goes through
    # and the queued copy is gone.
    sent = []
    monkeypatch.setattr(auth_router, "revoke_apple_token",
                        lambda t: sent.append(t) or True)
    with api.db() as s:
        stored = s.get(PendingAppleRevocation, row.id)
        stored.last_attempt_at = datetime.utcnow() - timedelta(hours=1)
        s.add(stored)
        s.commit()
    assert auth_router.revoke_pending_apple_grants(api.engine, [row.id]) == 1
    assert sent == [token]
    assert token not in _queued(api)


def test_a_successful_revoke_leaves_nothing_queued(api, monkeypatch, revoke_spy):
    signin = _apple_user(api, monkeypatch, "q-ok", "q-ok@example.com",
                         exchange="apple-rt-accepted")
    h = {"Authorization": f"Bearer {signin['access_token']}"}
    assert api.client.delete("/me", headers=h).status_code == 204
    assert revoke_spy == ["apple-rt-accepted"]
    assert "apple-rt-accepted" not in _queued(api)


def test_retries_back_off_and_stop(api, monkeypatch):
    from app.routers import auth as auth_router

    sent = []
    monkeypatch.setattr(auth_router, "revoke_apple_token",
                        lambda t: sent.append(t) or False)
    now = datetime.utcnow()
    just_failed = _queue(api, "rt-just-failed", attempts=1, last_attempt_at=now)
    waited = _queue(api, "rt-waited", attempts=1,
                    last_attempt_at=now - auth_router.REVOKE_BACKOFF)
    second_wait = _queue(api, "rt-second-wait", attempts=2,
                         last_attempt_at=now - auth_router.REVOKE_BACKOFF)
    spent = _queue(api, "rt-spent", attempts=auth_router.MAX_REVOKE_ATTEMPTS,
                   last_attempt_at=now - timedelta(days=30))

    auth_router.revoke_pending_apple_grants(
        api.engine, [just_failed, waited, second_wait, spent])

    # Due: one backoff after the first failure. Not yet: one backoff after
    # the second (it doubles), straight after a failure, or out of tries.
    assert sent == ["rt-waited"]
    queued = _queued(api)
    assert queued["rt-waited"].attempts == 2
    assert queued["rt-spent"].attempts == auth_router.MAX_REVOKE_ATTEMPTS

    with api.db() as s:  # leave the shared database as we found it
        for row_id in (just_failed, waited, second_wait, spent):
            s.delete(s.get(PendingAppleRevocation, row_id))
        s.commit()


def test_an_apple_sign_in_with_no_stored_grant_is_logged(
        api, monkeypatch, revoke_spy, caplog):
    signin = _apple_user(api, monkeypatch, "q-none", "q-none@example.com",
                         exchange=None)
    h = {"Authorization": f"Bearer {signin['access_token']}"}
    with caplog.at_level("WARNING", logger="app.routers.auth"):
        assert api.client.delete("/me", headers=h).status_code == 204
    assert revoke_spy == []
    assert any("no stored Apple grant" in r.getMessage() for r in caplog.records)


def test_startup_retries_the_queue_only_when_apple_is_configured(
        api, monkeypatch):
    from app.config import get_settings
    from app.routers import auth as auth_router

    with api.db() as s:  # this test retries the whole queue
        for row in s.exec(select(PendingAppleRevocation)).all():
            s.delete(row)
        s.commit()
    _queue(api, "rt-at-boot")
    sent = []
    monkeypatch.setattr(auth_router, "revoke_apple_token",
                        lambda t: sent.append(t) or True)

    monkeypatch.delenv("APPLE_PRIVATE_KEY", raising=False)
    monkeypatch.delenv("APPLE_PRIVATE_KEY_PATH", raising=False)
    get_settings.cache_clear()
    try:
        assert auth_router.start_queued_apple_revokes(api.engine) is None
        assert sent == []

        monkeypatch.setenv("APPLE_PRIVATE_KEY", "-----BEGIN PRIVATE KEY-----")
        get_settings.cache_clear()
        thread = auth_router.start_queued_apple_revokes(api.engine)
        assert thread is not None and thread.daemon
        thread.join(timeout=10)
    finally:
        get_settings.cache_clear()
    assert sent == ["rt-at-boot"]
    assert _queued(api) == {}


def test_census_export_unaffected_by_deleted_users(
        api, monkeypatch, revoke_spy):
    keeper = _google_user(api, monkeypatch, "keep-sub", "keep@example.com")
    kh = {"Authorization": f"Bearer {keeper['access_token']}"}
    api.client.patch("/me", json={"census_opt_in": True}, headers=kh)
    keeper_plant = api.client.post("/plants/", json={
        "nickname": "Keeper", "species_id": _species_id(api)}, headers=kh).json()

    doomed = _apple_user(api, monkeypatch, "del-sub-3", "doomed3@example.com")
    dh = {"Authorization": f"Bearer {doomed['access_token']}"}
    api.client.patch("/me", json={"census_opt_in": True}, headers=dh)
    doomed_plant = api.client.post("/plants/", json={
        "nickname": "Gone", "species_id": _species_id(api)}, headers=dh).json()

    from tests import census_operator
    census_operator.pin_salt(monkeypatch)
    keeper_ref = census_operator.ref(keeper_plant["plant_uuid"])
    doomed_ref = census_operator.ref(doomed_plant["plant_uuid"])

    before = census_operator.export(api.client, monkeypatch)
    refs_before = {p["plant_ref"] for p in before["plants"]}
    assert {keeper_ref, doomed_ref} <= refs_before

    assert api.client.delete("/me", headers=dh).status_code == 204

    after = census_operator.export(api.client, monkeypatch)
    refs_after = {p["plant_ref"] for p in after["plants"]}
    assert keeper_ref in refs_after
    assert doomed_ref not in refs_after
