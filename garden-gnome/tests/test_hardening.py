"""Phase 9 acceptance: rate limiting + checklist pins.

The 429 test enables the limiter for its own scope only (the suite otherwise
runs with it disabled — all TestClient requests share one 'IP').
"""
import pytest
from sqlmodel import Session, create_engine

from app.rate_limit import SIGNIN_LIMIT, limiter


@pytest.fixture()
def api(migrated_db_url):
    from fastapi.testclient import TestClient

    from app.db.database import get_session
    from app.main import app

    engine = create_engine(
        migrated_db_url, connect_args={"check_same_thread": False})

    def override():
        with Session(engine) as s:
            yield s

    app.dependency_overrides[get_session] = override
    yield TestClient(app)
    app.dependency_overrides.clear()
    engine.dispose()


def test_auth_signin_rate_limited_429(api):
    limiter.reset()
    limiter.enabled = True
    try:
        budget = int(SIGNIN_LIMIT.split("/")[0])  # e.g. "10/minute" -> 10
        statuses = []
        # Garbage sign-ins: each is a 401 until the per-IP budget runs out,
        # then the limiter answers 429 before the handler runs.
        for _ in range(budget + 3):
            r = api.post("/auth/google", json={"id_token": "garbage"})
            statuses.append(r.status_code)
        assert statuses.count(429) >= 1
        assert statuses[-1] == 429  # over budget stays limited
        assert all(s in (401, 503, 429) for s in statuses)
        # The limited response is the standard slowapi shape
        assert "Retry-After" in r.headers or "error" in r.text.lower() \
            or "rate limit" in r.text.lower()
    finally:
        limiter.enabled = False
        limiter.reset()


def test_each_fly_client_ip_spends_its_own_budget(api):
    """On Fly every request's TCP peer is Fly's proxy; keyed on that, one
    user's sign-ins would spend everyone's. Fly-Client-IP names the caller."""
    limiter.reset()
    limiter.enabled = True
    try:
        budget = int(SIGNIN_LIMIT.split("/")[0])
        first = {"Fly-Client-IP": "203.0.113.7"}
        second = {"Fly-Client-IP": "198.51.100.23"}
        for _ in range(budget):
            assert api.post("/auth/google", json={"id_token": "garbage"},
                            headers=first).status_code != 429
        assert api.post("/auth/google", json={"id_token": "garbage"},
                        headers=first).status_code == 429
        # Same proxy peer, different caller: a fresh bucket.
        assert api.post("/auth/google", json={"id_token": "garbage"},
                        headers=second).status_code != 429
        # And the first caller is still limited.
        assert api.post("/auth/google", json={"id_token": "garbage"},
                        headers=first).status_code == 429
    finally:
        limiter.enabled = False
        limiter.reset()


def test_client_key_reads_fly_client_ip_and_falls_back_to_the_peer():
    from starlette.requests import Request

    from app.rate_limit import client_key

    def request(header: str | None, peer: str = "10.0.0.1") -> Request:
        headers = [] if header is None else [(b"fly-client-ip", header.encode())]
        return Request({"type": "http", "method": "POST", "path": "/auth/apple",
                        "headers": headers, "client": (peer, 443)})

    assert client_key(request("203.0.113.7")) == "203.0.113.7"
    assert client_key(request(" 203.0.113.7 ")) == "203.0.113.7"
    # Off Fly, or a header that is not an address: the socket peer.
    assert client_key(request(None)) == "10.0.0.1"
    assert client_key(request("not-an-address")) == "10.0.0.1"
    # One device's IPv6 /64 is one caller, wherever in it the address falls.
    assert client_key(request("2001:db8:1:2::1")) == \
        client_key(request("2001:db8:1:2:ffff::9")) == "2001:db8:1:2::/64"
    assert client_key(request("2001:db8:1:3::1")) != \
        client_key(request("2001:db8:1:2::1"))
    # An IPv4 caller written as IPv6 is still that IPv4 caller.
    assert client_key(request("::ffff:203.0.113.7")) == "203.0.113.7"


def test_rate_limit_does_not_touch_normal_routes(api):
    limiter.reset()
    limiter.enabled = True
    try:
        # The root health route is public and undecorated — hammering it never
        # 429s (only the auth routes carry a limiter). /species used to serve
        # this role but now requires auth.
        for _ in range(15):
            assert api.get("/").status_code == 200
    finally:
        limiter.enabled = False
        limiter.reset()


# --- Checklist pins (Phase 9: iss checked, leeway <= 60 s) ---------------------


def test_jwt_issuer_and_leeway_match_plan():
    from app.services import tokens
    assert tokens.ISSUER == "plantadvocate"
    assert tokens.LEEWAY_SECONDS <= 60

    from app.services.oauth import apple, google
    assert apple.LEEWAY_SECONDS <= 60
    assert google.LEEWAY_SECONDS <= 60


def test_no_token_material_in_log_calls():
    """Source-level guard: logging statements in the auth surface must never
    interpolate token/secret variables. Complements the manual sweep."""
    import re
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "app"
    suspicious = re.compile(
        r"log(?:ger)?\.\w+\([^)]*"
        r"(access_token|refresh_token|token_hash|plaintext|client_secret"
        r"|jwt_secret|fernet|authorization_code|identity_token|id_token)",
        re.IGNORECASE,
    )
    offenders = []
    for py in root.rglob("*.py"):
        for i, line in enumerate(py.read_text(encoding="utf-8").splitlines(), 1):
            if suspicious.search(line):
                offenders.append(f"{py.name}:{i}: {line.strip()}")
    assert offenders == [], f"token material in log calls: {offenders}"
