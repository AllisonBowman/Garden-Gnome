"""Care advice service.

This module is the ONLY place that talks to an LLM. The rest of the app calls
`get_care_advice(species, plant, recent_logs, care_schedules)` and gets back a
string. Swapping providers (stub -> anthropic) is a config change
here, nothing else.

Core principle: the species row + care schedules are authoritative ground truth.
The model INTERPRETS those facts for the specific plant; it does not invent care
knowledge. The prompt enforces this.

Backend is chosen by the ADVISOR_BACKEND environment variable:
    stub      - no model; returns deterministic advice from the data (default)
    anthropic - Claude API (cloud, paid)
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

from app.models.models import (
    Species, Plant, CareLog, CareSchedule, CareType, Environment,
    Shelter, TempExposure, SunExposure,
)

logger = logging.getLogger("plantadvocate.advisor")

# The one user-facing failure message, mirroring vision.UNAVAILABLE_MESSAGE.
# Deliberately free of setup instructions, env var names, and tool names --
# those go to the log.
UNAVAILABLE_MESSAGE = (
    "The Gnome couldn't put together advice just now — the care engine didn't "
    "respond. Please try again in a few minutes."
)

# Prefix the diagnose route uses when it files a photo diagnosis to a plant's
# timeline. _build_prompt recognizes it so model output never re-enters a
# prompt disguised as owner-recorded history.
PHOTO_DIAGNOSIS_PREFIX = "Photo diagnosis: "


class AdvisorUnavailable(RuntimeError):
    """The configured advisor backend cannot serve requests right now.

    str(exc) is user-presentable; the technical cause is already logged."""


BACKEND = os.getenv("ADVISOR_BACKEND", "stub").lower()
# Backend used when the owner reports free-text symptoms (which the stub
# cannot diagnose). Defaults to the base backend, so setting only
# ADVISOR_SYMPTOMS_BACKEND=anthropic gives cheap deterministic advice for
# routine checks and an LLM for actual diagnosis.
SYMPTOMS_BACKEND = os.getenv("ADVISOR_SYMPTOMS_BACKEND", BACKEND).lower()
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")


SYSTEM_INSTRUCTION = (
    "You are a careful houseplant care assistant. You are given authoritative "
    "care facts and care schedules for a plant's species and that specific "
    "plant's recent care history. Advise the owner on what to do now. Base "
    "every recommendation ONLY on the facts provided. Do not invent care "
    "requirements that are not grounded in the data. If the owner reports "
    "symptoms, diagnose them using only the provided species facts and care "
    "history -- do not guess at causes the data doesn't support. If the data "
    "is insufficient to answer something, say so plainly. "
    "If a GROW ENVIRONMENT and LOCAL WEATHER are provided, treat the forecast "
    "as authoritative and translate the OUTSIDE conditions into what the plant "
    "actually experiences IN HERE, given how sheltered it is and whether it "
    "feels outdoor air: an exposed, outdoor plant feels the full forecast; a "
    "partially sheltered one feels a muted version; a fully sheltered indoor "
    "plant is barely affected. Turn that into concrete timing (e.g. skip a "
    "watering before heavy rain reaches an unsheltered plant, check sooner in a "
    "heat spike, protect from a cold snap or scorching UV). "
    "Keep advice concise, specific, and friendly."
)

_CARE_TYPE_LABELS = {
    CareType.water: "Watering",
    CareType.fertilize: "Fertilizing",
    CareType.mist: "Misting",
    CareType.prune: "Pruning",
    CareType.repot: "Repotting",
    CareType.rotate: "Rotating",
    CareType.clean: "Leaf cleaning",
    CareType.other: "Other",
}


def _days_since(when: datetime | None) -> int | None:
    if when is None:
        return None
    now = datetime.now(timezone.utc)
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return (now - when).days


def weather_applies(environment: Environment | None) -> bool:
    """Whether the outside world reaches this plant enough for weather to matter.

    A desk plant in a climate-controlled room (indoor + sheltered) is unaffected
    by the forecast, so weather grounding and nudges are skipped for it. This is
    the gate that scopes the feature to "plants outside of shelters." """
    if environment is None:
        return False
    return (
        environment.temp_exposure == TempExposure.outdoor
        or environment.shelter in (Shelter.partial, Shelter.exposed)
    )


_SHELTER_DESC = {
    Shelter.sheltered: "sheltered (roofed/indoors — rain and wind don't reach it)",
    Shelter.partial: "partial (covered balcony/porch — some rain and wind)",
    Shelter.exposed: "exposed (open to the sky — full rain and wind)",
}
_TEMP_EXPOSURE_DESC = {
    TempExposure.indoor: "indoor (climate-controlled, stable temperature)",
    TempExposure.outdoor: "outdoor (feels the outside air temperature)",
}


def _environment_block(environment: Environment) -> str:
    return (
        "\nGROW ENVIRONMENT (how much of the weather actually reaches this plant):\n"
        f"- Name: {environment.name}\n"
        f"- Shelter: {_SHELTER_DESC.get(environment.shelter, environment.shelter.value)}\n"
        f"- Temperature exposure: "
        f"{_TEMP_EXPOSURE_DESC.get(environment.temp_exposure, environment.temp_exposure.value)}\n"
        f"- Sun exposure: {environment.sun_exposure.value}\n"
    )


def _weather_block(weather: dict) -> str:
    cur = weather.get("current") or {}
    parts = []
    if cur.get("temp_f") is not None:
        parts.append(f"{cur['temp_f']}°F")
    if cur.get("humidity_pct") is not None:
        parts.append(f"humidity {cur['humidity_pct']}%")
    if cur.get("uv_index") is not None:
        parts.append(f"UV {cur['uv_index']}")
    if cur.get("condition"):
        parts.append(str(cur["condition"]))
    now_line = ", ".join(parts) if parts else "unavailable"

    lines = [
        "\nLOCAL WEATHER (Apple Weather — authoritative current conditions and forecast):",
        f"- Now: {now_line}",
    ]
    days = weather.get("daily") or []
    if days:
        lines.append("- Forecast:")
        for d in days:
            seg = []
            if d.get("high_f") is not None and d.get("low_f") is not None:
                seg.append(f"high {d['high_f']}°F / low {d['low_f']}°F")
            if d.get("precip_chance_pct") is not None:
                seg.append(f"rain {d['precip_chance_pct']}%")
            if d.get("uv_max") is not None:
                seg.append(f"UV up to {d['uv_max']}")
            if d.get("daylight_hours") is not None:
                seg.append(f"~{d['daylight_hours']}h daylight")
            lines.append(f"  - {d.get('date') or '?'}: {', '.join(seg)}")
    return "\n".join(lines) + "\n"


def _build_prompt(
    species: Species,
    plant: Plant,
    recent_logs: list[CareLog],
    care_schedules: list[CareSchedule],
    symptoms: str = "",
    environment: Environment | None = None,
    weather: dict | None = None,
) -> str:
    facts = (
        f"SPECIES CARE FACTS (authoritative):\n"
        f"- Common name: {species.common_name}\n"
        f"- Scientific name: {species.scientific_name}\n"
        f"- Light need: {species.light_need.value}\n"
        f"- Humidity: {species.humidity_pct_min}-{species.humidity_pct_max}%\n"
        f"- Temperature: {species.temp_f_min}-{species.temp_f_max} F\n"
        f"- Soil: {species.soil_type}\n"
        f"- Toxic to pets: {'yes' if species.toxic_to_pets else 'no'}\n"
        f"- Curated notes: {species.care_notes or '(none)'}\n"
    )

    if care_schedules:
        lines = []
        for cs in care_schedules:
            label = _CARE_TYPE_LABELS.get(cs.care_type, cs.care_type.value)
            note = f" — {cs.notes}" if cs.notes else ""
            lines.append(
                f"- {label}: every {cs.interval_days_min}-{cs.interval_days_max} days{note}"
            )
        schedules_block = "\nCARE SCHEDULES (authoritative):\n" + "\n".join(lines) + "\n"
    else:
        schedules_block = "\nCARE SCHEDULES: none defined.\n"

    this_plant = (
        f"\nTHIS PLANT:\n"
        f"- Nickname: {plant.nickname}\n"
        f"- Location: {plant.location or '(unspecified)'}\n"
        f"- Maturity: {plant.maturity_stage.value}\n"
    )

    if recent_logs:
        lines = []
        for log in recent_logs:
            d = _days_since(log.logged_at)
            ago = f"{d} days ago" if d is not None else "date unknown"
            raw_note = log.notes or ""
            if raw_note.startswith(PHOTO_DIAGNOSIS_PREFIX):
                # A filed photo diagnosis is model output. Inlining it verbatim
                # would feed the model its own words back as owner-recorded
                # history, compounding any earlier drift. Record that a
                # check-up happened; drop what it said.
                lines.append(f"- photo check-up filed, {ago}")
                continue
            note = f" ({raw_note})" if raw_note else ""
            lines.append(f"- {log.action.value}, {ago}{note}")
        history = "\nRECENT CARE HISTORY (newest first):\n" + "\n".join(lines) + "\n"
    else:
        history = "\nRECENT CARE HISTORY: none logged yet.\n"

    # Environment + weather only when the outside world reaches this plant and
    # we actually have a forecast; a desk plant's prompt is unchanged.
    if weather is not None and weather_applies(environment):
        env_weather = _environment_block(environment) + _weather_block(weather)
        weather_clause = (
            " Factor in the local weather and how much of it this plant's "
            "environment actually exposes it to."
        )
    else:
        env_weather = ""
        weather_clause = ""

    if symptoms.strip():
        symptoms_block = f"\nOWNER-REPORTED SYMPTOMS:\n{symptoms.strip()}\n"
        question = (
            "\nDiagnose the reported symptoms using only the facts above and "
            "explain the most likely cause(s) and what to do. Then cover any "
            "other care types that have a schedule and are due, mentioning "
            "timing specifically." + weather_clause
        )
    else:
        symptoms_block = ""
        question = (
            "\nGiven only the above, what should the owner do for this plant now? "
            "Cover each care type that has a schedule, mentioning timing "
            "specifically." + weather_clause
        )
    return facts + schedules_block + this_plant + env_weather + history + symptoms_block + question


_CARE_TYPE_EMOJI = {
    CareType.water: "💧",
    CareType.fertilize: "🌿",
    CareType.mist: "💨",
    CareType.prune: "✂️",
    CareType.repot: "🪴",
    CareType.rotate: "🔄",
    CareType.clean: "🧽",
    CareType.other: "📝",
}


def _weather_nudges(
    species: Species,
    environment: Environment | None,
    weather: dict | None,
) -> list[str]:
    """Deterministic, conservative forecast nudges for plants the weather
    reaches. One line per applicable signal; each is gated by the physical
    reality of the environment (rain only matters where the sky reaches, heat
    and cold only where the plant feels outdoor air, UV only in open sun)."""
    if environment is None or weather is None:
        return []

    days = weather.get("daily") or []
    current = weather.get("current") or {}
    unsheltered = environment.shelter in (Shelter.partial, Shelter.exposed)
    outdoor = environment.temp_exposure == TempExposure.outdoor
    open_sun = unsheltered and environment.sun_exposure != SunExposure.shade

    nudges: list[str] = []

    # Rain reaching an unsheltered plant → let the sky do the watering.
    if unsheltered:
        wet = next((d for d in days if (d.get("precip_chance_pct") or 0) >= 60), None)
        if wet:
            nudges.append(
                f"🌧️ Rain likely ({wet['precip_chance_pct']}% on {wet['date']}) — "
                f"hold off watering; the sky may do it for you."
            )

    # Heat spike above the species' comfort ceiling for an outdoor plant.
    if outdoor and species.temp_f_max is not None:
        hot = next(
            (d for d in days if d.get("high_f") is not None and d["high_f"] > species.temp_f_max),
            None,
        )
        if hot:
            nudges.append(
                f"🔥 Heat ahead (high {hot['high_f']}°F on {hot['date']}, above its "
                f"{species.temp_f_max}°F comfort ceiling) — check soil sooner and add shade or water."
            )

    # Cold snap below the comfort floor for an outdoor plant.
    if outdoor and species.temp_f_min is not None:
        cold = next(
            (d for d in days if d.get("low_f") is not None and d["low_f"] < species.temp_f_min),
            None,
        )
        if cold:
            nudges.append(
                f"❄️ Cold night ahead (low {cold['low_f']}°F on {cold['date']}, below its "
                f"{species.temp_f_min}°F comfort floor) — bring it in or shelter it."
            )

    # Very high UV reaching a plant that's open to the sky and not in shade.
    if open_sun:
        uv_vals = [current.get("uv_index")] + [d.get("uv_max") for d in days]
        peak = max((u for u in uv_vals if isinstance(u, (int, float))), default=None)
        if peak is not None and peak >= 8:
            nudges.append(
                f"☀️ Very high UV (up to {peak}) — even sun-lovers can scorch; "
                f"a little midday shade helps."
            )

    return nudges


def _advise_stub(
    species: Species,
    plant: Plant,
    recent_logs: list[CareLog],
    care_schedules: list[CareSchedule],
    symptoms: str = "",
    environment: Environment | None = None,
    weather: dict | None = None,
) -> str:
    # One line per care type; the client renders each line as its own row.
    lines = []
    for cs in care_schedules:
        label = _CARE_TYPE_LABELS.get(cs.care_type, cs.care_type.value)
        emoji = _CARE_TYPE_EMOJI.get(cs.care_type, "🪴")
        last_log = next(
            (log for log in recent_logs if log.action == cs.care_type),
            None,
        )
        days = _days_since(last_log.logged_at) if last_log else None

        if days is None:
            lines.append(
                f"{emoji} {label}: no log yet — recommended every "
                f"{cs.interval_days_min}–{cs.interval_days_max} days."
            )
        elif days < cs.interval_days_min:
            lines.append(
                f"{emoji} {label}: done {days} day{'s' if days != 1 else ''} ago. "
                f"Next window opens in {cs.interval_days_min - days} "
                f"day{'s' if cs.interval_days_min - days != 1 else ''} — hold off."
            )
        elif days <= cs.interval_days_max:
            lines.append(
                f"{emoji} {label}: done {days} days ago, inside the "
                f"{cs.interval_days_min}–{cs.interval_days_max} day window. "
                f"Check and do if needed."
            )
        else:
            lines.append(
                f"{emoji} {label}: done {days} days ago — past the "
                f"{cs.interval_days_max} day mark. Likely due."
            )

    if not lines:
        lines.append("No care schedules defined for this species yet.")

    # Weather-driven nudges for plants the forecast actually reaches.
    lines.extend(_weather_nudges(species, environment, weather))

    if species.toxic_to_pets:
        lines.append(f"⚠️ {species.common_name} is toxic to pets.")

    if symptoms.strip():
        # "AI advisor" violates the handoff rebrand rule ("care engine", never
        # "AI", and the gnome is the voice the caretaker hears).
        lines.append(
            f"🔍 You noted: “{symptoms.strip()}”. The Gnome can't read symptoms "
            f"yet — these schedule-based tips are the best he can offer for now."
        )

    return "\n".join(lines)


def _advise_anthropic(
    species: Species,
    plant: Plant,
    recent_logs: list[CareLog],
    care_schedules: list[CareSchedule],
    symptoms: str = "",
    environment: Environment | None = None,
    weather: dict | None = None,
) -> str:
    import anthropic

    prompt = _build_prompt(
        species, plant, recent_logs, care_schedules, symptoms, environment, weather
    )
    try:
        client = anthropic.Anthropic()
        message = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=400,
            system=SYSTEM_INSTRUCTION,
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.APIError as e:
        logger.error("Anthropic advice failed: %s", e)
        raise AdvisorUnavailable(UNAVAILABLE_MESSAGE) from e
    except Exception as e:  # missing key raises at client construction
        logger.error(
            "Anthropic client error (%s). Is ANTHROPIC_API_KEY set in .env?", e
        )
        raise AdvisorUnavailable(UNAVAILABLE_MESSAGE) from e
    usage = message.usage
    logger.info(
        "Anthropic advice tokens in=%d out=%d", usage.input_tokens, usage.output_tokens
    )
    return "".join(block.text for block in message.content if block.type == "text").strip()


_BACKENDS = {
    "stub": _advise_stub,
    "anthropic": _advise_anthropic,
}


def get_care_advice(
    species: Species,
    plant: Plant,
    recent_logs: list[CareLog],
    care_schedules: list[CareSchedule],
    symptoms: str = "",
    environment: Environment | None = None,
    weather: dict | None = None,
) -> dict:
    backend = SYMPTOMS_BACKEND if symptoms.strip() else BACKEND
    fn = _BACKENDS.get(backend, _advise_stub)
    advice = fn(species, plant, recent_logs, care_schedules, symptoms, environment, weather)
    return {"backend": backend, "advice": advice}
