"""Properties, zones, the site profile, imagery, map layers, the seasonal plan
and Home.

Every route in build spec section 4. All of them need a signed-in user and
see only that user's rows: another person's property or zone is a 404, never
a 403, as everywhere else in this API. Each route answers 404 while its
feature flag is off (PLAN.md D5), before it reads anything:
SITE_PROFILE_ENABLED for properties, zones, the site profile and imagery;
SEASON_PLAN_ENABLED for the seasonal plan and /vitals.

A zone is a growing-area row with `property_id` set (D1). Creating a property
creates its whole-lot zone, outdoors and open to the sky, with the default
footprint: the north-aligned square of about 8,500 square feet around the pin.

The routes do the bookkeeping (ownership, rows, statuses) and leave the
science to the service entry points they call: `profile.build_fast`,
`profile.build_background`, `profile.site_profile`, `plan.seasonal_plan` and
`vitals.vitals`. The background step starts through `queue_background`, the
one function tests swap to run it inline or not at all.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any, Callable, Optional

from fastapi import (
    APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, Response,
)
from sqlmodel import Session, select

from app.config import get_settings
from app.db.database import get_session
from app.deps import get_current_user
from app.models.models import (
    BoundarySource, GrowingArea, GrowingAreaType, OverrideMethod, Plant,
    Property, SeasonEventState, Shelter, SiteOverride, SiteReading,
    StewardshipRecord, SunExposure, TempExposure, User,
)
from app.models.schemas import (
    Box, ImageryOut, MapLayersOut, OverrideIn, PropertyCreate, PropertyOut,
    PropertyPatch, RefreshOut, SeasonEvent, SeasonEventStateIn,
    SeasonalPlanOut, SiteProfileOut, VitalsOut, ZoneCreate, ZoneOut,
    ZonePatch,
)
from app.rate_limit import SITE_BUILD_LIMIT, limiter
from app.services import coverage
from app.services import vitals as vitals_service
from app.services.season import plan as plan_service
from app.services.site import grid, tiles
from app.services.site import http as site_http
from app.services.site import layers as layer_service
from app.services.site import profile as profile_service

logger = logging.getLogger("plantadvocate.properties")

#: What a property is called when the owner gives no name.
DEFAULT_PROPERTY_NAME = "My land"
#: What the whole-lot zone is called.
WHOLE_LOT_NAME = "Whole lot"
#: A zone's name when the owner gives none, from what grows there.
ZONE_NAMES = {
    "tree": "Trees", "shrub": "Shrubs", "grass": "Lawn",
    "garden_bed": "Garden bed", "bare_hardscape": "Paving",
}
#: The largest box an owner may draw, in degrees on a side (about 1 km):
#: larger than any block of aerial imagery the app shows.
MAX_BOX_DEG = 0.01
#: Sun corrections, as the old growing-area column understands them.
SUN_TO_EXPOSURE = {
    "full_sun": SunExposure.full_sun,
    "part_shade": SunExposure.partial_sun,
    "shade": SunExposure.shade,
}
_TILE_KEY = re.compile(r"^[A-Za-z0-9_\-]{1,120}$")
#: Properties one account may hold, and zones one property may hold. Each
#: property costs about 20 requests to the federal services and half a
#: megabyte of cache; a yard rarely needs more than a few dozen beds.
MAX_PROPERTIES_PER_ACCOUNT = 5
MAX_ZONES_PER_PROPERTY = 40


# --- flags ------------------------------------------------------------------------

def _flag(attr: str) -> Callable[[], None]:
    def check() -> None:
        if not getattr(get_settings(), attr):
            raise HTTPException(status_code=404, detail="Not Found")
    check.__name__ = f"require_{attr}"
    return check


#: Route dependencies: 404 while the flag is off.
require_site_profile = _flag("site_profile_enabled")
require_season_plan = _flag("season_plan_enabled")


# --- the background step ----------------------------------------------------------

def _run_background(property_id: int) -> None:
    """Runs after the response. Never raises: a failure is the profile's
    "failed" status, written by build_background, not a server error."""
    if not site_http.flags_allow("site_profile"):
        return
    try:
        profile_service.build_background(property_id)
    except Exception:  # noqa: BLE001 -- the response has already gone
        logger.exception("background site profile step failed for property %s",
                         property_id)


def queue_background(background: BackgroundTasks, property_id: int) -> None:
    """Start the background step for one property. The one place it is
    started; tests replace this function to run it inline or not at all."""
    background.add_task(_run_background, property_id)


# --- helpers ----------------------------------------------------------------------

def _owned_property(property_id: int, user: User, session: Session) -> Property:
    prop = session.get(Property, property_id)
    if prop is None or prop.user_id != user.id:
        raise HTTPException(status_code=404, detail="Property not found")
    return prop


def _zones(session: Session, prop: Property) -> list[GrowingArea]:
    return list(session.exec(
        select(GrowingArea)
        .where(GrowingArea.property_id == prop.id)
        .where(GrowingArea.user_id == prop.user_id)
        .order_by(GrowingArea.is_whole_lot.desc(), GrowingArea.id.asc())
    ).all())


def _whole_lot(session: Session, prop: Property) -> Optional[GrowingArea]:
    return session.exec(
        select(GrowingArea)
        .where(GrowingArea.property_id == prop.id)
        .where(GrowingArea.user_id == prop.user_id)
        .where(GrowingArea.is_whole_lot == True)  # noqa: E712
        .order_by(GrowingArea.id.asc())
    ).first()


def _owned_zone(prop: Property, zone_id: int, session: Session) -> GrowingArea:
    zone = session.get(GrowingArea, zone_id)
    if (zone is None or zone.property_id != prop.id
            or zone.user_id != prop.user_id):
        raise HTTPException(status_code=404, detail="Zone not found")
    return zone


def _plant_count(session: Session, area_id: int) -> int:
    return len(session.exec(
        select(Plant).where(Plant.growing_area_id == area_id)).all())


def _set_status(prop: Property, **steps: str) -> None:
    status = dict(prop.profile_status or {"fast": "pending", "background": "pending"})
    status.update(steps)
    prop.profile_status = status  # a new dict, so the JSON column is marked dirty


def _mark_rebuild(prop: Property) -> None:
    """Both steps are to run again. A background step running right now is
    left as it is and runs once more when it ends, so two runs never go to
    the public services side by side."""
    if profile_service.request_rerun(prop.id):
        _set_status(prop, fast="pending")
    else:
        _set_status(prop, fast="pending", background="pending")


def property_out(session: Session, prop: Property) -> PropertyOut:
    """The Property shape for one row."""
    whole = _whole_lot(session, prop)
    return PropertyOut(
        id=prop.id, uuid=prop.uuid, name=prop.name,
        pin_lat=prop.pin_lat, pin_lng=prop.pin_lng,
        pin_source=prop.pin_source.value if hasattr(prop.pin_source, "value")
        else prop.pin_source,
        city=prop.city, region=prop.region, country=prop.country,
        timezone=prop.timezone,
        lot_contents=list(prop.lot_contents or []),
        frost_bias=prop.frost_bias.value if hasattr(prop.frost_bias, "value")
        else prop.frost_bias,
        whole_lot_zone_id=whole.id if whole else None,
        profile_status=profile_service.profile_status(prop),
        created_at=prop.created_at,
    )


def _zone_out(session: Session, zone: GrowingArea,
              profile: Optional[SiteProfileOut]) -> ZoneOut:
    box = grid.polygon_box(zone.boundary_geojson)
    values = []
    if profile is not None:
        for z in profile.zones:
            if z.zone_id == zone.id:
                values = z.values
    enum_value = lambda v: v.value if hasattr(v, "value") else v  # noqa: E731
    return ZoneOut(
        id=zone.id, growing_area_id=zone.id, property_id=zone.property_id,
        name=zone.name,
        vegetation_type=enum_value(zone.vegetation_type),
        is_whole_lot=bool(zone.is_whole_lot),
        box=Box(**box) if box else None,
        boundary_source=enum_value(zone.boundary_source) or "default",
        leaf_habit=enum_value(zone.leaf_habit),
        plant_count=_plant_count(session, zone.id),
        values=values,
    )


def _copy_place(zone: GrowingArea, prop: Property) -> None:
    """A zone carries a server-written copy of the property's pin and place,
    so the old weather and candidate routes work for it unchanged."""
    zone.lat = prop.pin_lat
    zone.lng = prop.pin_lng
    zone.city = prop.city or ""
    zone.region = prop.region or ""
    zone.country = prop.country or ""


def _new_zone(prop: Property, *, name: str, is_whole_lot: bool,
              boundary: dict, boundary_source: BoundarySource,
              vegetation_type: Optional[str] = None,
              leaf_habit: Optional[str] = None) -> GrowingArea:
    """Every zone is created outdoors and open to the sky (PLAN.md
    section 5): the model's own defaults are a roofed indoor room. Surface
    stays null, because a defaulted surface would be an invented fact."""
    zone = GrowingArea(
        name=name, type=GrowingAreaType.home, user_id=prop.user_id,
        temp_exposure=TempExposure.outdoor, shelter=Shelter.exposed,
        surface=None, property_id=prop.id, is_whole_lot=is_whole_lot,
        boundary_geojson=boundary, boundary_source=boundary_source,
        vegetation_type=vegetation_type, leaf_habit=leaf_habit,
    )
    _copy_place(zone, prop)
    return zone


def _check_box(box: Box) -> dict:
    if box.east - box.west > MAX_BOX_DEG or box.north - box.south > MAX_BOX_DEG:
        raise HTTPException(
            status_code=422,
            detail="That box is larger than the aerial image. Draw it over one bed or area.")
    return grid.box_polygon(box.west, box.south, box.east, box.north)


def _dedupe(values: Optional[list[str]]) -> Optional[list[str]]:
    if values is None:
        return None
    seen: list[str] = []
    for v in values:
        if v not in seen:
            seen.append(v)
    return seen


def _run_fast(session: Session, prop: Property) -> None:
    """The fast step, inline. A failure marks the step failed and never
    fails the request: the property exists either way."""
    try:
        profile_service.build_fast(session, prop)
        session.commit()
    except Exception:  # noqa: BLE001
        session.rollback()
        logger.exception("fast site profile step failed for property %s", prop.id)
        prop = session.get(Property, prop.id)
        _set_status(prop, fast="failed")
        session.add(prop)
        session.commit()


def _delete_site_rows(session: Session, property_id: int,
                      zone_id: Optional[int] = None) -> None:
    """Readings, corrections and event states for a property, or for one of
    its zones when `zone_id` is given."""
    for model in (SiteReading, SiteOverride, SeasonEventState):
        query = select(model).where(model.property_id == property_id)
        if zone_id is not None:
            query = query.where(model.zone_id == zone_id)
        for row in session.exec(query).all():
            session.delete(row)


def delete_properties_of(session: Session, user_id: str) -> list[int]:
    """Account deletion: every property of a user and its site rows. Zones
    are growing areas and go with the user's growing areas. Returns the
    property ids removed. Flushes; the caller commits."""
    props = session.exec(select(Property).where(Property.user_id == user_id)).all()
    ids = [p.id for p in props]
    for pid in ids:
        _delete_site_rows(session, pid)
    session.flush()
    if ids:
        tiles.prune_unused(session, excluding_property_ids=ids,
                           keep_recent_imagery=False)
    for prop in props:
        session.delete(prop)
    session.flush()
    return ids


# --- properties -------------------------------------------------------------------

router = APIRouter(prefix="/properties", tags=["properties"])


@router.get("", response_model=list[PropertyOut],
            dependencies=[Depends(require_site_profile)])
def list_properties(user: User = Depends(get_current_user),
                    session: Session = Depends(get_session)):
    props = session.exec(
        select(Property).where(Property.user_id == user.id)
        .order_by(Property.id.asc())).all()
    return [property_out(session, p) for p in props]


@router.post("", response_model=PropertyOut, status_code=201,
             dependencies=[Depends(require_site_profile)])
@limiter.limit(SITE_BUILD_LIMIT)
def create_property(request: Request, payload: PropertyCreate,
                    background: BackgroundTasks,
                    user: User = Depends(get_current_user),
                    session: Session = Depends(get_session)):
    """Creates the property and its whole-lot zone, runs the fast step
    inline and queues the background step. No address is accepted or kept."""
    held = len(session.exec(select(Property.id).where(Property.user_id == user.id)).all())
    if held >= MAX_PROPERTIES_PER_ACCOUNT:
        raise HTTPException(
            status_code=409,
            detail=f"An account can hold {MAX_PROPERTIES_PER_ACCOUNT} properties. "
                   "Delete one to add another.")
    tiles.check_volume()
    prop = Property(
        user_id=user.id,
        name=(payload.name or "").strip() or DEFAULT_PROPERTY_NAME,
        pin_lat=payload.pin_lat, pin_lng=payload.pin_lng,
        pin_source=payload.pin_source,
        lot_contents=_dedupe(payload.lot_contents),
        profile_status={"fast": "pending", "background": "pending"},
    )
    session.add(prop)
    session.flush()
    session.add(_new_zone(
        prop, name=WHOLE_LOT_NAME, is_whole_lot=True,
        boundary=grid.default_footprint(prop.pin_lat, prop.pin_lng),
        boundary_source=BoundarySource.default))
    session.commit()
    session.refresh(prop)

    _run_fast(session, prop)
    queue_background(background, prop.id)
    session.refresh(prop)
    return property_out(session, prop)


@router.get("/{property_id}", response_model=PropertyOut,
            dependencies=[Depends(require_site_profile)])
def get_property(property_id: int, user: User = Depends(get_current_user),
                 session: Session = Depends(get_session)):
    return property_out(session, _owned_property(property_id, user, session))


@router.patch("/{property_id}", response_model=PropertyOut,
              dependencies=[Depends(require_site_profile)])
def patch_property(property_id: int, payload: PropertyPatch,
                   background: BackgroundTasks,
                   user: User = Depends(get_current_user),
                   session: Session = Depends(get_session)):
    """A moved pin moves every zone's copy of it and the default footprint,
    and rebuilds the profile. `frost_bias: null` clears it."""
    prop = _owned_property(property_id, user, session)
    changes = payload.model_dump(exclude_unset=True)
    if ("pin_lat" in changes) != ("pin_lng" in changes):
        raise HTTPException(status_code=422,
                            detail="Send pin_lat and pin_lng together.")
    if changes.get("pin_lat", 0) is None or changes.get("pin_lng", 0) is None:
        raise HTTPException(status_code=422, detail="A pin cannot be removed.")
    moved = "pin_lat" in changes and (
        changes["pin_lat"] != prop.pin_lat or changes["pin_lng"] != prop.pin_lng)

    if "name" in changes:
        prop.name = (changes["name"] or "").strip() or DEFAULT_PROPERTY_NAME
    if "lot_contents" in changes:
        prop.lot_contents = _dedupe(changes["lot_contents"])
    if "frost_bias" in changes:
        prop.frost_bias = changes["frost_bias"]
    if moved:
        prop.pin_lat, prop.pin_lng = changes["pin_lat"], changes["pin_lng"]
        # The place came from the Weather Service lookup for the old pin; the
        # seasonal plan fills it again for the new one.
        prop.city = prop.region = prop.country = prop.timezone = None
        _mark_rebuild(prop)
        for zone in _zones(session, prop):
            _copy_place(zone, prop)
            if zone.is_whole_lot and zone.boundary_source in (
                    None, BoundarySource.default, "default"):
                zone.boundary_geojson = grid.default_footprint(
                    prop.pin_lat, prop.pin_lng)
            session.add(zone)
    session.add(prop)
    session.commit()
    session.refresh(prop)
    if moved:
        _run_fast(session, prop)
        queue_background(background, prop.id)
        session.refresh(prop)
    return property_out(session, prop)


@router.delete("/{property_id}", status_code=204,
               dependencies=[Depends(require_site_profile)])
def delete_property(property_id: int, user: User = Depends(get_current_user),
                    session: Session = Depends(get_session)):
    """Zones holding plants (or plant history) become plain growing areas,
    kept outdoors where they are; empty zones are removed."""
    prop = _owned_property(property_id, user, session)
    for zone in _zones(session, prop):
        keeps_history = session.exec(
            select(StewardshipRecord)
            .where(StewardshipRecord.growing_area_id == zone.id)).first()
        if _plant_count(session, zone.id) or keeps_history is not None:
            zone.property_id = None
            zone.is_whole_lot = False
            zone.boundary_geojson = None
            zone.boundary_source = None
            session.add(zone)
        else:
            session.delete(zone)
    _delete_site_rows(session, prop.id)
    session.flush()
    tiles.prune_unused(session, excluding_property_ids=[prop.id])
    session.delete(prop)
    session.commit()
    return Response(status_code=204)


# --- site profile and corrections -------------------------------------------------

@router.get("/{property_id}/site-profile", response_model=SiteProfileOut,
            dependencies=[Depends(require_site_profile)])
def get_site_profile(property_id: int, user: User = Depends(get_current_user),
                     session: Session = Depends(get_session)):
    prop = _owned_property(property_id, user, session)
    return profile_service.site_profile(session, prop)


@router.post("/{property_id}/site-profile/refresh", response_model=RefreshOut,
             status_code=202, dependencies=[Depends(require_site_profile)])
@limiter.limit(SITE_BUILD_LIMIT)
def refresh_site_profile(request: Request, property_id: int, background: BackgroundTasks,
                         user: User = Depends(get_current_user),
                         session: Session = Depends(get_session)):
    """Runs the fast step again inline and queues the background step.
    Owner corrections are never touched by a refresh."""
    prop = _owned_property(property_id, user, session)
    _mark_rebuild(prop)
    session.add(prop)
    session.commit()
    session.refresh(prop)
    _run_fast(session, prop)
    queue_background(background, prop.id)
    return RefreshOut(status="queued")


def _override_zone(session: Session, prop: Property,
                   zone_id: Optional[int]) -> Optional[GrowingArea]:
    return _owned_zone(prop, zone_id, session) if zone_id is not None else None


def _active_overrides(session: Session, prop: Property, zone_id: Optional[int],
                      field: str) -> list[SiteOverride]:
    query = (select(SiteOverride)
             .where(SiteOverride.property_id == prop.id)
             .where(SiteOverride.field == field)
             .where(SiteOverride.retracted_at == None))  # noqa: E711
    query = query.where(SiteOverride.zone_id == zone_id) if zone_id is not None \
        else query.where(SiteOverride.zone_id == None)  # noqa: E711
    return list(session.exec(query).all())


def _apply_sun(session: Session, prop: Property, zone: Optional[GrowingArea],
               value: Any) -> None:
    """A sun correction also tells the growing-area row, so the fit engine
    and the 1.1.x client see the owner's answer (`sun_source = owner`)."""
    target = zone or _whole_lot(session, prop)
    if target is None:
        return
    if value is None:
        target.sun_source = None
    elif value in SUN_TO_EXPOSURE:
        target.sun_exposure = SUN_TO_EXPOSURE[value]
        target.sun_source = "owner"
    session.add(target)


