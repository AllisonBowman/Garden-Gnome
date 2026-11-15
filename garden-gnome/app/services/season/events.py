"""The seasonal events: a pure engine (PLAN.md section 7; build spec section 4).

Given the place, today, the frost normals, the forecast (or none), what is on
the lot and what the owner has said, it returns the ten event types for the
current season (1 July to 30 June) and for as much of the next season as
falls within twelve months of today. Nothing here reads the database or the
network; `plan.py` gathers the inputs.

Observed freezes. No observed-temperature source was proven for this build
(PLAN.md P0-5 fallback path), so "happened" for a frost event comes only
from an owner tap, or from a cold night the Weather Service forecast for the
night that had already begun when we read it ("seen in the forecast",
worded as a forecast, never as a measurement). A fall event past its
nine-years-in-ten date with neither reads "typically around".

Spring Index. The USA National Phenology Network Spring Index layers are
published as GeoTIFF rasters, which this build cannot read without a new
reader, so spring emergence and first bloom use a stand-in labelled as our
estimate: the date the station's normal daily mean temperature, summed above
32 F from 1 January, reaches a level calibrated on the two test places
(data/README.md).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

from app.models.schemas import (
    AppliesTo, EventWindow, Explained, SeasonEvent, SeasonTask, SourceOut)
from app.services.season import forecast as fcm
from app.services.season import normals as nm
from app.services.season import rules
from app.services.season.daylength import first_day_shorter_than

DEGREE = "°F"

DAYLENGTH_SOURCE = {"name": "Day length calculated from your latitude",
                    "detail": "National Oceanic and Atmospheric Administration solar equations; no data sent anywhere"}
STANDIN_SOURCE = {"name": "Spring Index stand-in (our estimate)",
                  "detail": "Normal warmth summed from 1 January, calibrated on two places against the "
                            "USA National Phenology Network Spring Index",
                  "url": "https://www.usanpn.org/data/maps/spring"}
OWNER_SOURCE = {"name": "You told us", "detail": "Your answer in the app"}

FALL_TYPES = ("first_frost", "first_freeze", "hard_freeze")
THRESHOLD = {"first_frost": "36", "first_freeze": "32", "hard_freeze": "28"}
BAND_RANK = {"none": 0, "frost": 1, "freeze": 2, "hard_freeze": 3}
TYPE_RANK = {"first_frost": 1, "first_freeze": 2, "hard_freeze": 3}
NAMES = {"first_frost": "first frost", "first_freeze": "first freeze",
         "hard_freeze": "first hard freeze"}
DEFINITIONS = {
    "first_frost": "a night at or below 36 " + DEGREE + ", when frost can form on plants",
    "first_freeze": "a night at or below 32 " + DEGREE,
    "hard_freeze": "a night at or below 28 " + DEGREE + ", cold enough to end the season for most plants",
}


@dataclass
class Zone:
    id: int
    vegetation_type: Optional[str]
    leaf_habit: Optional[str]
    is_whole_lot: bool = False


@dataclass
class OwnerState:
    status: str               # done | not_needed | happened | not_yet | seen_in_forecast
    observed_on: Optional[date] = None
    band: Optional[str] = None


@dataclass
class Inputs:
    lat: float
    today: date
    normals: dict
    forecast: Optional[fcm.Forecast] = None
    lot_contents: Optional[list[str]] = None
    frost_bias: Optional[str] = None
    zones: list[Zone] = field(default_factory=list)
    states: dict[str, OwnerState] = field(default_factory=dict)


def season_year(d: date) -> int:
    """The season runs 1 July to 30 June; a January freeze belongs to the
    fall that started it."""
    return d.year if d.month >= 7 else d.year - 1


def event_key(etype: str, year: int, stage: str) -> str:
    return f"{etype}:{year}:{stage}"


# --- who the tasks are for ---------------------------------------------------------

@dataclass
class Audience:
    known: bool
    trees: bool
    deciduous: bool
    shrubs: bool
    beds: bool
    lawn: bool
    pots: bool
    paved: bool
    zone_ids: dict[str, list[int]]


def audience(inp: Inputs) -> Audience:
    lc = set(inp.lot_contents or [])
    owner_zones = [z for z in inp.zones if not z.is_whole_lot and z.vegetation_type]
    ids: dict[str, list[int]] = {}
    for z in owner_zones:
        ids.setdefault(z.vegetation_type, []).append(z.id)
    known = inp.lot_contents is not None or bool(owner_zones)
    woody = [z for z in owner_zones if z.vegetation_type in ("tree", "shrub")]
    decid_zone = any(z.leaf_habit in (None, "drops_leaves", "mixed") for z in woody)
    if not known:
        return Audience(False, True, True, True, True, True, True, True, ids)
    return Audience(
        known=True,
        trees="trees_that_drop_leaves" in lc or "evergreens" in lc or "tree" in ids,
        deciduous="trees_that_drop_leaves" in lc or decid_zone
                  or ("shrubs" in lc and not woody),
        shrubs="shrubs" in lc or "shrub" in ids,
        beds="garden_beds" in lc or "vegetables" in lc or "garden_bed" in ids,
        lawn="lawn" in lc or "grass" in ids,
        pots="potted_plants" in lc,
        paved="mostly_paved" in lc or "bare_hardscape" in ids,
        zone_ids=ids)


def _applies(aud: Audience, kinds: tuple[str, ...]) -> AppliesTo:
    ids = sorted(i for k in kinds for i in aud.zone_ids.get(k, []))
    return AppliesTo(kind="zones", ids=ids) if ids else AppliesTo(kind="lot", ids=[])


def _task(ekey: str, line_key: str, aud: Audience, kinds: tuple[str, ...], why: str,
          data_sources: list[dict], state: str) -> SeasonTask:
    ln = rules.line(line_key)
    src = rules.line_source(line_key)
    guidance = ("Guidance: general gardening advice; no primary source is attached yet."
                if ln["kind"] == "general" else f"Guidance: {src['name']}.")
    return SeasonTask(
        task_key=f"{ekey}:{line_key}", text=ln["text"],
        low_impact_note=ln.get("low_impact_note"),
        reason=f"{why} {guidance}".strip(),
        sources=[SourceOut(**s) for s in [src] + data_sources],
        applies_to=_applies(aud, kinds), state=state)


# --- small helpers -----------------------------------------------------------------

def _src(d: dict) -> SourceOut:
    return SourceOut(**d)


def _normals_source(n: dict) -> dict:
    st = n["stations"][0]
    return dict(nm.SOURCE, detail=f"{st['name']} station ({st['id']})")


def _forecast_source(fc: fcm.Forecast) -> dict:
    return dict(fcm.NWS_SOURCE, detail=f"Forecast as of {_when(fc)}")


def _when(fc: fcm.Forecast) -> str:
    from zoneinfo import ZoneInfo
    from datetime import timezone
    t = fc.issued_at.replace(tzinfo=timezone.utc).astimezone(ZoneInfo(fc.timezone))
    return clock_text(t)


def clock_text(t) -> str:
    """"1:56 am 15 November"."""
    hour = t.hour % 12 or 12
    ampm = "am" if t.hour < 12 else "pm"
    return f"{hour}:{t.minute:02d} {ampm} {t.day} {nm._MONTHS[t.month - 1]}"


def _weekday(d: date) -> str:
    return ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")[d.weekday()]


def _explained(display, confidence, reason, sources, provenance) -> Explained:
    return Explained(display=display, confidence=confidence, reason=reason,
                     sources=[_src(s) if isinstance(s, dict) else s for s in sources],
                     provenance=provenance)


def _min_conf(a: str, b: str) -> str:
    order = ["not_known_yet", "rough_estimate", "area_estimate", "good_estimate"]
    return a if order.index(a) <= order.index(b) else b


def _task_state(status: str) -> str:
    return {"done": "done", "not_needed": "not_needed"}.get(status, "open")


def _owner(inp: Inputs, key: str) -> Optional[OwnerState]:
    return inp.states.get(key)


def _actions(status: str, owner: Optional[OwnerState], kind: str) -> list[str]:
    acts: list[str]
    if kind == "frost":
        if status == "happened":
            acts = ["mark_not_yet"]
        else:
            acts = ["mark_happened", "mark_not_needed"]
    elif kind == "leaf":
        acts = ["mark_happened", "mark_done", "mark_not_needed"]
    elif kind == "state":
        acts = ["mark_happened", "mark_not_yet"]
    else:
        acts = ["mark_done", "mark_not_needed"]
    if owner is not None and owner.status != "seen_in_forecast":
        acts = [a for a in acts if a != {"done": "mark_done", "not_needed": "mark_not_needed",
                                         "happened": "mark_happened",
                                         "not_yet": "mark_not_yet"}.get(owner.status)]
        acts.append("clear")
    return acts


def _owner_override(owner: Optional[OwnerState], title: str):
    """(status, Explained) when the owner's answer decides the event."""
    if owner is None or owner.status in ("not_yet", "seen_in_forecast"):
        return None
    when = f" on {nm.day_text(owner.observed_on)}" if owner.observed_on else ""
    text = {"done": f"{title}: done{when}.",
            "not_needed": f"{title}: not needed this year.",
            "happened": f"{title}: happened{when}."}[owner.status]
    return owner.status, _explained(text, "you_told_us", "You marked this in the app.",
                                    [OWNER_SOURCE], "owner")


