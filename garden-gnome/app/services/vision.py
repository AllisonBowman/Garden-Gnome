"""Photo diagnosis service (Phase 3).

This module is the ONLY place that talks to a vision model. Mirrors
app/services/advisor.py's backend-swap pattern: the rest of the app calls
`diagnose_photo(...)` and gets back a dict, swapping backends is a config
change here, nothing else.

Backend is chosen by the VISION_BACKEND environment variable:
    stub   - no model; returns a placeholder explaining how to enable it (default)
    ollama - local vision-capable model via Ollama (free, private, self-hosted)

Licensing note: the default Ollama model is `moondream` (Apache 2.0), chosen
specifically because it is free for unrestricted commercial use at any scale
-- no licensing fee ever, regardless of how the app grows. Other Apache-2.0
vision models (e.g. qwen2.5vl, minicpm-v) are drop-in alternatives via
OLLAMA_VISION_MODEL if more accuracy is needed. Avoid LLaMA-derived vision
models (llava, llama3.2-vision) for this project: their weights carry Meta's
custom community license, which has commercial-use conditions rather than
being unconditionally free like Apache 2.0/MIT.

Core principle (same as advisor.py): the species row + care schedules are
authoritative ground truth. The model describes what it observes in the photo
and reasons about likely causes using ONLY the provided care facts -- it does
not invent diagnoses unsupported by the image or the data.
"""
from __future__ import annotations

import base64
import os

from app.models.models import Species, Plant, CareSchedule


BACKEND = os.getenv("VISION_BACKEND", "stub").lower()
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_VISION_MODEL = os.getenv("OLLAMA_VISION_MODEL", "moondream")


SYSTEM_INSTRUCTION = (
    "You are a careful houseplant diagnosis assistant. You are given a photo "
    "of a plant plus authoritative species care facts and care schedules. "
    "First describe what you observe in the photo (leaf color, spots, "
    "wilting, pests, soil condition, etc.). Then reason about the likely "
    "cause using ONLY the provided care facts -- do not diagnose conditions "
    "unsupported by either the image or the data. If the photo is unclear or "
    "insufficient, say so plainly. Keep the response concise, specific, and "
    "friendly."
)


def _build_context(
    species: Species, plant: Plant, care_schedules: list[CareSchedule]
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
        lines = [
            f"- {cs.care_type.value}: every {cs.interval_days_min}-{cs.interval_days_max} days"
            for cs in care_schedules
        ]
        schedules_block = "\nCARE SCHEDULES:\n" + "\n".join(lines) + "\n"
    else:
        schedules_block = ""

    plant_block = (
        f"\nTHIS PLANT:\n"
        f"- Nickname: {plant.nickname}\n"
        f"- Location: {plant.location or '(unspecified)'}\n"
    )
    return facts + schedules_block + plant_block


def _diagnose_stub(
    species: Species,
    plant: Plant,
    care_schedules: list[CareSchedule],
    image_bytes: bytes,
    user_notes: str,
) -> str:
    return (
        f"[STUB] {plant.nickname} ({species.common_name}): No vision backend "
        f"configured ({len(image_bytes)} byte photo received but not analyzed). "
        f"Set VISION_BACKEND=ollama and pull a vision model "
        f"(`ollama pull {OLLAMA_VISION_MODEL}`) to enable photo diagnosis."
    )


def _diagnose_ollama(
    species: Species,
    plant: Plant,
    care_schedules: list[CareSchedule],
    image_bytes: bytes,
    user_notes: str,
) -> str:
    import httpx

    prompt = _build_context(species, plant, care_schedules)
    if user_notes.strip():
        prompt += f"\nOWNER NOTES:\n{user_notes.strip()}\n"
    prompt += "\nWhat do you observe in the photo, and what's the likely cause?"

    image_b64 = base64.b64encode(image_bytes).decode("ascii")
    try:
        resp = httpx.post(
            f"{OLLAMA_HOST}/api/chat",
            json={
                "model": OLLAMA_VISION_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_INSTRUCTION},
                    {"role": "user", "content": prompt, "images": [image_b64]},
                ],
                "stream": False,
            },
            timeout=180.0,  # local CPU vision inference can be slow
        )
        resp.raise_for_status()
        data = resp.json()
        return data["message"]["content"].strip()
    except httpx.HTTPError as e:
        raise RuntimeError(
            f"Ollama vision request failed ({e}). Is `ollama serve` running and "
            f"has '{OLLAMA_VISION_MODEL}' been pulled?"
        ) from e