def record_override(session: Session, prop: Property, zone: Optional[GrowingArea],
                    field: str, value: Any, method: OverrideMethod) -> SiteOverride:
    """Retract the active correction for this field (append-only) and add
    the new one. Flushes; the caller commits."""
    now = datetime.utcnow()
    zone_id = zone.id if zone is not None else None
    for old in _active_overrides(session, prop, zone_id, field):
        old.retracted_at = now
        session.add(old)
    row = SiteOverride(property_id=prop.id, zone_id=zone_id, field=field,
                       value=value, method=method, created_at=now)
    session.add(row)
    if field == "sun":
        _apply_sun(session, prop, zone, value)
    session.flush()
    return row


@router.put("/{property_id}/overrides", response_model=SiteProfileOut,
            dependencies=[Depends(require_site_profile)])
def put_override(property_id: int, payload: OverrideIn,
                 user: User = Depends(get_current_user),
                 session: Session = Depends(get_session)):
    prop = _owned_property(property_id, user, session)
    zone = _override_zone(session, prop, payload.zone_id)
    value = payload.value
    if value is None or isinstance(value, (dict, list)) or (
            isinstance(value, str) and not (0 < len(value) <= 64)):
        raise HTTPException(status_code=422,
                            detail="A correction is one choice or one number.")
    if payload.field == "sun" and value not in SUN_TO_EXPOSURE:
        raise HTTPException(status_code=422,
                            detail="Sun is full_sun, part_shade or shade.")
    try:
        profile_service.validate_override(payload.field, value)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
    record_override(session, prop, zone, payload.field, value,
                    OverrideMethod(payload.method))
    session.commit()
    session.refresh(prop)
    return profile_service.site_profile(session, prop)


