"""Every /species route requires a signed-in caller.

The catalog is populated by direct DB writes (seed.py / the offline expansion
pipeline), and the app only reads /species post-login with a bearer token, so
none of these routes should serve anonymous requests — reads OR writes.
"""
import pytest
from sqlmodel import Session, create_engine, select


@pytest.fixture()
def api(migrated_db_url):
    from fastapi.testclient import TestClient

    from app.db.database import get_session
    from app.main import app
    from app.models.models import User
    from app.services import tokens

    engine = create_engine(migrated_db_url, connect_args={"check_same_thread": False})

    def override():
        with Session(engine) as s:
            yield s

    app.dependency_overrides[get_session] = override

    with Session(engine) as s:
        user = User(email="species@example.com")
        s.add(user)
        s.commit()
        headers = {"Authorization": f"Bearer {tokens.issue_access_token(user.id)}"}

    client = TestClient(app)
    try:
        yield client, headers
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


# (method, path, kwargs) for every species route.
ROUTES = [
    ("get", "/species/", {}),
    ("get", "/species/1", {}),
    ("post", "/species/", {"json": {}}),
    ("post", "/species/bulk", {"json": []}),
    ("post", "/species/generate", {"json": {"name": "Basil"}}),
    ("post", "/species/identify-photo",
     {"files": {"photo": ("p.jpg", b"\xff\xd8\xff bytes", "image/jpeg")}}),
]


@pytest.mark.parametrize("method,path,kwargs", ROUTES)
def test_species_route_requires_auth(api, method, path, kwargs):
    client, _ = api
    resp = getattr(client, method)(path, **kwargs)
    assert resp.status_code == 401, f"{method.upper()} {path} was reachable without a token"


def test_species_list_works_with_a_token(api):
    client, headers = api
    resp = client.get("/species/", headers=headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