# --- frost, freeze and hard freeze (fall) --------------------------------------------

def _forecast_conf(fc: fcm.Forecast, night: fcm.Night, low: float, lead: int) -> str:
    second = (fc.second_opinion or {}).get(night.date.isoformat())
    if lead >= 6 or (second is not None and abs(second - low) > 5):
        return "rough_estimate"
    # 3 to 5 nights, one provider, or near a band edge: Area estimate. The
    # Good estimate row is capped off for the first season (PLAN.md section 7).
    return "area_estimate"


def _forecast_hit(inp: Inputs, threshold: float, after: Optional[date] = None):
    """The first forecast night from tonight with an adjusted low at or below
    `threshold`, as (night, adjusted low, lead)."""
    fc = inp.forecast
    if fc is None:
        return None
    today = inp.today
    for n in fc.nights:
        lead = (n.date - today).days
        if lead < 0 or lead > 7 or (after and n.date < after):
            continue
        adj = fcm.adjusted_low(n, inp.frost_bias)
        if adj is not None and round(adj) <= threshold:
            return n, adj, lead
    return None


def _range_text(adj: float, lead: int) -> str:
    spread = 3 if lead <= 2 else 5
    lo, hi = round(adj) - spread, round(adj) + spread
    return f"could be {lo} to {hi} {DEGREE}"