@router.delete("/{property_id}/overrides/{field}", response_model=SiteProfileOut,
               dependencies=[Depends(require_site_profile)])
def delete_override(property_id: int, field: str,
                    zone_id: Optional[int] = Query(default=None),
                    user: User = Depends(get_current_user),
                    session: Session = Depends(get_session)):
    """Retracts the correction; the public reading shows again."""
    prop = _owned_property(property_id, user, session)
    zone = _override_zone(session, prop, zone_id)
    now = datetime.utcnow()
    for old in _active_overrides(session, prop, zone_id, field):
        old.retracted_at = now
        session.add(old)
    if field == "sun":
        _apply_sun(session, prop, zone, None)
    session.commit()
    session.refresh(prop)
    return profile_service.site_profile(session, prop)


# --- zones ------------------------------------------------------------------------

@router.get("/{property_id}/zones", response_model=list[ZoneOut],
            dependencies=[Depends(require_site_profile)])
def list_zones(property_id: int, user: User = Depends(get_current_user),
               session: Session = Depends(get_session)):
    prop = _owned_property(property_id, user, session)
    profile = profile_service.site_profile(session, prop)
    return [_zone_out(session, z, profile) for z in _zones(session, prop)]


@router.post("/{property_id}/zones", response_model=ZoneOut, status_code=201,
             dependencies=[Depends(require_site_profile)])
