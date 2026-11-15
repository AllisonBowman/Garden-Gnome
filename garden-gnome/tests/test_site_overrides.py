"""Owner corrections (overrides.py): which fields can be corrected and with
what, append-only rows, the resolved value, and the sun column kept in step
on the growing-area row."""
import pytest
from sqlmodel import select

from app.models.models import (
    GrowingArea, OverrideMethod, Property, SiteOverride, SunExposure, User,
)
from app.services.site import overrides as o


def test_fields_and_choices():
    assert not o.can_override("land_cover") and not o.can_override("hardiness_zone")
    assert [v for v, _ in o.spec("sun").choices] == ["full_sun", "part_shade", "shade"]
    assert [v for v, _ in o.spec("soil_texture").choices] == ["sandy", "loamy", "clayey"]
    assert o.label("water_collects", "stands_after_rain") == "Water stands here after rain"
    assert o.label("water_collects", "stays_dry") == "This stays dry"
    assert o.spec("soil_ph").kind == "number" and o.spec("soil_ph").measured
    assert "flat" in [v for v, _ in o.spec("facing").choices]
    assert [v for v, _ in o.spec("disturbed_soil").choices] == ["original_ground", "brought_in"]


@pytest.mark.parametrize("field,value", [
    ("sun", "lots"), ("soil_texture", "gravel"), ("soil_ph", 2.0), ("soil_ph", "6"),
    ("soil_ph", True), ("land_cover", "forest"), ("hardiness_zone", "8a"),
    ("frost_dates", "early"), ("facing", "up"), ("not_a_field", 1),
])
def test_bad_corrections_are_refused(field, value):
    with pytest.raises(ValueError):
        o.validate(field, value)


@pytest.mark.parametrize("field,value", [
    ("sun", "shade"), ("soil_texture", "clayey"), ("soil_ph", 6.4), ("soil_ph", 7),
    ("water_collects", "stays_dry"), ("facing", "south_west"),
    ("disturbed_soil", "brought_in"),
])
def test_good_corrections_pass(field, value):
    o.validate(field, value)


def _land(session):
    user = User(email=f"o-{id(session)}@example.test")
    session.add(user)
    session.flush()
    prop = Property(user_id=user.id, pin_lat=38.9123, pin_lng=-76.9681)
    session.add(prop)
    session.flush()
    whole = GrowingArea(name="Whole lot", user_id=user.id, property_id=prop.id,
                        is_whole_lot=True)
    bed = GrowingArea(name="Bed", user_id=user.id, property_id=prop.id)
    session.add(whole)
    session.add(bed)
    session.flush()
    return prop, whole, bed


def test_record_is_append_only_and_keeps_the_sun_column_in_step(session):
    prop, whole, bed = _land(session)
    o.record(session, prop, None, "sun", "shade", OverrideMethod.tap)
    o.record(session, prop, None, "sun", "full_sun", OverrideMethod.tap)
    o.record(session, prop, bed, "sun", "part_shade", OverrideMethod.tap)
    rows = session.exec(select(SiteOverride).where(SiteOverride.property_id == prop.id)
                        .order_by(SiteOverride.id)).all()
    assert [(r.zone_id, r.value, r.retracted_at is None) for r in rows] == [
        (None, "shade", False), (None, "full_sun", True), (bed.id, "part_shade", True)]
    assert whole.sun_source == "owner" and whole.sun_exposure == SunExposure.full_sun
    assert bed.sun_source == "owner" and bed.sun_exposure == SunExposure.partial_sun

    found = o.active(session, prop)
    assert o.for_zone(found, "sun", None, whole.id).value == "full_sun"
    assert o.for_zone(found, "sun", whole.id, whole.id).value == "full_sun"
    assert o.for_zone(found, "sun", bed.id, whole.id).value == "part_shade"
    assert o.for_zone(found, "soil_texture", bed.id, whole.id) is None

    o.sync_sun_column(bed, None)
    assert bed.sun_source is None
    with pytest.raises(ValueError):
        o.record(session, prop, None, "land_cover", "forest", OverrideMethod.tap)


def test_a_whole_lot_zone_row_and_a_property_row_resolve_to_the_newer(session):
    prop, whole, _ = _land(session)
    o.record(session, prop, None, "soil_texture", "sandy", OverrideMethod.tap)
    o.record(session, prop, whole, "soil_texture", "clayey", OverrideMethod.tap)
    found = o.active(session, prop)
    assert o.for_zone(found, "soil_texture", None, whole.id).value == "clayey"