def _bias_note(inp: Inputs, night: fcm.Night) -> str:
    if inp.frost_bias and fcm.radiative(night):
        word = "colder" if inp.frost_bias == "earlier" else "warmer"
        return (f" You told us your yard frosts {inp.frost_bias} than the neighbours, so on this "
                f"clear, calm night we count it {fcm.BIAS_F} {DEGREE} {word}.")
    return ""


def _seen(inp: Inputs, year: int, etype: str) -> Optional[OwnerState]:
    """A cold night seen in the forecast for this event or a colder one.
    A hard freeze arriving first satisfies the earlier ones."""
    best = None
    for t in FALL_TYPES:
        if TYPE_RANK[t] < TYPE_RANK[etype]:
            continue
        st = inp.states.get(event_key(t, year, "fall"))
        if st and st.status == "seen_in_forecast" and st.observed_on and st.observed_on < inp.today:
            if best is None or st.observed_on < best.observed_on:
                best = st
    return best


def _owner_happened_colder(inp: Inputs, year: int, etype: str) -> Optional[OwnerState]:
    for t in FALL_TYPES:
        if TYPE_RANK[t] > TYPE_RANK[etype]:
            st = inp.states.get(event_key(t, year, "fall"))
            if st and st.status == "happened":
                return st
    return None


def frost_event(inp: Inputs, etype: str, year: int, *, use_forecast: bool,
                aud: Audience) -> Optional[SeasonEvent]:
    n = inp.normals
    t = THRESHOLD[etype]
    key = event_key(etype, year, "fall")
    title = NAMES[etype].capitalize()
    owner = _owner(inp, key)
    ready = n.get("status") == "ready"
    sources: list[dict] = []
    p = n["fall"][t] if ready else {"p10": None, "p50": None, "p90": None}
    p10, p50, p90 = (nm.fall_date(p[k], year) for k in ("p10", "p50", "p90"))
    occ = (n.get("occurs_pct") or {}).get(t) if ready else None
    if ready:
        sources.append(_normals_source(n))
    typical = nm.typical_text(n, "fall", t) if ready and p50 else ""
    window = EventWindow(start=p10, end=p90,
                         text=(f"Typically {typical}. As early as {nm.day_text(p10)} in one year in ten, "
                               f"and by {nm.day_text(p90)} in nine years in ten.")
                         if p50 and p10 and p90 else
                         (f"Typically {typical}." if p50 else "No typical date for this place."))
    sort_date = p50
    defn = DEFINITIONS[etype]
    why_typical = (f"Your typical {NAMES[etype]} ({defn}) is {typical}, from station normals."
                   if p50 else f"There is no typical date for the {NAMES[etype]} here.")
    conf = n.get("confidence", "not_known_yet") if p50 else "not_known_yet"

    status: str
    expl: Explained
    over = _owner_override(owner, title)
    colder = _owner_happened_colder(inp, year, etype)
    seen = None if (owner and owner.status == "not_yet") else _seen(inp, year, etype)
    hit = _forecast_hit(inp, float(t)) if use_forecast else None
    if over:
        status, expl = over
    elif colder and not (owner and owner.status == "not_yet"):
        status = "happened"
        expl = _explained(f"{title}: happened. You told us a colder night already came"
                          + (f" on {nm.day_text(colder.observed_on)}." if colder.observed_on else "."),
                          "you_told_us", "A colder night also counts as this one.",
                          [OWNER_SOURCE], "owner")
    elif seen is not None:
        status = "happened"
        sort_date = seen.observed_on
        expl = _explained(
            f"{title}: the National Weather Service forecast a "
            f"{'hard freeze' if seen.band == 'hard_freeze' else seen.band or 'cold night'} for your area "
            f"on the night of {nm.day_text(seen.observed_on)}. Not measured at your place.",
            "rough_estimate",
            "This comes from the forecast for that night, read while it was current. We have no "
            "measured low for your yard. Didn't happen at your place? Tell us and we will keep watching.",
            [fcm.NWS_SOURCE] + sources, "modelled")
    elif hit is not None:
        night, adj, lead = hit
        status = "forecast"
        sort_date = night.date
        conf_f = _forecast_conf(inp.forecast, night, adj, lead)
        when = "tonight" if lead == 0 else f"on the night of {_weekday(night.date)} {nm.day_text(night.date)}"
        yard = (f" (about {round(adj)} {DEGREE} for your yard)"
                if round(adj) != round(night.low_f) else "")
        window = EventWindow(start=night.date, end=night.date,
                             text=f"Low near {round(night.low_f)} {DEGREE}{yard} {when}; "
                                  f"{_range_text(adj, lead)}.")
        expl = _explained(
            f"{title} forecast {when}: low near {round(night.low_f)} {DEGREE}{yard}.",
            conf_f,
            f"Why: forecast low of {round(night.low_f)} {DEGREE} {when}, the {NAMES[etype]} of the season "
            f"if it comes.{_bias_note(inp, night)} {why_typical} A forecast is not a measurement "
            f"for your yard.",
            [_forecast_source(inp.forecast)] + sources, "modelled")
    elif not p50 or (occ is not None and occ < 50):
        status = "not_needed"
        sort_date = None
        expl = _explained(
            f"{title}: not expected most years here.",
            conf if p50 else "rough_estimate",
            (f"At the nearest station this happens in only about {round(occ / 10)} years in ten."
             if occ is not None else "The nearest station has no date for it.")
            + " If it does come, the forecast will show it.",
            sources or [nm.SOURCE], "public_map")
    elif inp.today > p90:
        status = "typically_around"
        expl = _explained(
            f"Most years the {NAMES[etype]} has come by now; it is typically {typical}. "
            "We have no measurement for your place, so tell us if it happened.",
            conf, why_typical + " We do not yet read measured lows for your area.",
            sources, "public_map")
    elif p10 <= inp.today <= p90:
        status = "expected"
        expl = _explained(
            f"{title} could come any night now: typically {typical}.", conf,
            why_typical + " Nothing that cold is in this week's forecast yet.", sources, "public_map")
    else:
        status = "typically_around"
        expl = _explained(f"Typical {NAMES[etype]} here: {typical}.", conf, why_typical,
                          sources, "public_map")
    if occ is not None and 50 <= occ < 90 and status not in ("happened", "done", "not_needed"):
        window = EventWindow(start=window.start, end=window.end,
                             text=window.text + f" It does not come every year (about {round(occ / 10)} years in ten).")

    tstate = _task_state(status)
    tasks: list[SeasonTask] = []
    if status != "not_needed":
        why = expl.reason.split(" A forecast is not")[0]
        data = sources + ([_forecast_source(inp.forecast)] if status == "forecast" else [])
        if etype == "first_frost":
            if aud.beds:
                tasks.append(_task(key, "frost_tender", aud, ("garden_bed",), why, data, tstate))
            if aud.pots:
                tasks.append(_task(key, "frost_pots", aud, (), why, data, tstate))
            if aud.trees or aud.shrubs or aud.lawn:
                tasks.append(_task(key, "frost_info_woody", aud, ("tree", "shrub", "grass"), why, data, tstate))
        elif etype == "first_freeze":
            if aud.pots:
                tasks.append(_task(key, "frost_pots", aud, (), why, data, tstate))
            if aud.trees or aud.shrubs or not aud.known:
                tasks.append(_task(key, "freeze_water", aud, ("tree", "shrub"), why, data, tstate))
        elif etype == "hard_freeze":
            if aud.beds:
                tasks.append(_task(key, "hard_freeze_stems", aud, ("garden_bed",), why, data, tstate))
    return SeasonEvent(event_key=key, type=etype, title=title, status=status, window=window,
                       explained=expl, tasks=tasks,
                       owner_actions=_actions(status, owner, "frost"), sort_date=sort_date)