def create_zone(property_id: int, payload: ZoneCreate,
                user: User = Depends(get_current_user),
                session: Session = Depends(get_session)):
    prop = _owned_property(property_id, user, session)
    if len(_zones(session, prop)) >= MAX_ZONES_PER_PROPERTY:
        raise HTTPException(
            status_code=409,
            detail=f"A property can hold {MAX_ZONES_PER_PROPERTY} zones. "
                   "Delete one to add another.")
    zone = _new_zone(
        prop,
        name=(payload.name or "").strip() or ZONE_NAMES[payload.vegetation_type],
        is_whole_lot=False, boundary=_check_box(payload.box),
        boundary_source=BoundarySource.owner if payload.drawn else BoundarySource.default,
        vegetation_type=payload.vegetation_type, leaf_habit=payload.leaf_habit)
    session.add(zone)
    session.commit()
    session.refresh(zone)
    return _zone_out(session, zone, profile_service.site_profile(session, prop))


@router.patch("/{property_id}/zones/{zone_id}", response_model=ZoneOut,
              dependencies=[Depends(require_site_profile)])
def patch_zone(property_id: int, zone_id: int, payload: ZonePatch,
               user: User = Depends(get_current_user),
               session: Session = Depends(get_session)):
    """A box drawn over the whole-lot zone replaces the default footprint."""
    prop = _owned_property(property_id, user, session)
    zone = _owned_zone(prop, zone_id, session)
    changes = payload.model_dump(exclude_unset=True)
    if "name" in changes:
        zone.name = (changes["name"] or "").strip() or zone.name
    if "vegetation_type" in changes:
        if changes["vegetation_type"] is None and not zone.is_whole_lot:
            raise HTTPException(status_code=422,
                                detail="A zone needs to say what grows there.")
        zone.vegetation_type = changes["vegetation_type"]
    if "leaf_habit" in changes:
        zone.leaf_habit = changes["leaf_habit"]
    if "box" in changes:
        if payload.box is None:
            raise HTTPException(status_code=422, detail="A zone keeps its box.")
        zone.boundary_geojson = _check_box(payload.box)
        zone.boundary_source = BoundarySource.owner
    session.add(zone)
    session.commit()
    session.refresh(zone)
    return _zone_out(session, zone, profile_service.site_profile(session, prop))


