"""The seasonal engine without a database (PLAN.md section 7 tests):
normals semantics, the range rule, day length, events at three fixed dates
for both landmarks, frost confidence, the forecast night rules and alerts."""
from datetime import date, datetime, timedelta

import pytest

from app.services.season import alerts, events as ev, forecast as fcm, normals as nm
from app.services.season.daylength import day_length_hours, first_day_shorter_than
from tests.explained_walker import assert_explained
from tests.season_fixtures import ARBORETUM, ZILKER, load

NOV_15 = date(2026, 11, 15)
LATE_WINTER = date(2027, 2, 20)
MIDSUMMER = date(2027, 7, 15)
NOW = datetime(2026, 11, 15, 14, 0)


def _fc(name: str, fetched_at: datetime = NOW) -> fcm.Forecast:
    doc = load(name)
    return fcm.parse_nws(doc["points"], doc["gridpoint"], doc["forecast"], fetched_at=fetched_at)


def _inp(pin, today, *, forecast=None, **kw) -> ev.Inputs:
    return ev.Inputs(lat=pin[0], today=today, normals=nm.frost_normals(*pin),
                     forecast=forecast, **kw)


def _by_type(events, year=None):
    out = {}
    for e in events:
        if year is None or e.event_key.split(":")[1] == str(year):
            out.setdefault(e.type, e)
    return out


# --- normals ---------------------------------------------------------------------

def test_normals_pinned_to_the_arboretum_station():
    n = nm.frost_normals(*ARBORETUM)
    assert n["status"] == "ready"
    assert n["stations"][0]["id"] == "USC00186350"
    assert n["stations"][1]["id"] == "USW00013743"  # Reagan National
    # Fall: "on or before". 10% = only one year in ten this early.
    assert n["fall"]["32"] == {"p10": "10-26", "p50": "11-08", "p90": "11-23"}
    # Spring: "a later one after". 10% = one year in ten freezes after it.
    assert n["spring"]["32"] == {"p10": "04-11", "p50": "03-29", "p90": "03-15"}


def test_washington_shows_a_range_because_its_stations_differ_by_ten_days():
    n = nm.frost_normals(*ARBORETUM)
    assert n["ranges"]["fall_32"] is True
    assert nm.typical_text(n, "fall", "32") == "around 8 to 18 November (nearby stations differ)"
    assert "8 to 18 November" in n["explained"]["display"]


def test_by_is_only_used_with_the_nine_in_ten_date():
    n = nm.frost_normals(*ARBORETUM)
    reason = n["explained"]["reason"]
    assert "by 23 November in nine years in ten" in reason
    assert "by 8 November" not in reason and "by 26 October" not in reason
    import re
    for pin in (ARBORETUM, ZILKER):
        for today in (NOV_15, LATE_WINTER, MIDSUMMER):
            for e in ev.plan_events(_inp(pin, today)):
                for text in (e.window.text, e.explained.display, e.explained.reason):
                    for m in re.finditer(r"\bby (?:about )?\d{1,2} [A-Z][a-z]+", text):
                        assert text[m.end():].startswith(" in nine years in ten"), text


def test_austin_shows_a_range_and_a_late_season():
    n = nm.frost_normals(*ZILKER)
    assert n["status"] == "ready" and n["ranges"]["fall_32"] is True
    assert "December" in nm.typical_text(n, "fall", "32")
    assert n["daily"]["fall_mean45"] is None  # the normal mean never falls to 45 F


def test_no_station_answers_plainly():
    n = nm.frost_normals(0.0, -150.0)  # open Pacific
    assert n["status"] == "none" and n["confidence"] == "not_known_yet"
    assert_explained(n["explained"])


def test_normals_file_is_small():
    assert nm.DATA_FILE.stat().st_size < 5 * 1024 * 1024


# --- day length and fall hardening ------------------------------------------------

def test_day_length_rule_for_both_test_latitudes():
    assert first_day_shorter_than(ARBORETUM[0], 13.5, 2026) == date(2026, 8, 22)
    assert first_day_shorter_than(ZILKER[0], 13.5, 2026) == date(2026, 8, 7)
    assert 9.5 < day_length_hours(ARBORETUM[0], NOV_15) < 10.5


def test_fall_hardening_dates_for_both_test_points():
    arb = _by_type(ev.plan_events(_inp(ARBORETUM, NOV_15)), 2026)["fall_hardening"]
    assert arb.sort_date == date(2026, 9, 27)  # 8 November minus 42 days
    zil = _by_type(ev.plan_events(_inp(ZILKER, NOV_15)), 2026)["fall_hardening"]
    # The nearest Austin station's median first freeze is 17 November.
    assert zil.sort_date == date(2026, 10, 6)
    for e in (arb, zil):
        assert e.explained.confidence in ("area_estimate", "rough_estimate")