# --- fall hardening, leaf drop, dormancy -----------------------------------------------

def _leaf_window(n: dict, year: int):
    if n.get("status") != "ready":
        return None
    m36 = nm.fall_date(n["fall"]["36"]["p50"], year)
    m32 = nm.fall_date(n["fall"]["32"]["p50"], year)
    m28 = nm.fall_date(n["fall"]["28"]["p50"], year)
    if not (m36 and m32):
        return None
    opens = m36 - timedelta(days=rules.default("leaf_drop_open_days_before_median_frost"))
    cap = m32 + timedelta(days=rules.default("leaf_drop_close_max_days_after_median_freeze"))
    close = min(m28 + timedelta(days=rules.default("leaf_drop_close_days_after_median_hard_freeze")), cap) \
        if m28 else cap
    return opens, m32, close


def hardening_event(inp: Inputs, year: int, aud: Audience) -> SeasonEvent:
    n = inp.normals
    key = event_key("fall_hardening", year, "fall")
    title = "Fall hardening begins"
    hours = rules.default("fall_hardening_day_length_hours")
    lead = rules.default("fall_hardening_days_before_median_freeze")
    dl = first_day_shorter_than(inp.lat, hours, year)
    m32 = nm.fall_date(n["fall"]["32"]["p50"], year) if n.get("status") == "ready" else None
    fz = m32 - timedelta(days=lead) if m32 else None
    start = max(d for d in (dl, fz) if d) if (dl or fz) else None
    lw = _leaf_window(n, year)
    ends = _dormancy_date(n, year, lw)
    sources = [DAYLENGTH_SOURCE] + ([_normals_source(n)] if m32 else [])
    parts = []
    if dl:
        parts.append(f"day length here falls under {hours} hours on {nm.day_text(dl)}")
    if m32:
        parts.append(f"your typical first freeze ({nm.typical_text(n, 'fall', '32')}) is "
                     f"about six weeks after {nm.day_text(fz)}")
    why = ("Why: " + ", and ".join(parts) + ". The later of the two is used. Both rules are our "
           "engineering defaults from the extension habit of about six weeks before first frost.") \
        if parts else "Why: no day length or freeze date is known here."
    if not m32:
        why += " No station normals are close enough, so this uses day length alone."
    conf = _min_conf(n.get("confidence", "rough_estimate") if m32 else "rough_estimate", "area_estimate")
    owner = _owner(inp, key)
    over = _owner_override(owner, title)
    if not (aud.trees or aud.shrubs or aud.beds):
        status = "not_needed"
        expl = _explained(f"{title}: no trees, shrubs or garden beds on your lot.", "you_told_us",
                          "From your answer to \"What's on your lot?\" and your zones.",
                          [OWNER_SOURCE], "owner")
    elif over:
        status, expl = over
    elif start is None:
        status, expl = "typically_around", _explained(
            "Fall hardening: no typical date here.", "not_known_yet", why, sources, "modelled")
    elif inp.today < start:
        status = "typically_around"
        expl = _explained(f"Trees and shrubs start hardening for winter around {nm.day_text(start)}.",
                          conf, why, sources, "modelled")
    elif ends is None or inp.today < ends:
        status = "happening"
        expl = _explained(f"Trees and shrubs have been hardening for winter since about "
                          f"{nm.day_text(start)}.", conf, why, sources, "modelled")
    else:
        status = "happened"
        expl = _explained(f"Fall hardening began around {nm.day_text(start)} (estimate).",
                          conf, why, sources, "modelled")
    window = EventWindow(start=start, end=ends,
                         text=(f"Begins around {nm.day_text(start)} and lasts until trees and shrubs "
                               "are dormant.") if start else "No typical date for this place.")
    tstate = _task_state(status)
    tasks = []
    if status != "not_needed":
        tasks.append(_task(key, "hardening_no_feed", aud, ("tree", "shrub", "garden_bed"),
                           why, sources, tstate))
    if aud.trees or aud.shrubs:
        tasks.append(_task(key, "hardening_no_prune", aud, ("tree", "shrub"), why, sources, tstate))
    return SeasonEvent(event_key=key, type="fall_hardening", title=title, status=status,
                       window=window, explained=expl, tasks=tasks,
                       owner_actions=_actions(status, owner, "task"), sort_date=start)