@router.delete("/{property_id}/zones/{zone_id}", status_code=204,
               dependencies=[Depends(require_site_profile)])
def delete_zone(property_id: int, zone_id: int,
                user: User = Depends(get_current_user),
                session: Session = Depends(get_session)):
    prop = _owned_property(property_id, user, session)
    zone = _owned_zone(prop, zone_id, session)
    if zone.is_whole_lot:
        raise HTTPException(status_code=409,
                            detail="The whole-lot zone stays while the property exists.")
    if _plant_count(session, zone.id):
        raise HTTPException(status_code=409,
                            detail="This zone still holds plants. Move or delete them first.")
    if session.exec(select(StewardshipRecord)
                    .where(StewardshipRecord.growing_area_id == zone.id)).first():
        raise HTTPException(status_code=409,
                            detail="This zone has plant history and can't be deleted.")
    _delete_site_rows(session, prop.id, zone_id=zone.id)
    session.delete(zone)
    session.commit()
    return Response(status_code=204)


# --- imagery ----------------------------------------------------------------------
#
# The aerial image source is B2a's `app.services.site.sources.imagery`, which
# exposes
#     block_imagery(session, block, pin, footprint, *, client) -> ImageryOut
#     tile_jpeg(session, tile_key) -> bytes | None
# Until it exists these routes answer 503 with a plain sentence.

