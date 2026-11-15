"""Owner corrections of site values (`site_override`, PLAN.md section 5).

Corrections are append-only: a new one retracts the active one for the same
field and zone, and a refresh never touches them. The resolved value is the
owner's correction when one is active, otherwise the latest public reading;
the public value stays visible beside it (`SiteValue.public`).

Land cover and the official hardiness zone cannot be corrected (build spec
A5); the frost dates are adjusted through the property's frost setting
instead. A sun correction also sets the zone's `sun_exposure` and
`sun_source = owner` on the growing-area row, so the existing fit engine and
the 1.1.x client read the owner's answer (PLAN.md section 5).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from sqlmodel import Session, select

from app.models.models import GrowingArea, Property, SiteOverride, SunExposure


@dataclass(frozen=True)
class Spec:
    kind: str                                 # "choice" | "number" | "none"
    choices: tuple[tuple[str, str], ...] = ()  # (value, label)
    low: Optional[float] = None
    high: Optional[float] = None
    measured: bool = False                    # a number the owner measured


FACINGS = (
    ("north", "North"), ("north_east", "North-east"), ("east", "East"),
    ("south_east", "South-east"), ("south", "South"),
    ("south_west", "South-west"), ("west", "West"),
    ("north_west", "North-west"), ("flat", "Flat, no facing direction"),
)

#: Which fields the owner may correct, and how.
SPECS: dict[str, Spec] = {
    "sun": Spec("choice", (
        ("full_sun", "Full sun (6 or more hours)"),
        ("part_shade", "Part shade (3 to 6 hours)"),
        ("shade", "Shade (under 3 hours)"))),
    "soil_texture": Spec("choice", (
        ("sandy", "Sandy (loose and gritty)"),
        ("loamy", "Loamy (crumbly)"),
        ("clayey", "Clayey (sticky when wet)"))),
    "soil_ph": Spec("number", low=3.0, high=10.0, measured=True),
    "water_collects": Spec("choice", (
        ("stands_after_rain", "Water stands here after rain"),
        ("stays_dry", "This stays dry"))),
    "soil_drainage": Spec("choice", (
        ("day_or_more", "After heavy rain, water sits for a day or more"),
        ("few_hours", "After heavy rain, water sits for a few hours"),
        ("drains_away", "After heavy rain, water drains away"))),
    "facing": Spec("choice", FACINGS),
    "slope": Spec("choice", (
        ("flat", "Flat"), ("gentle", "Gentle"), ("steep", "Steep"),
        ("regraded", "The ground has been regraded"))),
    "disturbed_soil": Spec("choice", (
        ("original_ground", "This is original ground"),
        ("brought_in", "Soil was brought in or regraded"))),
    "flooding": Spec("choice", (
        ("floods", "This area floods"), ("never_floods", "Never floods"))),
    "land_cover": Spec("none"),
    "hardiness_zone": Spec("none"),
    "frost_dates": Spec("none"),
}

#: Sun answers, as the old growing-area column understands them.
SUN_TO_EXPOSURE = {
    "full_sun": SunExposure.full_sun,
    "part_shade": SunExposure.partial_sun,
    "shade": SunExposure.shade,
}


def spec(field: str) -> Spec:
    return SPECS.get(field, Spec("none"))


def can_override(field: str) -> bool:
    return spec(field).kind != "none"


def choices(field: str) -> list[dict]:
    return [{"value": v, "label": label} for v, label in spec(field).choices]


def label(field: str, value: Any) -> Optional[str]:
    for v, text in spec(field).choices:
        if v == value:
            return text
    return None


def validate(field: str, value: Any) -> None:
    """Raise ValueError (with a plain sentence) for a correction that is not
    one of the field's choices, or a number out of range."""
    s = SPECS.get(field)
    if s is None or s.kind == "none":
        if field == "hardiness_zone":
            raise ValueError("The official hardiness zone cannot be changed. "
                             "Use the frost setting if your yard frosts earlier "
                             "or later than the neighbours.")
        if field == "land_cover":
            raise ValueError("Land cover describes the neighbourhood, not your lot, "
                             "so it cannot be changed. Draw zones for your lot instead.")
        if field == "frost_dates":
            raise ValueError("Typical frost dates come from weather stations. Use the "
                             "frost setting if your yard frosts earlier or later.")
        raise ValueError(f"{field} cannot be corrected.")
    if s.kind == "number":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("Enter one number from your soil test.")
        if not (s.low <= float(value) <= s.high):
            raise ValueError(f"A soil acidity (pH) result is between {s.low:g} "
                             f"and {s.high:g}.")
        return
    allowed = [v for v, _ in s.choices]
    if value not in allowed:
        raise ValueError("Choose one of: " + ", ".join(allowed) + ".")


def active(session: Session, prop: Property) -> dict[tuple[Optional[int], str], SiteOverride]:
    """The active correction for each (zone_id, field); the newest wins if
    more than one is somehow active. zone_id None means the whole property."""
    rows = session.exec(
        select(SiteOverride)
        .where(SiteOverride.property_id == prop.id)
        .where(SiteOverride.retracted_at == None)  # noqa: E711
        .order_by(SiteOverride.created_at.asc(), SiteOverride.id.asc())
    ).all()
    out: dict[tuple[Optional[int], str], SiteOverride] = {}
    for row in rows:
        out[(row.zone_id, row.field)] = row
    return out


def for_zone(found: dict[tuple[Optional[int], str], SiteOverride], field: str,
             zone_id: Optional[int], whole_lot_id: Optional[int]) -> Optional[SiteOverride]:
    """The correction that applies to one zone. The whole property and its
    whole-lot zone are the same place, so either row applies to both (the
    newer one wins)."""
    if zone_id is None or zone_id == whole_lot_id:
        rows = [r for r in (found.get((None, field)),
                            found.get((whole_lot_id, field)) if whole_lot_id else None)
                if r is not None]
        if not rows:
            return None
        return max(rows, key=lambda r: (r.created_at, r.id or 0))
    return found.get((zone_id, field))


def sync_sun_column(zone: Optional[GrowingArea], value: Any) -> None:
    """Keep a zone's growing-area sun column in step with the owner's answer
    (the router calls the same rule when it records a correction). None
    clears the owner flag, so the fit engine treats sun as unknown again."""
    if zone is None:
        return
    if value is None:
        zone.sun_source = None
    elif value in SUN_TO_EXPOSURE:
        zone.sun_exposure = SUN_TO_EXPOSURE[value]
        zone.sun_source = "owner"


def record(session: Session, prop: Property, zone: Optional[GrowingArea],
           field: str, value: Any, method: Any, *,
           now: Optional[datetime] = None) -> SiteOverride:
    """Append a correction, retracting the active one for the same field and
    zone. Flushes; the caller commits. For callers other than the routes
    (which use properties.record_override, the same rule)."""
    validate(field, value)
    t = now or datetime.utcnow()
    zone_id = zone.id if zone is not None else None
    for (zid, f), old in active(session, prop).items():
        if zid == zone_id and f == field:
            old.retracted_at = t
            session.add(old)
    row = SiteOverride(property_id=prop.id, zone_id=zone_id, field=field,
                       value=value, method=method, created_at=t)
    session.add(row)
    if field == "sun":
        target = zone
        if target is None:
            target = session.exec(
                select(GrowingArea).where(GrowingArea.property_id == prop.id)
                .where(GrowingArea.is_whole_lot == True)).first()  # noqa: E712
        sync_sun_column(target, value)
        if target is not None:
            session.add(target)
    session.flush()
    return row