def leaf_event(inp: Inputs, year: int, aud: Audience) -> SeasonEvent:
    n = inp.normals
    key = event_key("leaf_drop", year, "fall")
    title = "Leaf drop"
    lw = _leaf_window(n, year)
    owner = _owner(inp, key)
    sources = [_normals_source(n)] if lw else [nm.SOURCE]
    if lw:
        opens, peak, close = lw
        window = EventWindow(start=opens, end=close,
                             text=f"Usually between about {nm.day_text(opens)} and {nm.day_text(close)}, "
                                  f"most around {nm.day_text(peak)}. This is a window, not a date.")
        why = (f"Why: leaves usually fall here between about {nm.day_text(opens)} and "
               f"{nm.day_text(close)}, worked out from the typical frost and freeze dates. "
               "Fall leaf timing models miss by one to two weeks, so this is a window. "
               "The window rule is our engineering default.")
    else:
        opens = peak = close = None
        window = EventWindow(text="No typical window for this place.")
        why = "Why: no typical frost dates are known here, so there is no leaf-drop window."
    hard = inp.states.get(event_key("hard_freeze", year, "fall"))
    conf = "area_estimate" if (hard and hard.status == "happened") else "rough_estimate"
    over = _owner_override(owner, title)
    if not aud.deciduous:
        status = "not_needed"
        expl = _explained("Leaf drop: no trees or shrubs that drop leaves on your lot.",
                          "you_told_us", "From your answer to \"What's on your lot?\" and your zones.",
                          [OWNER_SOURCE], "owner")
    elif over:
        status, expl = over
        if status == "happened":
            expl = _explained("Leaves are falling (you told us).", "you_told_us",
                              "You marked leaf drop in the app.", [OWNER_SOURCE], "owner")
    elif not lw:
        status = "typically_around"
        expl = _explained("Leaf drop: no typical window here.", "not_known_yet", why, sources, "public_map")
    elif inp.today < opens:
        status = "typically_around"
        expl = _explained(f"Leaves usually start falling around {nm.day_text(opens)}.", conf, why,
                          sources, "public_map")
    elif inp.today <= close:
        status = "happening"
        expl = _explained(f"Leaves are probably coming down now (estimate; window "
                          f"{nm.day_text(opens)} to {nm.day_text(close)}).", conf, why, sources, "public_map")
    else:
        status = "happened"
        expl = _explained(f"Leaves are probably mostly down (estimate; window {nm.day_text(opens)} "
                          f"to {nm.day_text(close)}).", conf, why, sources, "public_map")
    tstate = _task_state(status)
    tasks = []
    if status != "not_needed":
        tasks.append(_task(key, "leaves_beds", aud, ("tree", "shrub", "garden_bed"), why, sources, tstate))
        if aud.lawn:
            tasks.append(_task(key, "leaves_lawn", aud, ("grass",), why, sources, tstate))
        if aud.paved or not aud.known:
            tasks.append(_task(key, "leaves_paths", aud, ("bare_hardscape",), why, sources, tstate))
    return SeasonEvent(event_key=key, type="leaf_drop", title=title, status=status, window=window,
                       explained=expl, tasks=tasks, owner_actions=_actions(status, owner, "leaf"),
                       sort_date=opens)