IMAGERY_UNAVAILABLE = "The aerial image is not available right now."


def _imagery_module():
    try:
        from app.services.site.sources import imagery  # type: ignore
    except ImportError:
        return None
    return imagery


def _imagery(session: Session, lat: float, lng: float,
             footprint: Optional[dict]) -> ImageryOut:
    module = _imagery_module()
    if module is None or not hasattr(module, "block_imagery"):
        raise HTTPException(status_code=503, detail=IMAGERY_UNAVAILABLE)
    # The aerial photography is of the United States only, and the privacy
    # policy says no map service is asked about land outside it. The check
    # is the same rough outline the site profile uses (services/coverage.py).
    if not coverage.in_united_states(lat, lng):
        raise HTTPException(status_code=503, detail=IMAGERY_UNAVAILABLE)
    block = grid.snap_block(lat, lng)
    tiles.commit_eagerly(session)  # no write lock held across the image fetch
    # The image service is slow when cold (12 to 61 s measured). The app
    # waits 60 s for this route, so: one attempt that ends before that.
    client = site_http.OutboundClient(flag="site_profile",
                                      timeout=site_http.IMAGERY_TIMEOUT, max_retries=0)
    try:
        out = module.block_imagery(session, block, (lat, lng), footprint,
                                   client=client)
    except Exception as exc:  # noqa: BLE001
        from app.services.site.types import SourceUnavailable
        if isinstance(exc, SourceUnavailable):
            raise HTTPException(status_code=503, detail=IMAGERY_UNAVAILABLE) from None
        raise
    finally:
        client.close()
    session.commit()
    return out


