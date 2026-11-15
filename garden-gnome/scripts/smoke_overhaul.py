"""End-to-end smoke run of the 1.2.0 land and season routes against real
public data, at a public landmark only (never a home address).

    cd garden-gnome && .venv/bin/python scripts/smoke_overhaul.py arboretum
    cd garden-gnome && .venv/bin/python scripts/smoke_overhaul.py zilker

It builds a temporary SQLite database at Alembic head, turns both feature
flags on, makes one test user, then drives the real routes through FastAPI's
TestClient: create a property at the landmark (fast step inline), run the
background step to completion, read the site profile, draw one zone box,
read zones, imagery, the seasonal plan and Home's vitals. It prints a
compact summary with timings. Nothing here runs in the automated tests.
"""
from __future__ import annotations

import os
import secrets
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

LANDMARKS = {
    "arboretum": ("United States National Arboretum", 38.9123, -76.9681),
    "zilker": ("Zilker Park, Austin", 30.2669, -97.7729),
}


def _setup_env(db_path: Path) -> str:
    url = f"sqlite:///{db_path.as_posix()}"
    os.environ["DATABASE_URL"] = url
    os.environ.setdefault("JWT_SECRET", secrets.token_hex(32))
    if "FERNET_KEY" not in os.environ:
        from cryptography.fernet import Fernet
        os.environ["FERNET_KEY"] = Fernet.generate_key().decode()
    os.environ["SITE_PROFILE_ENABLED"] = "true"
    os.environ["SEASON_PLAN_ENABLED"] = "true"
    return url


def _migrate(url: str) -> None:
    from alembic import command
    from alembic.config import Config
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")


class Clock:
    def __init__(self):
        self.rows: list[tuple[str, float]] = []

    def run(self, label, fn, *a, **kw):
        t = time.perf_counter()
        try:
            return fn(*a, **kw)
        finally:
            self.rows.append((label, time.perf_counter() - t))


def _sources(explained: dict) -> str:
    return "; ".join(s.get("name", "?") for s in explained.get("sources") or [])


def main(which: str) -> int:
    name, lat, lng = LANDMARKS[which]
    tmp = Path(tempfile.mkdtemp(prefix="smoke-overhaul-"))
    url = _setup_env(tmp / "smoke.db")
    clock = Clock()
    clock.run("migrate to head", _migrate, url)

    from fastapi.testclient import TestClient
    from sqlmodel import Session, create_engine

    from app.db.database import get_session
    from app.main import app
    from app.models.models import User
    from app.routers import properties as props_router
    from app.services import tokens
    from app.services.site import profile

    engine = create_engine(url, connect_args={"check_same_thread": False})

    def override():
        with Session(engine) as s:
            yield s

    app.dependency_overrides[get_session] = override
    profile.SESSION_FACTORY = lambda: Session(engine)
    props_router.queue_background = lambda background, pid: None  # run it below, timed

    with Session(engine) as s:
        user = User(email=f"smoke-{which}@example.com")
        s.add(user)
        s.commit()
        uid = user.id
    h = {"Authorization": f"Bearer {tokens.issue_access_token(uid)}"}
    client = TestClient(app)
    out: list[str] = []
    p = out.append

    p(f"# {name} ({lat}, {lng})")
    r = clock.run("POST /properties (fast step inline)", client.post, "/properties",
                  headers=h, json={"pin_lat": lat, "pin_lng": lng,
                                   "pin_source": "owner_pin",
                                   "lot_contents": ["trees_that_drop_leaves", "lawn",
                                                    "garden_beds"]})
    assert r.status_code == 201, r.text
    prop = r.json()
    pid = prop["id"]
    p(f"property {pid}: status after create {prop['profile_status']}")

    clock.run("background step", profile.build_background, pid)
    with Session(engine) as s:
        from app.models.models import Property
        st = s.get(Property, pid).profile_status
    p(f"status after background: fast={st.get('fast')} background={st.get('background')}")
    p(f"sources: {st.get('sources')}")
    if st.get("errors"):
        p(f"errors: {st.get('errors')}")

    sp = clock.run("GET site-profile", client.get, f"/properties/{pid}/site-profile",
                   headers=h).json()
    p("\n## Site profile")
    for v in sp["values"]:
        p(f"- {v['field']} [{v['confidence_label']}]: {v['display']}")
        p(f"    why: {v['reason']}")
        p(f"    sources: {_sources(v)}")
    for n in sp.get("notes") or []:
        p(f"- note: {n}")

    # One zone box: a bed about 20 m square, 15 m south-east of the pin.
    box = {"west": lng + 0.00012, "south": lat - 0.00030,
           "east": lng + 0.00035, "north": lat - 0.00012}
    r = clock.run("POST zone", client.post, f"/properties/{pid}/zones", headers=h,
                  json={"name": "Front bed", "vegetation_type": "garden_bed", "box": box})
    assert r.status_code == 201, r.text
    zone = r.json()
    clock.run("background step again (zone)", profile.build_background, pid)
    zones = clock.run("GET zones", client.get, f"/properties/{pid}/zones",
                      headers=h).json()
    p("\n## Zones")
    for z in zones:
        p(f"- zone {z['id']} {z['name']!r} whole_lot={z['is_whole_lot']} "
          f"type={z['vegetation_type']} source={z['boundary_source']} plants={z['plant_count']}")
        for v in z["values"]:
            p(f"    {v['field']} [{v['confidence_label']}]: {v['display']}")
    del zone

    p("\n## Imagery")
    r = clock.run("GET property imagery", client.get, f"/properties/{pid}/imagery", headers=h)
    if r.status_code == 200:
        im = r.json()
        p(f"- {im['tile_key']} {im['width']}x{im['height']} captured={im.get('captured')} "
          f"source={im['source'].get('name')}")
        jpg = clock.run("GET tile jpeg", client.get, im["image_path"], headers=h)
        p(f"- tile: HTTP {jpg.status_code}, {len(jpg.content)} bytes, "
          f"{jpg.headers.get('content-type')}")
    else:
        p(f"- HTTP {r.status_code}: {r.json().get('detail')}")

    plan = clock.run("GET seasonal-plan", client.get, f"/properties/{pid}/seasonal-plan",
                     headers=h).json()
    p(f"\n## Seasonal plan ({plan['season_label']})")
    fc = plan.get("forecast")
    if fc:
        p(f"forecast: {fc['provider_name']}, {len(fc['days'])} days, risks "
          f"{[d['frost_risk'] for d in fc['days']]}")
    for e in plan["events"]:
        p(f"- {e['type']} [{e['status']}] {e['window']['text']} "
          f"({len(e['tasks'])} tasks; {e['explained']['confidence_label']})")
    p(f"alerts: {[a['title'] for a in plan['alerts']]}")
    for n in plan.get("notes") or []:
        p(f"- note: {n}")

    v = clock.run("GET vitals", client.get, f"/vitals?property_id={pid}", headers=h).json()
    p("\n## Vitals")
    p(f"headline: {v['headline']}")
    for c in v["cards"]:
        p(f"- {c['key']} [{c['tone']}] {c['title']}: {c['value_text']} | {c['detail']}")
    p(f"this_week: {len(v['this_week'])} items; season_ahead: "
      f"{[e['type'] for e in v['season_ahead']]}")

    p("\n## Timings")
    for label, secs in clock.rows:
        p(f"- {label}: {secs:.2f} s")
    print("\n".join(out))

    from tests.explained_walker import problems
    bad = problems(sp) + problems(plan) + problems(v) + problems(zones)
    if bad:
        print("\nREASON/SOURCE PROBLEMS:", bad[:10])
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "arboretum"))