def _dormancy_date(n: dict, year: int, lw) -> Optional[date]:
    if n.get("status") != "ready":
        return None
    mean45 = (n.get("daily") or {}).get("fall_mean45")
    d45 = nm.fall_date(mean45, year) if mean45 else None
    close = lw[2] if lw else None
    if d45:
        return max(d for d in (d45, close) if d)
    return None


def dormancy_event(inp: Inputs, year: int, aud: Audience) -> SeasonEvent:
    n = inp.normals
    key = event_key("dormancy", year, "fall")
    owner = _owner(inp, key)
    lw = _leaf_window(n, year)
    d = _dormancy_date(n, year, lw)
    warm = n.get("status") == "ready" and not (n.get("daily") or {}).get("fall_mean45")
    title = "Winter rest" if warm else "Woody plants dormant"
    sources = [_normals_source(n)] if n.get("status") == "ready" else [nm.SOURCE]
    mean = rules.default("dormancy_normal_mean_f")
    if d:
        why = (f"Why: trees and shrubs go dormant once their leaves are down and the weather stays cold. "
               f"With no measured temperatures for your area yet, this uses the date the station's normal "
               f"daily mean falls to {mean} {DEGREE} ({nm.day_text(d)}), our engineering default.")
    elif warm:
        why = (f"Why: the station's normal daily mean never falls to {mean} {DEGREE} here, so many plants "
               "never go fully dormant. Growth slows for winter instead.")
    else:
        why = "Why: no station normals are close enough to date this."
    leaf = inp.states.get(event_key("leaf_drop", year, "fall"))
    hard = inp.states.get(event_key("hard_freeze", year, "fall"))
    over = _owner_override(owner, title)
    if not (aud.trees or aud.shrubs or not aud.known):
        status = "not_needed"
        expl = _explained(f"{title}: no trees or shrubs on your lot.", "you_told_us",
                          "From your answer to \"What's on your lot?\" and your zones.",
                          [OWNER_SOURCE], "owner")
    elif over:
        status, expl = over
    elif leaf and leaf.status == "happened" and hard and hard.status == "happened":
        status = "happened"
        expl = _explained(f"{title}: leaves are down and a hard freeze came (you told us).",
                          "area_estimate", "Both conditions for dormancy are met from your answers.",
                          [OWNER_SOURCE] + sources, "owner")
    elif d is None:
        status = "typically_around"
        expl = _explained("Growth slows for winter here; no dormancy date." if warm
                          else f"{title}: no typical date here.", "rough_estimate" if warm else "not_known_yet",
                          why, sources, "public_map")
    elif inp.today >= d:
        status = "happened"
        expl = _explained(f"Trees and shrubs are probably dormant now (estimate, since about "
                          f"{nm.day_text(d)}).", "rough_estimate", why, sources, "public_map")
    else:
        status = "typically_around"
        expl = _explained(f"Trees and shrubs usually go dormant around {nm.day_text(d)} (estimate).",
                          "rough_estimate", why, sources, "public_map")
    window = EventWindow(start=d, end=None,
                         text=(f"Usually from about {nm.day_text(d)}." if d else
                               "Growth slows for winter; many plants here never go fully dormant."
                               if warm else "No typical date for this place."))
    tstate = _task_state(status)
    tasks = []
    if status != "not_needed":
        tasks.append(_task(key, "dormant_woody", aud, ("tree", "shrub"), why, sources, tstate))
    return SeasonEvent(event_key=key, type="dormancy", title=title, status=status, window=window,
                       explained=expl, tasks=tasks, owner_actions=_actions(status, owner, "state"),
                       sort_date=d)


# --- spring --------------------------------------------------------------------------

def _spring(n: dict, t: str, p: str, year: int) -> Optional[date]:
    if n.get("status") != "ready":
        return None
    return nm.spring_date(n["spring"][t][p], year)


def _daily(n: dict, k: str, year: int) -> Optional[date]:
    v = (n.get("daily") or {}).get(k) if n.get("status") == "ready" else None
    return nm.spring_date(v, year) if v else None


def emergence_event(inp: Inputs, year: int, aud: Audience) -> SeasonEvent:
    n = inp.normals
    key = event_key("spring_emergence", year, "spring")
    title = "Spring growth starts"
    owner = _owner(inp, key)
    d = _daily(n, "first_leaf", year)
    sources = [STANDIN_SOURCE] + ([_normals_source(n)] if n.get("status") == "ready" else [nm.SOURCE])
    why = ("Why: the USA National Phenology Network Spring Index cannot be read by this version, so this "
           "date is our estimate from normal temperatures at the nearest station, matched to the Spring "
           "Index first-leaf date at two test places. It can be a week or more off in a given year.")
    over = _owner_override(owner, title)
    if over:
        status, expl = over
    elif d is None:
        status = "typically_around"
        expl = _explained("Spring growth: no typical date here.", "not_known_yet", why, sources, "modelled")
    elif inp.today >= d:
        status = "happened"
        expl = _explained(f"Spring growth has probably started (estimate, typically around "
                          f"{nm.day_text(d)}).", "rough_estimate", why, sources, "modelled")
    else:
        status = "expected" if (d - inp.today).days <= 7 else "typically_around"
        expl = _explained(f"Spring growth typically starts around {nm.day_text(d)} (estimate).",
                          "rough_estimate", why, sources, "modelled")
    window = EventWindow(start=d, end=None,
                         text=f"Typically around {nm.day_text(d)} (estimate)." if d else "No typical date.")
    tstate = _task_state(status)
    tasks = [_task(key, "emergence_beds", aud, ("garden_bed",), why, sources, tstate)] \
        if (aud.beds and status != "not_needed") else []
    return SeasonEvent(event_key=key, type="spring_emergence", title=title, status=status,
                       window=window, explained=expl, tasks=tasks,
                       owner_actions=_actions(status, owner, "state"), sort_date=d)


