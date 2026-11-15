"""The single outbound client for public geodata (build spec section 2).

Soil, elevation, land cover, canopy and imagery services only ever receive
the grid-snapped block (PLAN.md D7). Every such request goes through
`OutboundClient`, which:

- sends a generic User-Agent that names no person, app account or address;
- uses one timeout and a bounded number of retries (connection errors,
  timeouts, 429 and 5xx answers), with a short backoff;
- lets at most `PER_HOST_LIMIT` requests run at once against one host,
  across every client in the process;
- refuses to send, before anything leaves the machine, any request whose
  path, query or body carries a coordinate that is not on the snap grid
  (`guard`); and
- refuses to send anything while both feature flags are off.

**Declaring coordinates.** A source names the parameters that carry a
place, with a `Coord` kind, so the guard checks each number on the right
axis: `coords={"geometry": Coord.BBOX, "inSR": ...}`. The names apply to
query parameters, form fields and top-level JSON body keys alike. Every
other value in the request is still scanned: any number with three or more
decimal places between -180 and 180 must lie on a grid line of one axis or
the request is refused. Input spatial references (`inSR`, `bboxSR`,
`geometrySR`, `srs`, `crs`, `srsName`) must be geographic degrees (4326,
4269 or CRS84): a projected system would let an exact location through as
metres. Output systems (`imageSR`, `outSR`) are not restricted.

Weather calls (B3) send the pin rounded to two decimal places, about a
kilometre, as `services/weather.py` already does; numbers with two or fewer
decimal places pass the scan, and `Coord.WEATHER_POINT` declares such a pair
explicitly.

Tests never reach the network: `use_transport` swaps the transport every new
client gets (tests/conftest.py installs one that refuses), or pass
`transport=httpx.MockTransport(...)` to the constructor.
"""
from __future__ import annotations

import json as jsonlib
import logging
import re
import threading
import time
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Any, Callable, Iterable, Mapping, Optional
from urllib.parse import parse_qsl, unquote, urlsplit

import httpx

from app.config import get_settings
from app.services.site import grid
from app.services.site.types import SourceUnavailable

logger = logging.getLogger("plantadvocate.site.http")

#: Generic and descriptive; holds no personal detail (build spec section 2).
USER_AGENT = "site-profile-research/0.1 (public geodata reader)"
DEFAULT_TIMEOUT = httpx.Timeout(20.0, connect=10.0)
#: For the federal image services (aerial imagery, elevation), whose cold
#: requests took 12 to 61 s on 2026-11-15. Used by the background step and
#: the imagery routes only.
SLOW_TIMEOUT = httpx.Timeout(60.0, connect=10.0)
#: For anything a request waits on inline (the fast profile step when a
#: property is created, the forecast behind Home). The app gives a call 15 s,
#: so an outside service gets one short attempt; what it could not answer is
#: tried again by the background step with the long timeout.
INLINE_TIMEOUT = httpx.Timeout(5.0, connect=3.0)
#: For the imagery routes: one attempt that ends before the app's own 60 s
#: limit for the aerial image, so the person gets an answer either way.
IMAGERY_TIMEOUT = httpx.Timeout(45.0, connect=10.0)
MAX_RETRIES = 2                    # so at most 3 attempts in all
BACKOFF_SECONDS = 0.5              # 0.5 s, then 1 s
RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})
PER_HOST_LIMIT = 2

_INPUT_SR_PARAMS = frozenset(
    {"insr", "bboxsr", "geometrysr", "srs", "crs", "srsname"})
_GEOGRAPHIC_SR = frozenset(
    {"4326", "4269", "epsg:4326", "epsg:4269", "crs84", "ogc:crs84",
     "urn:ogc:def:crs:ogc:1.3:crs84", "urn:ogc:def:crs:epsg::4326"})
_NUMBER = re.compile(r"-?\d+(?:\.\d+)?")
_FRACTIONAL = re.compile(r"-?\d+\.(\d+)")
_WKT = re.compile(
    r"\b(?:MULTI)?(?:POINT|LINESTRING|POLYGON)\s*(?:Z\s*)?\(+[-\d.,\s()eE+]+\)+",
    re.IGNORECASE)


class OutboundRefused(ValueError):
    """The guard would not send this request. A programming error in a
    source, never an outage: it is not a SourceUnavailable."""


class GeodataDisabled(OutboundRefused):
    """Both feature flags are off, so nothing may be sent."""


