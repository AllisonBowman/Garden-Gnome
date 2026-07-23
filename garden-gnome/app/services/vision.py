"""Photo diagnosis service (Phase 3).

This module is the ONLY place that would talk to a vision model. Mirrors
app/services/advisor.py's backend-swap pattern: the rest of the app calls
`diagnose_photo(...)` and gets back a dict, swapping backends is a config
change here, nothing else.

Backend is chosen by the VISION_BACKEND environment variable:
    stub - no model; returns a placeholder explaining the feature isn't
           enabled yet (default, and currently the only backend)

No hosted vision backend is configured on purpose: photo species
identification runs on-device in the mobile app (Apple Foundation Models /
Gemini Nano), and server-side photo diagnosis ships disabled until a
backend direction is chosen. The functions stay async and the backend dict
stays in place so a future backend is a config change, not a rewrite.

Core principle (same as advisor.py): the species row + care schedules are
authoritative ground truth. Any future model describes what it observes in
the photo and reasons about likely causes using ONLY the provided care
facts -- it does not invent diagnoses unsupported by the image or the data.
"""
from __future__ import annotations

import logging
import os

from app.models.models import Species, Plant, CareSchedule

logger = logging.getLogger("plantadvocate.vision")


# Config is read at call time, not import time, so tests and long-running
# processes can switch backends without re-importing the module.
def _backend() -> str:
    return os.getenv("VISION_BACKEND", "stub").lower()


async def _diagnose_stub(
    species: Species,
    plant: Plant,
    care_schedules: list[CareSchedule],
    image_bytes: bytes,
    user_notes: str,
) -> str:
    # The photo is received but never analyzed while diagnosis is disabled.
    # Keep the operational detail (that this is the stub, and the byte count)
    # in the server log; the user only ever sees the friendly note below.
    logger.info(
        "stub diagnosis: %d byte photo for plant %s (%s) received, not analyzed",
        len(image_bytes), plant.nickname, species.common_name,
    )
    return (
        "📷 Photo received! The Gnome's photo check-ups aren't switched on "
        "yet, so there's no diagnosis to share this time. Your plant's care "
        "guide below still has everything for its species and history."
    )


async def _identify_stub(image_bytes: bytes, catalog: list[Species]) -> tuple[str, list[str]]:
    return (
        "📷 Photo received! AI identification isn't enabled yet, so pick "
        "your plant from the search below — automatic identification will "
        "light up once a vision backend is turned on.",
        [],
    )


_IDENTIFY_BACKENDS = {
    "stub": _identify_stub,
}


async def identify_species(image_bytes: bytes, catalog: list[Species]) -> dict:
    """Identify which catalog species a photo most likely shows.

    Returns {"backend", "observation", "candidate_ids"} where candidate_ids
    are Species.id values matched against the model's named candidates,
    most likely first. The stub backend returns no candidates."""
    backend = _backend()
    fn = _IDENTIFY_BACKENDS.get(backend, _identify_stub)
    observation, names = await fn(image_bytes, catalog)

    candidate_ids: list[int] = []
    for name in names:
        lowered = name.lower()
        for s in catalog:
            if s.id in candidate_ids:
                continue
            if s.common_name.lower() in lowered or s.scientific_name.lower() in lowered:
                candidate_ids.append(s.id)
                break
    return {"backend": backend, "observation": observation, "candidate_ids": candidate_ids}


_BACKENDS = {
    "stub": _diagnose_stub,
}


async def diagnose_photo(
    species: Species,
    plant: Plant,
    care_schedules: list[CareSchedule],
    image_bytes: bytes,
    user_notes: str = "",
) -> dict:
    """Return a photo diagnosis for a plant. The only function the rest of the
    app calls. Returns a dict so the API response can report which backend
    produced the diagnosis."""
    backend = _backend()
    fn = _BACKENDS.get(backend, _diagnose_stub)
    diagnosis = await fn(species, plant, care_schedules, image_bytes, user_notes)
    return {"backend": backend, "diagnosis": diagnosis}


async def vision_status() -> dict:
    """Readiness of the vision backend, for /ai/status and the startup log.

    ready=True would mean a photo request right now reaches a real model;
    with only the stub registered this is always False."""
    backend = _backend()
    return {
        "backend": backend,
        "model": None,
        "ready": False,
        "detail": "No vision backend configured; photo features return a not-enabled message.",
    }