def last_frost_event(inp: Inputs, year: int, aud: Audience, *, use_forecast: bool) -> SeasonEvent:
    n = inp.normals
    key = event_key("last_frost", year, "spring")
    title = "Last spring freeze"
    owner = _owner(inp, key)
    p90, p50, p10 = (_spring(n, "32", p, year) for p in ("p90", "p50", "p10"))
    occ = (n.get("occurs_pct") or {}).get("32") if n.get("status") == "ready" else None
    sources = [_normals_source(n)] if p50 else [nm.SOURCE]
    typical = nm.typical_text(n, "spring", "32") if p50 else ""
    conf = n.get("confidence", "rough_estimate") if p50 else "not_known_yet"
    why = (f"Why: your typical last freeze (a night at or below 32 {DEGREE}) is {typical}. One year in "
           f"ten still has a freeze after {nm.day_text(p10)}, so frost can still come until then."
           if p50 and p10 else "Why: there is no typical last-freeze date here.")
    emerge = _daily(n, "first_leaf", year)
    hit = _forecast_hit(inp, 36.0, after=emerge) if (use_forecast and inp.today.month < 7) else None
    over = _owner_override(owner, title)
    window = EventWindow(start=p90, end=p10,
                         text=(f"Typically {typical}. Frost is still possible until about "
                               f"{nm.day_text(p10)}: one year in ten has a freeze after that.")
                         if p50 and p10 else "No typical date for this place.")
    sort_date = p50
    if over:
        status, expl = over
    elif hit:
        night, adj, lead = hit
        status = "forecast"
        sort_date = night.date
        when = "tonight" if lead == 0 else f"on the night of {_weekday(night.date)} {nm.day_text(night.date)}"
        window = EventWindow(start=night.date, end=night.date,
                             text=f"Low near {round(night.low_f)} {DEGREE} {when}; {_range_text(adj, lead)}.")
        expl = _explained(f"Late frost forecast {when}: low near {round(night.low_f)} {DEGREE}.",
                          _forecast_conf(inp.forecast, night, adj, lead),
                          f"Why: forecast low of {round(night.low_f)} {DEGREE} {when}, after spring growth "
                          f"has started.{_bias_note(inp, night)} {why[5:]}",
                          [_forecast_source(inp.forecast)] + sources, "modelled")
    elif not p50 or (occ is not None and occ < 50):
        status = "not_needed"
        sort_date = None
        expl = _explained("Spring freeze: not expected most years here.", "rough_estimate",
                          "The nearest station rarely records a freeze.", sources, "public_map")
    elif inp.today < p90:
        status = "typically_around"
        expl = _explained(f"Typical last freeze here: {typical}.", conf, why, sources, "public_map")
    elif inp.today <= p10:
        status = "expected"
        expl = _explained(f"Frost is still possible until about {nm.day_text(p10)}.", conf, why,
                          sources, "public_map")
    else:
        status = "typically_around"
        expl = _explained(f"Past the date after which only one year in ten has a freeze "
                          f"({nm.day_text(p10)}).", conf, why, sources, "public_map")
    tstate = _task_state(status)
    tasks = []
    if status != "not_needed":
        if aud.beds or aud.pots:
            tasks.append(_task(key, "late_frost_cover", aud, ("garden_bed",), why, sources, tstate))
    return SeasonEvent(event_key=key, type="last_frost", title=title, status=status, window=window,
                       explained=expl, tasks=tasks, owner_actions=_actions(status, owner, "frost"),
                       sort_date=sort_date)