class Coord(str, Enum):
    """How a declared parameter names a place. Longitude first unless the
    name says otherwise."""
    BBOX = "bbox"                  # "west,south,east,north", or an Esri envelope
    POINT_LNGLAT = "point_lnglat"  # "lng,lat", or an Esri point {"x","y"}
    POINT_LATLNG = "point_latlng"  # "lat,lng"
    LAT = "lat"
    LNG = "lng"
    WKT = "wkt"                    # WKT geometry, alone or inside SQL text
    GEOJSON = "geojson"            # a GeoJSON geometry (dict or JSON text)
    WEATHER_POINT = "weather_point"  # "lat,lng" at two decimal places at most
    SPATIAL_REFERENCE = "spatial_reference"  # must be geographic degrees


# --- the guard -------------------------------------------------------------------

def _decimals(text: str) -> int:
    m = _FRACTIONAL.fullmatch(text.strip())
    return len(m.group(1).rstrip("0")) if m else 0


def _num_text(value: Any) -> str:
    if isinstance(value, bool):
        return str(int(value))
    if isinstance(value, float):
        return repr(value)
    return str(value)


def _numbers(value: Any) -> list[str]:
    """Every number in a value, as text, walking JSON structures."""
    if value is None:
        return []
    if isinstance(value, bool):
        return []
    if isinstance(value, (int, float)):
        return [_num_text(value)]
    if isinstance(value, Mapping):
        return [n for v in value.values() for n in _numbers(v)]
    if isinstance(value, (list, tuple)):
        return [n for v in value for n in _numbers(v)]
    return _NUMBER.findall(str(value))


def _as_float(text: str, where: str) -> float:
    try:
        return float(Decimal(text))
    except (InvalidOperation, ValueError):
        raise OutboundRefused(f"{where}: {text!r} is not a number") from None


def _need_lat(text: str, where: str) -> None:
    if not grid.lat_on_grid(_as_float(text, where)):
        raise OutboundRefused(
            f"{where}: latitude {text} is not on the snap grid; send the block")


def _need_lng(text: str, where: str) -> None:
    if not grid.lng_on_grid(_as_float(text, where)):
        raise OutboundRefused(
            f"{where}: longitude {text} is not on the snap grid; send the block")


def _pairs_lnglat(nums: list[str], where: str) -> None:
    if len(nums) % 2:
        raise OutboundRefused(f"{where}: coordinates do not come in pairs")
    for i in range(0, len(nums), 2):
        _need_lng(nums[i], where)
        _need_lat(nums[i + 1], where)


def _parse_maybe_json(value: Any) -> Any:
    if isinstance(value, str) and value.strip()[:1] in "{[":
        try:
            return jsonlib.loads(value)
        except ValueError:
            return value
    return value


def _check_declared(name: str, kind: Coord, value: Any) -> None:
    where = f"parameter {name!r}"
    if kind is Coord.SPATIAL_REFERENCE:
        _check_sr(name, value, declared=True)
        return
    parsed = _parse_maybe_json(value)
    if kind is Coord.BBOX:
        if isinstance(parsed, Mapping) and "xmin" in parsed:
            _check_esri_sr(parsed, where)
            nums = [_num_text(parsed[k]) for k in ("xmin", "ymin", "xmax", "ymax")]
        else:
            nums = _numbers(parsed)
        if len(nums) != 4:
            raise OutboundRefused(f"{where}: a box has four numbers")
        _need_lng(nums[0], where); _need_lat(nums[1], where)
        _need_lng(nums[2], where); _need_lat(nums[3], where)
    elif kind is Coord.POINT_LNGLAT:
        if isinstance(parsed, Mapping) and "x" in parsed:
            _check_esri_sr(parsed, where)
            nums = [_num_text(parsed["x"]), _num_text(parsed["y"])]
        else:
            nums = _numbers(parsed)
        if len(nums) != 2:
            raise OutboundRefused(f"{where}: a point has two numbers")
        _need_lng(nums[0], where); _need_lat(nums[1], where)
    elif kind is Coord.POINT_LATLNG:
        nums = _numbers(parsed)
        if len(nums) != 2:
            raise OutboundRefused(f"{where}: a point has two numbers")
        _need_lat(nums[0], where); _need_lng(nums[1], where)
    elif kind is Coord.LAT:
        for n in _numbers(parsed):
            _need_lat(n, where)
    elif kind is Coord.LNG:
        for n in _numbers(parsed):
            _need_lng(n, where)
    elif kind is Coord.WKT:
        text = str(value)
        geoms = _WKT.findall(text)
        for g in geoms:
            _pairs_lnglat(_NUMBER.findall(g), where)
        # Whatever is outside the geometries is still scanned.
        _scan(_WKT.sub(" ", text), where)
    elif kind is Coord.GEOJSON:
        if not isinstance(parsed, Mapping):
            raise OutboundRefused(f"{where}: not a GeoJSON object")
        coords = parsed.get("coordinates")
        if coords is None and "bbox" not in parsed:
            raise OutboundRefused(f"{where}: GeoJSON without coordinates")
        _pairs_lnglat(_numbers(coords), where)
        if "bbox" in parsed:
            _check_declared(name, Coord.BBOX, parsed["bbox"])
    elif kind is Coord.WEATHER_POINT:
        nums = _numbers(parsed)
        if len(nums) != 2:
            raise OutboundRefused(f"{where}: a point has two numbers")
        for n in nums:
            if _decimals(n) > 2:
                raise OutboundRefused(
                    f"{where}: {n} is finer than two decimal places (about "
                    "a kilometre), the most a weather service is told")
    else:  # pragma: no cover - every kind is handled above
        raise OutboundRefused(f"{where}: unknown coordinate kind {kind!r}")