@router.get("/{property_id}/imagery", response_model=ImageryOut,
            dependencies=[Depends(require_site_profile)])
@limiter.limit(SITE_BUILD_LIMIT)
def property_imagery(request: Request, property_id: int,
                     user: User = Depends(get_current_user),
                     session: Session = Depends(get_session)):
    prop = _owned_property(property_id, user, session)
    whole = _whole_lot(session, prop)
    return _imagery(session, prop.pin_lat, prop.pin_lng,
                    whole.boundary_geojson if whole else None)


imagery_router = APIRouter(prefix="/imagery", tags=["imagery"],
                           dependencies=[Depends(require_site_profile)])


@imagery_router.get("/block", response_model=ImageryOut)
@limiter.limit(SITE_BUILD_LIMIT)
def block_imagery(request: Request, lat: float = Query(ge=-90, le=90),
                  lng: float = Query(ge=-180, le=180),
                  user: User = Depends(get_current_user),
                  session: Session = Depends(get_session)):
    """For the pin step, before a property exists. The pin is used to pick
    the block and is not stored."""
    return _imagery(session, lat, lng, grid.default_footprint(lat, lng))


@imagery_router.get("/tiles/{tile_key}.jpg")
def imagery_tile(tile_key: str, user: User = Depends(get_current_user),
                 session: Session = Depends(get_session)):
    if not _TILE_KEY.match(tile_key):
        raise HTTPException(status_code=404, detail="Image not found")
    module = _imagery_module()
    if module is None or not hasattr(module, "tile_jpeg"):
        raise HTTPException(status_code=404, detail="Image not found")
    data = module.tile_jpeg(session, tile_key)
    session.commit()  # the tile cache moved last_used_at
    if data is None:
        raise HTTPException(status_code=404, detail="Image not found")
    return Response(content=data, media_type="image/jpeg",
                    headers={"Cache-Control": "private, max-age=86400"})


# --- map layers -------------------------------------------------------------------
#
# Sun, trees and water pictures over the aerial image, drawn only from the
# elevation and canopy copies the server already holds (services/site/
# layers.py): these routes never build an outbound client. A layer whose
# source is not cached yet reads "not_ready" in the list and answers 409 as
# a picture; one that cannot be drawn here (outside the United States, or
# ground data too coarse) reads "unavailable" and answers 409 too.

#: Gentler than SITE_BUILD_LIMIT: these answers cost no outside request,
#: and a screen asks for the list and up to three pictures.
LAYER_LIMIT = "30/minute"


def _layer_block(prop: Property):
    return grid.snap_block(prop.pin_lat, prop.pin_lng)


def _layers_preparing(prop: Property) -> bool:
    """True while the background step that caches the layers' sources is
    pending or building, so "check back in a few minutes" is true."""
    bg = profile_service.profile_status(prop).background
    return bg in ("pending", "building")


@router.get("/{property_id}/layers", response_model=MapLayersOut,
            dependencies=[Depends(require_site_profile)])
@limiter.limit(LAYER_LIMIT)
def property_layers(request: Request, property_id: int,
                    user: User = Depends(get_current_user),
                    session: Session = Depends(get_session)):
    prop = _owned_property(property_id, user, session)
    out = layer_service.layers_for(
        session, _layer_block(prop), property_id=prop.id,
        in_us=coverage.in_united_states(prop.pin_lat, prop.pin_lng),
        preparing=_layers_preparing(prop))
    session.commit()  # the tile cache moved last_used_at
    return out


