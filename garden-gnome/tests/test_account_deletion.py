"""Phase 7 acceptance: DELETE /me.

Verifies: the deleted user's access and refresh tokens are rejected; every
row they owned is gone (plants, care logs, stewardship, environments,
identities, refresh tokens, the user itself); Apple revoke is called exactly
once with the decrypted stored token; a Google-only account deletes with no
revoke call; a failed revoke never blocks deletion; and the census export is
unaffected by deleted users.
"""
import pytest
from sqlmodel import Session, create_engine, select

from app.models.models import (
    AuthIdentity, CareLog, Environment, Plant, RefreshToken,
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
    env2 = api.client.post("/environments/", json={
        "name": "Second", "type": "balcony"}, headers=h).json()
    api.client.post(f"/plants/{plant['id']}/transfer",
                    json={"to_environment_id": env2["id"]}, headers=h)
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
        assert s.exec(select(Environment).where(
            Environment.user_id == uid)).all() == []

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

    before = api.client.get("/census/export", headers=kh).json()
    uuids_before = {p["plant_uuid"] for p in before["plants"]}
    assert {keeper_plant["plant_uuid"], doomed_plant["plant_uuid"]} <= uuids_before

    assert api.client.delete("/me", headers=dh).status_code == 204

    after = api.client.get("/census/export", headers=kh).json()
    uuids_after = {p["plant_uuid"] for p in after["plants"]}
    assert keeper_plant["plant_uuid"] in uuids_after
    assert doomed_plant["plant_uuid"] not in uuids_after