def test_leaf_drop_window_from_normals_for_both_stations():
    arb = _by_type(ev.plan_events(_inp(ARBORETUM, NOV_15)), 2026)["leaf_drop"]
    assert (arb.window.start, arb.window.end) == (date(2026, 10, 22), date(2026, 11, 27))
    assert arb.status == "happening" and arb.explained.confidence == "rough_estimate"
    zil = _by_type(ev.plan_events(_inp(ZILKER, NOV_15)), 2026)["leaf_drop"]
    assert zil.window.start < zil.window.end and zil.window.end.month in (12, 1)


# --- three fixed days --------------------------------------------------------------

def test_mid_november_arboretum_with_the_forecast():
    events = ev.plan_events(_inp(ARBORETUM, NOV_15, forecast=_fc("arboretum")))
    by = _by_type(events, 2026)
    assert by["first_frost"].status == "forecast"          # 35 F tonight
    assert by["first_frost"].window.start == NOV_15
    assert by["first_freeze"].status == "expected"         # in its window, nothing forecast
    assert by["dormancy"].status == "typically_around"
    assert by["fall_hardening"].status == "happening"
    assert_explained([e.model_dump(mode="json") for e in events])


def test_the_plan_lists_the_next_twelve_months():
    for pin in (ARBORETUM, ZILKER):
        for today in (NOV_15, LATE_WINTER, MIDSUMMER):
            events = ev.plan_events(_inp(pin, today))
            dated = [e.sort_date for e in events if e.sort_date]
            assert dated == sorted(dated)
            assert max(dated) <= today + timedelta(days=365)
            ahead = {e.type for e in events if e.sort_date and e.sort_date >= today}
            # Something from each half of the year is always ahead within a year.
            assert ahead & {"first_frost", "first_freeze", "fall_hardening"}
            assert ahead & {"last_frost", "spring_emergence", "spring_cleanup", "tender_plants_out"}
            assert_explained([e.model_dump(mode="json") for e in events])


def test_late_winter_shows_fall_behind_and_spring_ahead():
    events = ev.plan_events(_inp(ARBORETUM, LATE_WINTER))
    by = _by_type(events, 2026)
    for t in ("first_frost", "first_freeze", "hard_freeze"):
        assert by[t].status == "typically_around"  # P0-5 fallback: no observed lows
        assert "tell us" in by[t].explained.display
        assert "mark_happened" in by[t].owner_actions
    assert by["leaf_drop"].status == "happened" and "estimate" in by["leaf_drop"].explained.display
    assert by["dormancy"].status == "happened"
    assert by["spring_emergence"].status == "typically_around"
    assert by["last_frost"].window.end == date(2027, 4, 11)
    nxt = _by_type(events, 2027)
    assert "first_frost" in nxt  # next fall is within twelve months


def test_midsummer_is_all_ahead():
    events = ev.plan_events(_inp(ZILKER, MIDSUMMER))
    assert {e.event_key.split(":")[1] for e in events} <= {"2027"}
    assert all(e.status in ("typically_around", "not_needed", "expected") for e in events)
    assert ev.season_label(MIDSUMMER) == "Mid summer 2027"
    assert ev.season_label(NOV_15) == "Late fall 2026"


def test_a_warm_january_does_not_fire_spring_emergence():
    # A synthetic warm week in a cold-winter place: lows of 55 F in January.
    fc = _fc("arboretum", fetched_at=datetime(2027, 1, 10, 14))
    for n in fc.nights:
        n.low_f = 55.0
    events = ev.plan_events(_inp(ARBORETUM, date(2027, 1, 10), forecast=fc))
    em = _by_type(events, 2026)["spring_emergence"]
    assert em.status == "typically_around" and em.sort_date == date(2027, 3, 14)


# --- lot contents decide which tasks appear ----------------------------------------------

def _tasks(events):
    return {t.task_key.split(":")[-1] for e in events for t in e.tasks}


def test_lot_contents_decide_the_tasks():
    paved = ev.plan_events(_inp(ARBORETUM, NOV_15, lot_contents=["mostly_paved", "potted_plants"]))
    by = _by_type(paved, 2026)
    assert by["leaf_drop"].status == "not_needed" and by["leaf_drop"].tasks == []
    assert "frost_pots" in _tasks(paved)
    assert "hardening_no_feed" not in _tasks(paved)
    yard = ev.plan_events(_inp(ARBORETUM, NOV_15, lot_contents=["trees_that_drop_leaves", "lawn",
                                                                 "garden_beds"]))
    names = _tasks(yard)
    assert {"leaves_beds", "leaves_lawn", "hardening_no_feed", "hard_freeze_stems"} <= names
    assert "frost_pots" not in names
    assert _by_type(yard, 2026)["tender_plants_out"].status == "not_needed"