def _check_esri_sr(obj: Mapping, where: str) -> None:
    sr = obj.get("spatialReference")
    if isinstance(sr, Mapping):
        wkid = sr.get("latestWkid", sr.get("wkid"))
        if wkid is not None and str(wkid) not in _GEOGRAPHIC_SR:
            raise OutboundRefused(
                f"{where}: spatial reference {wkid} is not geographic degrees")


def _check_sr(name: str, value: Any, *, declared: bool) -> None:
    parsed = _parse_maybe_json(value)
    if isinstance(parsed, Mapping):
        wkid = parsed.get("latestWkid", parsed.get("wkid"))
        text = "" if wkid is None else str(wkid)
    else:
        text = str(parsed).strip().lower()
    if text and text not in _GEOGRAPHIC_SR:
        raise OutboundRefused(
            f"parameter {name!r}: input spatial reference {value!r} is not "
            "geographic degrees, so the guard could not check it; send "
            "coordinates in degrees (4326)")


def _scan(value: Any, where: str) -> None:
    """Undeclared values: any number precise enough to place a house must
    still sit on a grid line."""
    for text in _numbers(value):
        if _decimals(text) < 3:
            continue
        v = _as_float(text, where)
        if abs(v) <= 180 and not grid.on_grid(v):
            raise OutboundRefused(
                f"{where}: {text} looks like a coordinate that is not on the "
                "snap grid; declare it with coords= and send the block")


def guard(url: str, *, params: Optional[Mapping[str, Any]] = None,
          data: Optional[Mapping[str, Any]] = None, json: Any = None,
          content: Optional[bytes | str] = None,
          coords: Optional[Mapping[str, Coord]] = None,
          not_coordinates: Iterable[str] = ()) -> None:
    """Raise OutboundRefused unless every place in the request is on the
    snap grid. Pure; sends nothing. `not_coordinates` names parameters whose
    numbers are known not to be places (an image size in degrees of nothing,
    a version string)."""
    declared = {k.lower(): v for k, v in (coords or {}).items()}
    skip = {k.lower() for k in not_coordinates}

    parts = urlsplit(url)
    _scan(unquote(parts.path), "the URL path")

    fields: list[tuple[str, Any]] = list(parse_qsl(parts.query, keep_blank_values=True))
    for source in (params, data):
        if source:
            fields.extend(source.items())
    if isinstance(json, Mapping):
        fields.extend(json.items())
    elif json is not None:
        _scan(json, "the JSON body")
    if content is not None:
        text = content.decode("utf-8", "replace") if isinstance(content, bytes) else content
        _scan(text, "the request body")

    for name, value in fields:
        key = str(name).lower()
        if key in declared:
            _check_declared(name, declared[key], value)
        elif key in _INPUT_SR_PARAMS:
            _check_sr(name, value, declared=False)
        elif key in skip:
            continue
        else:
            _scan(value, f"parameter {name!r}")


# --- transport and limits ----------------------------------------------------------

def _refuse_without_transport() -> Optional[httpx.BaseTransport]:
    return None  # None means httpx's real transport