IDENTIFY_INSTRUCTION = (
    "You are a houseplant identification assistant. You are given a photo of "
    "a plant and a list of candidate species. Name the most likely species "
    "from the candidate list. Respond with up to three candidates, one per "
    "line, exactly as they appear in the list (common name), most likely "
    "first. If the plant matches none of the candidates, or the photo is "
    "unclear, respond with the single word: UNKNOWN. Then, on a new line "
    "starting with 'OBSERVED:', briefly describe the identifying features "
    "you can see (leaf shape, pattern, growth habit)."
)


def _identify_stub(image_bytes: bytes, catalog: list[Species]) -> tuple[str, list[str]]:
    return (
        "📷 Photo received! AI identification isn't enabled yet, so pick "
        "your plant from the search below — automatic identification will "
        "light up once a vision backend is turned on.",
        [],
    )


def _identify_ollama(image_bytes: bytes, catalog: list[Species]) -> tuple[str, list[str]]:
    import httpx

    names = "\n".join(f"- {s.common_name} ({s.scientific_name})" for s in catalog)
    prompt = f"CANDIDATE SPECIES:\n{names}\n\nWhich species is in the photo?"
    image_b64 = base64.b64encode(image_bytes).decode("ascii")
    try:
        resp = httpx.post(
            f"{OLLAMA_HOST}/api/chat",
            json={
                "model": OLLAMA_VISION_MODEL,
                "messages": [
                    {"role": "system", "content": IDENTIFY_INSTRUCTION},
                    {"role": "user", "content": prompt, "images": [image_b64]},
                ],
                "stream": False,
            },
            timeout=180.0,
        )
        resp.raise_for_status()
        text = resp.json()["message"]["content"].strip()
    except httpx.HTTPError as e:
        raise RuntimeError(
            f"Ollama vision request failed ({e}). Is `ollama serve` running and "
            f"has '{OLLAMA_VISION_MODEL}' been pulled?"
        ) from e

    # The name lines come before the OBSERVED: line; keep order (most likely first)
    name_lines = [
        line.strip("- ").strip()
        for line in text.splitlines()
        if line.strip() and not line.upper().startswith(("OBSERVED:", "UNKNOWN"))
    ]
    return text, name_lines


_IDENTIFY_BACKENDS = {
    "stub": _identify_stub,
    "ollama": _identify_ollama,
}


def identify_species(image_bytes: bytes, catalog: list[Species]) -> dict:
    """Identify which catalog species a photo most likely shows.

    Returns {"backend", "observation", "candidate_ids"} where candidate_ids
    are Species.id values matched against the model's named candidates,
    most likely first. The stub backend returns no candidates."""
    fn = _IDENTIFY_BACKENDS.get(BACKEND, _identify_stub)
    observation, names = fn(image_bytes, catalog)

    candidate_ids: list[int] = []
    for name in names:
        lowered = name.lower()
        for s in catalog:
            if s.id in candidate_ids:
                continue
            if s.common_name.lower() in lowered or s.scientific_name.lower() in lowered:
                candidate_ids.append(s.id)
                break
    return {"backend": BACKEND, "observation": observation, "candidate_ids": candidate_ids}


_BACKENDS = {
    "stub": _diagnose_stub,
    "ollama": _diagnose_ollama,
}


def diagnose_photo(
    species: Species,
    plant: Plant,
    care_schedules: list[CareSchedule],
    image_bytes: bytes,
    user_notes: str = "",
) -> dict:
    """Return a photo diagnosis for a plant. The only function the rest of the
    app calls. Returns a dict so the API response can report which backend
    produced the diagnosis."""
    fn = _BACKENDS.get(BACKEND, _diagnose_stub)
    diagnosis = fn(species, plant, care_schedules, image_bytes, user_notes)
    return {"backend": BACKEND, "diagnosis": diagnosis}
