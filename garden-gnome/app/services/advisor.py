"""Care advice service.

This module is the ONLY place that talks to an LLM. The rest of the app calls
`get_care_advice(species, plant, recent_logs, care_schedules)` and gets back a
string. Swapping providers (stub -> ollama -> anthropic) is a config change
here, nothing else.

Core principle: the species row + care schedules are authoritative ground truth.
The model INTERPRETS those facts for the specific plant; it does not invent care
knowledge. The prompt enforces this.

Backend is chosen by the ADVISOR_BACKEND environment variable:
    stub      - no model; returns deterministic advice from the data (default)
    ollama    - local model via Ollama's HTTP API (free, private)
    anthropic - Claude API (cloud, paid)
"""
from __future__ import annotations

import os
from datetime import datetime, timezone

from app.models.models import Species, Plant, CareLog, CareSchedule, CareType


BACKEND = os.getenv("ADVISOR_BACKEND", "stub").lower()
# Backend used when the owner reports free-text symptoms (which the stub
# cannot diagnose). Defaults to the base backend, so setting only
# ADVISOR_SYMPTOMS_BACKEND=anthropic gives cheap deterministic advice for
# routine checks and an LLM for actual diagnosis.
SYMPTOMS_BACKEND = os.getenv("ADVISOR_SYMPTOMS_BACKEND", BACKEND).lower()
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")


SYSTEM_INSTRUCTION = (
    "You are a careful houseplant care assistant. You are given authoritative "
    "care facts and care schedules for a plant's species and that specific "
    "plant's recent care history. Advise the owner on what to do now. Base "
    "every recommendation ONLY on the facts provided. Do not invent care "
    "requirements that are not grounded in the data. If the owner reports "
    "symptoms, diagnose them using only the provided species facts and care "
    "history -- do not guess at causes the data doesn't support. If the data "
    "is insufficient to answer something, say so plainly. Keep advice "
    "concise, specific, and friendly."
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


def _build_prompt(
    species: Species,
    plant: Plant,
    recent_logs: list[CareLog],
    care_schedules: list[CareSchedule],
    symptoms: str = "",
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
            note = f" ({log.notes})" if log.notes else ""
            lines.append(f"- {log.action.value}, {ago}{note}")
        history = "\nRECENT CARE HISTORY (newest first):\n" + "\n".join(lines) + "\n"
    else:
        history = "\nRECENT CARE HISTORY: none logged yet.\n"

    if symptoms.strip():
        symptoms_block = f"\nOWNER-REPORTED SYMPTOMS:\n{symptoms.strip()}\n"
        question = (
            "\nDiagnose the reported symptoms using only the facts above and "
            "explain the most likely cause(s) and what to do. Then cover any "
            "other care types that have a schedule and are due, mentioning "
            "timing specifically."
        )
    else:
        symptoms_block = ""
        question = (
            "\nGiven only the above, what should the owner do for this plant now? "
            "Cover each care type that has a schedule, mentioning timing specifically."
        )
    return facts + schedules_block + this_plant + history + symptoms_block + question


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


def _advise_stub(
    species: Species,
    plant: Plant,
    recent_logs: list[CareLog],
    care_schedules: list[CareSchedule],
    symptoms: str = "",
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

    if species.toxic_to_pets:
        lines.append(f"⚠️ {species.common_name} is toxic to pets.")

    if symptoms.strip():
        lines.append(
            f"🔍 You reported: “{symptoms.strip()}”. Symptom diagnosis needs "
            f"the AI advisor, which isn't enabled yet — these schedule-based "
            f"tips are the best I can do for now."
        )

    return "\n".join(lines)


def _advise_ollama(
    species: Species,
    plant: Plant,
    recent_logs: list[CareLog],
    care_schedules: list[CareSchedule],
    symptoms: str = "",
) -> str:
    import httpx

    prompt = _build_prompt(species, plant, recent_logs, care_schedules, symptoms)
    try:
        resp = httpx.post(
            f"{OLLAMA_HOST}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_INSTRUCTION},
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
            },
            timeout=120.0,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["message"]["content"].strip()
    except httpx.HTTPError as e:
        raise RuntimeError(
            f"Ollama request failed ({e}). Is `ollama serve` running and has "
            f"'{OLLAMA_MODEL}' been pulled?"
        ) from e


def _advise_anthropic(
    species: Species,
    plant: Plant,
    recent_logs: list[CareLog],
    care_schedules: list[CareSchedule],
    symptoms: str = "",
) -> str:
    import anthropic

    prompt = _build_prompt(species, plant, recent_logs, care_schedules, symptoms)
    try:
        client = anthropic.Anthropic()
        message = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=400,
            system=SYSTEM_INSTRUCTION,
            messages=[{"role": "user", "content": prompt}],
        )
    except anthropic.APIError as e:
        raise RuntimeError(
            f"Anthropic request failed ({e}). Check ANTHROPIC_API_KEY in .env."
        ) from e
    except Exception as e:  # missing key raises at client construction
        raise RuntimeError(
            f"Anthropic client error ({e}). Is ANTHROPIC_API_KEY set in .env?"
        ) from e
    usage = message.usage
    print(f"[advisor] anthropic tokens in={usage.input_tokens} out={usage.output_tokens}")
    return "".join(block.text for block in message.content if block.type == "text").strip()


_BACKENDS = {
    "stub": _advise_stub,
    "ollama": _advise_ollama,
    "anthropic": _advise_anthropic,
}


def get_care_advice(
    species: Species,
    plant: Plant,
    recent_logs: list[CareLog],
    care_schedules: list[CareSchedule],
    symptoms: str = "",
) -> dict:
    backend = SYMPTOMS_BACKEND if symptoms.strip() else BACKEND
    fn = _BACKENDS.get(backend, _advise_stub)
    advice = fn(species, plant, recent_logs, care_schedules, symptoms)
    return {"backend": backend, "advice": advice}