_transport_factory: Callable[[], Optional[httpx.BaseTransport]] = _refuse_without_transport
_host_locks: dict[str, threading.BoundedSemaphore] = {}
_host_locks_guard = threading.Lock()
_sent_lock = threading.Lock()
_sent = 0


def use_transport(factory: Callable[[], Optional[httpx.BaseTransport]]):
    """Make every new OutboundClient use `factory()` as its transport.
    Returns the previous factory so a test can put it back."""
    global _transport_factory
    previous = _transport_factory
    _transport_factory = factory
    return previous


def requests_sent() -> int:
    """How many requests have been handed to a transport in this process."""
    return _sent


def _count() -> None:
    global _sent
    with _sent_lock:
        _sent += 1


def _host_lock(host: str) -> threading.BoundedSemaphore:
    with _host_locks_guard:
        lock = _host_locks.get(host)
        if lock is None:
            lock = _host_locks[host] = threading.BoundedSemaphore(PER_HOST_LIMIT)
        return lock


def flags_allow(flag: str) -> bool:
    s = get_settings()
    if flag == "site_profile":
        return bool(s.site_profile_enabled)
    if flag == "season_plan":
        return bool(s.season_plan_enabled)
    raise ValueError(f"unknown flag {flag!r}")


class OutboundClient:
    """The one way out to public geodata and weather services.

    `flag` is the feature flag this client works for ("site_profile" for
    geodata sources, "season_plan" for the seasonal engine); while it is off,
    every request raises GeodataDisabled before anything is sent."""

    def __init__(self, *, flag: str = "site_profile",
                 transport: Optional[httpx.BaseTransport] = None,
                 timeout: httpx.Timeout = DEFAULT_TIMEOUT,
                 max_retries: int = MAX_RETRIES,
                 sleep: Callable[[float], None] = time.sleep):
        flags_allow(flag)  # validates the name
        self.flag = flag
        self.max_retries = max_retries
        self._sleep = sleep
        self._client = httpx.Client(
            transport=transport if transport is not None else _transport_factory(),
            timeout=timeout,
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
        )

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def close(self) -> None:
        self._client.close()

    def get(self, url: str, **kwargs) -> httpx.Response:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> httpx.Response:
        return self.request("POST", url, **kwargs)

    def request(self, method: str, url: str, *,
                params: Optional[Mapping[str, Any]] = None,
                data: Optional[Mapping[str, Any]] = None,
                json: Any = None,
                content: Optional[bytes | str] = None,
                headers: Optional[Mapping[str, str]] = None,
                coords: Optional[Mapping[str, Coord]] = None,
                not_coordinates: Iterable[str] = (),
                source_key: str = "outbound",
                raise_for_status: bool = True) -> httpx.Response:
        """Send one request through the guard, the host limit and retries.

        Raises OutboundRefused (or GeodataDisabled) before sending anything,
        and SourceUnavailable(source_key) when the service cannot be reached
        or, with `raise_for_status`, answers with an error status after the
        retries. A 4xx other than 429 is not retried."""
        if not flags_allow(self.flag):
            raise GeodataDisabled(
                f"{self.flag} is off: no outbound request may be made")
        guard(url, params=params, data=data, json=json, content=content,
              coords=coords, not_coordinates=not_coordinates)
        host = urlsplit(url).hostname or ""
        if headers and any(k.lower() == "user-agent" for k in headers):
            raise OutboundRefused("the User-Agent is fixed; do not set it per request")

        last_error: Optional[str] = None
        for attempt in range(self.max_retries + 1):
            if attempt:
                self._sleep(BACKOFF_SECONDS * (2 ** (attempt - 1)))
            try:
                with _host_lock(host):
                    _count()
                    response = self._client.request(
                        method, url, params=params, data=data, json=json,
                        content=content, headers=headers)
            except httpx.TransportError as exc:
                last_error = f"{type(exc).__name__}: {exc}"
                logger.info("%s: %s (attempt %d)", source_key, last_error, attempt + 1)
                continue
            if response.status_code in RETRY_STATUSES and attempt < self.max_retries:
                last_error = f"HTTP {response.status_code}"
                continue
            if raise_for_status and response.status_code >= 400:
                raise SourceUnavailable(source_key, f"HTTP {response.status_code}")
            return response
        raise SourceUnavailable(source_key, last_error or "no answer")


def get_client(flag: str = "site_profile") -> OutboundClient:
    """A new client for one build step. Close it when the step ends."""
    return OutboundClient(flag=flag)