def tender_out_event(inp: Inputs, year: int, aud: Audience, *, use_forecast: bool) -> SeasonEvent:
    n = inp.normals
    key = event_key("tender_plants_out", year, "spring")
    title = "Tender plants back outside"
    owner = _owner(inp, key)
    low50 = _daily(n, "spring_low50", year)
    p10 = _spring(n, "32", "p10", year)
    d = max(x for x in (low50, p10) if x) if (low50 or p10) else None
    lim = rules.default("tender_plants_out_normal_low_f")
    sources = [_normals_source(n)] if d else [nm.SOURCE]
    why = (f"Why: the station's normal low reaches {lim} {DEGREE} around {nm.day_text(low50)}"
           if low50 else "Why: no normal-low date is known here")
    why += (f", and one year in ten still freezes after {nm.day_text(p10)}. The later date is used."
            if p10 else ".")
    over = _owner_override(owner, title)
    warm_week = False
    fc = inp.forecast
    if use_forecast and fc and d and inp.today >= (p10 or d):
        lows = [x.low_f for x in fc.nights if x.low_f is not None]
        warm_week = len(lows) >= 7 and min(lows) >= lim
    if not (aud.pots or not aud.known):
        status = "not_needed"
        expl = _explained(f"{title}: no potted plants on your lot.", "you_told_us",
                          "From your answer to \"What's on your lot?\".", [OWNER_SOURCE], "owner")
    elif over:
        status, expl = over
    elif warm_week:
        status = "forecast"
        expl = _explained(f"Every night this week is forecast at or above {lim} {DEGREE}.",
                          "area_estimate", why + " The seven-night forecast agrees.",
                          [_forecast_source(fc)] + sources, "modelled")
    elif d is None:
        status = "typically_around"
        expl = _explained(f"{title}: no typical date here.", "not_known_yet", why, sources, "public_map")
    elif inp.today < d:
        status = "typically_around"
        expl = _explained(f"Tender potted plants can usually go back out around {nm.day_text(d)}.",
                          n.get("confidence", "rough_estimate"), why, sources, "public_map")
    else:
        status = "expected"
        expl = _explained(f"Nights are usually mild enough now (since about {nm.day_text(d)}). "
                          "Check the week's forecast first.", n.get("confidence", "rough_estimate"),
                          why, sources, "public_map")
    window = EventWindow(start=d, end=None,
                         text=f"Usually from about {nm.day_text(d)}." if d else "No typical date.")
    tstate = _task_state(status)
    tasks = [_task(key, "tender_out", aud, (), why, sources, tstate)] if status != "not_needed" else []
    return SeasonEvent(event_key=key, type="tender_plants_out", title=title, status=status,
                       window=window, explained=expl, tasks=tasks,
                       owner_actions=_actions(status, owner, "task"), sort_date=d)


def cleanup_event(inp: Inputs, year: int, aud: Audience) -> SeasonEvent:
    n = inp.normals
    key = event_key("spring_cleanup", year, "spring")
    title = "Spring cleanup window"
    owner = _owner(inp, key)
    p10 = _spring(n, "32", "p10", year)
    bloom = _daily(n, "first_bloom", year)
    d = max(x for x in (p10, bloom) if x) if (p10 or bloom) else None
    sources = [_normals_source(n), STANDIN_SOURCE] if d else [nm.SOURCE]
    why = ("Why: cleanup waits until late spring, when the one-year-in-ten freeze date"
           + (f" ({nm.day_text(p10)})" if p10 else "") + " and the typical first bloom"
           + (f" (about {nm.day_text(bloom)}, our estimate)" if bloom else "") + " have both passed.")
    over = _owner_override(owner, title)
    if not (aud.beds or not aud.known):
        status = "not_needed"
        expl = _explained(f"{title}: no garden beds on your lot.", "you_told_us",
                          "From your answer to \"What's on your lot?\" and your zones.",
                          [OWNER_SOURCE], "owner")
    elif over:
        status, expl = over
    elif d is None:
        status = "typically_around"
        expl = _explained(f"{title}: no typical date here.", "not_known_yet", why, sources, "public_map")
    elif inp.today < d:
        status = "typically_around"
        expl = _explained(f"Hold off on cutting back beds until about {nm.day_text(d)}.",
                          "rough_estimate", why, sources, "modelled")
    else:
        status = "happening"
        expl = _explained(f"The cleanup window is open (since about {nm.day_text(d)}).",
                          "rough_estimate", why, sources, "modelled")
    window = EventWindow(start=d, end=None,
                         text=f"Opens around {nm.day_text(d)}." if d else "No typical date.")
    tstate = _task_state(status)
    tasks = [_task(key, "cleanup_stems", aud, ("garden_bed",), why, sources, tstate)] \
        if status != "not_needed" else []
    return SeasonEvent(event_key=key, type="spring_cleanup", title=title, status=status,
                       window=window, explained=expl, tasks=tasks,
                       owner_actions=_actions(status, owner, "task"), sort_date=d)


# --- the whole season ---------------------------------------------------------------

def season_events(inp: Inputs, year: int, *, use_forecast: bool) -> list[SeasonEvent]:
    aud = audience(inp)
    out = [hardening_event(inp, year, aud), leaf_event(inp, year, aud)]
    for t in FALL_TYPES:
        e = frost_event(inp, t, year, use_forecast=use_forecast, aud=aud)
        if e:
            out.append(e)
    out += [dormancy_event(inp, year, aud), emergence_event(inp, year, aud),
            last_frost_event(inp, year, aud, use_forecast=use_forecast),
            tender_out_event(inp, year, aud, use_forecast=use_forecast),
            cleanup_event(inp, year, aud)]
    return out


def plan_events(inp: Inputs) -> list[SeasonEvent]:
    """The current season in full, then the next season's events that fall
    within twelve months of today, ordered by date (undated last)."""
    s = season_year(inp.today)
    events = season_events(inp, s, use_forecast=True)
    horizon = inp.today + timedelta(days=365)
    events += [e for e in season_events(inp, s + 1, use_forecast=False)
               if e.sort_date is not None and e.sort_date <= horizon]
    far = date.max
    events.sort(key=lambda e: (e.sort_date or far, e.event_key))
    return events


def season_label(today: date) -> str:
    """"Late fall 2026", "Mid winter 2027": meteorological seasons, in thirds."""
    m = today.month
    name = ("winter", "spring", "summer", "fall")[(m % 12) // 3]
    part = ("Early", "Mid", "Late")[(m % 12) % 3]
    return f"{part} {name} {today.year}"