@router.get("/{property_id}/layers/{kind}.png",
            dependencies=[Depends(require_site_profile)])
@limiter.limit(LAYER_LIMIT)
def property_layer_image(request: Request, property_id: int, kind: str,
                         user: User = Depends(get_current_user),
                         session: Session = Depends(get_session)):
    # Tile touches and the stored picture commit at once, so no write lock
    # is held while the picture is drawn (seconds on the small machine).
    tiles.commit_eagerly(session)
    prop = _owned_property(property_id, user, session)
    if kind not in layer_service.KINDS:
        raise HTTPException(status_code=404, detail="Map layer not found")
    if not coverage.in_united_states(prop.pin_lat, prop.pin_lng):
        raise HTTPException(status_code=409, detail=layer_service.OUTSIDE_US_TEXT)
    try:
        data = layer_service.layer_png(session, _layer_block(prop), kind,
                                       property_id=prop.id)
    except layer_service.LayerNotReady as exc:
        session.commit()
        detail = (layer_service.not_ready_text(_layers_preparing(prop))
                  if exc.status == "not_ready" else exc.text)
        raise HTTPException(status_code=409, detail=detail) from None
    session.commit()  # the tile cache moved last_used_at, or stored the picture
    return Response(content=data, media_type="image/png",
                    headers={"Cache-Control": "private, max-age=86400"})


# --- seasonal plan ----------------------------------------------------------------

@router.get("/{property_id}/seasonal-plan", response_model=SeasonalPlanOut,
            dependencies=[Depends(require_season_plan)])
def get_seasonal_plan(property_id: int, user: User = Depends(get_current_user),
                      session: Session = Depends(get_session)):
    prop = _owned_property(property_id, user, session)
    return plan_service.seasonal_plan(session, prop)


def _find_event(plan: SeasonalPlanOut, event_key: str) -> Optional[SeasonEvent]:
    return next((e for e in plan.events if e.event_key == event_key), None)


@router.put("/{property_id}/seasonal-plan/events/{event_key}",
            response_model=SeasonEvent,
            dependencies=[Depends(require_season_plan)])
def put_event_state(property_id: int, event_key: str,
                    payload: SeasonEventStateIn,
                    user: User = Depends(get_current_user),
                    session: Session = Depends(get_session)):
    """Records what the owner said about one event ("clear" forgets it) and
    answers with the event as the plan now shows it. An event the plan does
    not hold is a 404."""
    prop = _owned_property(property_id, user, session)
    if _find_event(plan_service.seasonal_plan(session, prop), event_key) is None:
        raise HTTPException(status_code=404, detail="Seasonal event not found")
    row = plan_service.find_state(session, prop.id, event_key)
    now = datetime.utcnow()
    if payload.state == "clear":
        if row is not None:
            session.delete(row)
    else:
        if row is None:
            row = plan_service.claim_state(session, prop.id, event_key, payload.state, now)
        row.status = payload.state
        row.observed_on = payload.observed_on
        row.updated_at = now
        session.add(row)
    session.commit()
    event = _find_event(plan_service.seasonal_plan(session, prop), event_key)
    if event is None:
        raise HTTPException(status_code=404, detail="Seasonal event not found")
    return event


# --- Home -------------------------------------------------------------------------

vitals_router = APIRouter(tags=["vitals"])


@vitals_router.get("/vitals", response_model=VitalsOut,
                   dependencies=[Depends(require_season_plan)])
def get_vitals(property_id: Optional[int] = Query(default=None),
               user: User = Depends(get_current_user),
               session: Session = Depends(get_session)):
    """Home. With `property_id`, that property (404 if it is not the
    person's); without it, their oldest property, or none. Properties are
    only read while SITE_PROFILE_ENABLED is on."""
    site_on = get_settings().site_profile_enabled
    prop: Optional[Property] = None
    if property_id is not None:
        if not site_on:
            raise HTTPException(status_code=404, detail="Property not found")
        prop = _owned_property(property_id, user, session)
    elif site_on:
        prop = session.exec(
            select(Property).where(Property.user_id == user.id)
            .order_by(Property.id.asc())).first()
    out = vitals_service.vitals(session, user, prop)
    out.can_add_land = site_on
    if prop is not None and out.property is None:
        out.property = property_out(session, prop)
    return out