def test_low_impact_guidance_is_in_the_task_text():
    events = ev.plan_events(_inp(ARBORETUM, NOV_15, lot_contents=["trees_that_drop_leaves",
                                                                   "garden_beds", "lawn"]))
    text = {t.task_key.split(":")[-1]: t for e in events for t in e.tasks}
    assert "Leave whole leaves" in text["leaves_beds"].text
    assert "skip fertilizer" in text["hardening_no_feed"].text
    assert "not lawn advice" in text["hardening_no_feed"].low_impact_note
    assert "stems" in text["hard_freeze_stems"].text and "standing" in text["hard_freeze_stems"].text


def test_zones_target_tasks_and_evergreens_silence_leaf_drop():
    zones = [ev.Zone(1, None, None, True), ev.Zone(7, "tree", "evergreen"),
             ev.Zone(8, "garden_bed", None)]
    events = ev.plan_events(_inp(ARBORETUM, NOV_15, lot_contents=[], zones=zones))
    by = _by_type(events, 2026)
    assert by["leaf_drop"].status == "not_needed"
    stems = next(t for t in by["hard_freeze"].tasks if t.task_key.endswith("hard_freeze_stems"))
    assert stems.applies_to.kind == "zones" and stems.applies_to.ids == [8]


def test_every_task_has_a_reason_and_named_sources():
    for pin in (ARBORETUM, ZILKER):
        for today in (NOV_15, LATE_WINTER, MIDSUMMER):
            for e in ev.plan_events(_inp(pin, today)):
                for t in e.tasks:
                    assert t.reason and t.sources and all(s.name for s in t.sources)
                    if t.sources[0].name == "General gardening advice":
                        assert t.text.startswith("General advice")


# --- the forecast rules -----------------------------------------------------------------

def test_night_assignment_uses_local_evening():
    fc = _fc("arboretum")
    # minTemperature starting 2026-11-16T00:00Z is 19:00 on 15 November in Washington.
    assert fc.night(date(2026, 11, 15)).low_f == pytest.approx(35, abs=0.6)
    zil = _fc("zilker")
    assert zil.timezone == "America/Chicago"
    assert round(zil.night(date(2026, 11, 15)).low_f) == 48


def test_frost_bias_moves_the_low_only_on_clear_calm_nights():
    fc = _fc("arboretum")
    windy = fc.night(date(2026, 11, 15))      # 7 miles per hour, 43% cloud
    calm = fc.night(date(2026, 11, 16))       # 3.5 miles per hour, 6% cloud
    assert not fcm.radiative(windy) and fcm.radiative(calm)
    assert fcm.adjusted_low(windy, "earlier") == windy.low_f
    assert fcm.adjusted_low(calm, "earlier") == calm.low_f - 2
    assert fcm.adjusted_low(calm, "later") == calm.low_f + 2
    events = ev.plan_events(_inp(ARBORETUM, NOV_15, forecast=fc, frost_bias="earlier"))
    freeze = _by_type(events, 2026)["first_freeze"]
    assert freeze.status == "forecast" and "for your yard" in freeze.explained.display
    assert "frosts earlier than the neighbours" in freeze.explained.reason


@pytest.mark.parametrize("low,expected", [(37, "none"), (36, "frost"), (33, "frost"), (32, "freeze"),
                                          (29, "freeze"), (28, "hard_freeze"), (None, "none")])
def test_bands_at_every_edge(low, expected):
    assert fcm.band(low) == expected


def test_frost_confidence_table_row_by_row():
    fc = _fc("arboretum")
    n = fc.nights[0]
    assert ev._forecast_conf(fc, n, 35, 6) == "rough_estimate"     # 6 to 7 nights away
    assert ev._forecast_conf(fc, n, 35, 4) == "area_estimate"      # 3 to 5 nights away
    assert ev._forecast_conf(fc, n, 35, 0) == "area_estimate"      # one provider: capped
    fc.second_opinion = {n.date.isoformat(): 42}
    assert ev._forecast_conf(fc, n, 35, 0) == "rough_estimate"     # providers 7 F apart
    fc.second_opinion = {n.date.isoformat(): 36}
    # Two providers agree, 0 nights away: still capped at Area estimate in the first season.
    assert ev._forecast_conf(fc, n, 35, 0) == "area_estimate"


