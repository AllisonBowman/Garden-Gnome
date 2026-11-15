"""Recorded National Weather Service answers for the two public landmarks
(build spec section 2), replayed through httpx.MockTransport. Recorded on
2026-11-15 at the weather cell (the pin at two decimal places)."""
from __future__ import annotations

import json
from pathlib import Path

import httpx

HERE = Path(__file__).parent / "fixtures" / "season"
ARBORETUM = (38.9123, -76.9681)
ZILKER = (30.2669, -97.7729)
FILES = {"arboretum": "nws_arboretum.json", "zilker": "nws_zilker.json"}


def load(name: str) -> dict:
    return json.loads((HERE / FILES[name]).read_text())


def nws_transport(name: str, *, calls: list | None = None, fail: bool = False) -> httpx.MockTransport:
    doc = load(name)
    pp = doc["points"]["properties"]
    grid_path = f"/gridpoints/{pp['gridId']}/{pp['gridX']},{pp['gridY']}"

    def handler(request: httpx.Request) -> httpx.Response:
        if calls is not None:
            calls.append(str(request.url))
        if fail:
            return httpx.Response(503, json={"title": "down"})
        path = request.url.path
        if path.startswith("/points/"):
            return httpx.Response(200, json=doc["points"])
        if path == grid_path:
            return httpx.Response(200, json=doc["gridpoint"])
        if path == grid_path + "/forecast":
            return httpx.Response(200, json=doc["forecast"])
        return httpx.Response(404, json={"title": "not found"})

    return httpx.MockTransport(handler)