def test_nothing_beyond_seven_nights_is_an_event():
    fc = _fc("arboretum")
    for n in fc.nights:
        n.low_f = 50.0
    fc.nights.append(fcm.Night(date=NOV_15 + timedelta(days=9), low_f=20.0, wind_mph=1, sky_pct=0))
    by = _by_type(ev.plan_events(_inp(ARBORETUM, NOV_15, forecast=fc)), 2026)
    assert by["hard_freeze"].status != "forecast"


def test_a_hard_freeze_seen_first_satisfies_frost_and_freeze():
    states = {"hard_freeze:2026:fall": ev.OwnerState("seen_in_forecast", date(2026, 11, 10),
                                                     "hard_freeze")}
    by = _by_type(ev.plan_events(_inp(ARBORETUM, NOV_15, states=states)), 2026)
    for t in ("first_frost", "first_freeze", "hard_freeze"):
        assert by[t].status == "happened"
        assert by[t].explained.confidence == "rough_estimate"
        assert "Not measured" in by[t].explained.display
        assert by[t].owner_actions == ["mark_not_yet"]


def test_owner_taps_outrank_everything():
    states = {"first_frost:2026:fall": ev.OwnerState("happened", date(2026, 11, 2)),
              "leaf_drop:2026:fall": ev.OwnerState("done"),
              "first_freeze:2026:fall": ev.OwnerState("not_yet")}
    fc = _fc("arboretum")
    by = _by_type(ev.plan_events(_inp(ARBORETUM, NOV_15, forecast=fc, states=states)), 2026)
    assert by["first_frost"].status == "happened"
    assert by["first_frost"].explained.confidence == "you_told_us"
    assert by["first_frost"].explained.provenance == "owner"
    assert "clear" in by["first_frost"].owner_actions
    assert by["leaf_drop"].status == "done"
    assert all(t.state == "done" for t in by["leaf_drop"].tasks)
    assert by["first_freeze"].status != "happened"


def test_warm_place_marks_rare_events_not_needed():
    n = nm.frost_normals(*ZILKER)
    n = dict(n, occurs_pct={"36": 100, "32": 40, "28": 20})
    inp = ev.Inputs(lat=ZILKER[0], today=NOV_15, normals=n)
    by = _by_type(ev.plan_events(inp), 2026)
    assert by["hard_freeze"].status == "not_needed" and by["hard_freeze"].tasks == []
    assert by["first_freeze"].status == "not_needed"
    assert by["dormancy"].title == "Winter rest"


def test_missing_normals_never_raise():
    n = nm.frost_normals(0.0, -150.0)
    for today in (NOV_15, LATE_WINTER, MIDSUMMER):
        events = ev.plan_events(ev.Inputs(lat=0.0, today=today, normals=n))
        assert events and all(e.type for e in events)
        assert_explained([e.model_dump(mode="json") for e in events])


# --- alerts ------------------------------------------------------------------------------

def test_alerts_from_the_forecast_carry_the_forecast_time():
    fc = _fc("arboretum")
    events = ev.plan_events(_inp(ARBORETUM, NOV_15, forecast=fc, frost_bias="earlier"))
    out = alerts.build_alerts(events, fc, now=NOW, today=NOV_15)
    assert out, "a frost tonight and a freeze on Monday night should alert"
    for a in out:
        assert a.built_from_forecast_at.replace(tzinfo=None) == fc.issued_at
        assert "Forecast as of" in a.body and "National Weather Service" in a.body
        assert a.fire_at > NOW.replace(tzinfo=a.fire_at.tzinfo)
        local = a.fire_at.astimezone(__import__("zoneinfo").ZoneInfo("America/New_York"))
        assert 8 <= local.hour < 21
    days = [a.fire_at.date() for a in out]
    assert len(days) == len(set(days))           # at most one a day
    assert len(out) <= 3


def test_no_alert_when_providers_disagree_or_far_away():
    fc = _fc("arboretum")
    fc.second_opinion = {n.date.isoformat(): (n.low_f or 0) + 10 for n in fc.nights}
    events = ev.plan_events(_inp(ARBORETUM, NOV_15, forecast=fc))
    assert alerts.build_alerts(events, fc, now=NOW, today=NOV_15) == []
    assert alerts.build_alerts(events, None, now=NOW, today=NOV_15) == []


def test_alerts_never_say_safe_after():
    for pin in (ARBORETUM, ZILKER):
        for today in (NOV_15, LATE_WINTER, MIDSUMMER):
            for e in ev.plan_events(_inp(pin, today)):
                blob = " ".join([e.window.text, e.explained.display, e.explained.reason]
                                + [t.text for t in e.tasks])
                assert "safe after" not in blob.lower()
                assert "—" not in blob  # no em dashes in owner-facing text
