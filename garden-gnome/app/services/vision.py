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

Operational notes (the Ollama path is built for real use, not a demo):
- All Ollama I/O is async (httpx.AsyncClient) so a slow local inference never
  blocks the FastAPI event loop for other requests.
- Photos are downscaled/re-encoded (Pillow) before upload: phone photos run
  5-10 MB, small vision models ingest at ~1k px anyway, and base64-in-JSON
  adds 33%. This also applies EXIF rotation, which models never read.
- Failures raise VisionUnavailable whose str() is safe to show an end user;
  the technical cause (connection refused, model not pulled, ...) goes to the
  server log only.
- `vision_status()` reports readiness (backend configured, Ollama reachable,
  model pulled) for the /ai/status endpoint and the startup log.
"""
from __future__ import annotations

import base64
import io
import logging
import os

import httpx

from app.models.models import Species, Plant, CareSchedule

logger = logging.getLogger("plantadvocate.vision")

DEFAULT_VISION_MODEL = "moondream"

# Inference tuning. keep_alive holds the model in memory between requests so
# only the first diagnosis after a quiet period pays the model-load cost.
KEEP_ALIVE = "30m"
TEMPERATURE = 0.2
CONNECT_TIMEOUT = 5.0   # fail fast when Ollama isn't running
READ_TIMEOUT = 180.0    # local CPU vision inference can be slow

# Image preprocessing bounds (see prepare_image).
MAX_IMAGE_DIM = 1024
JPEG_QUALITY = 85

# The one user-facing failure message. Deliberately free of setup
# instructions, env var names, and tool names -- those go to the log.
UNAVAILABLE_MESSAGE = (
    "The Gnome couldn't examine this photo right now — the photo check-up "
    "service didn't respond. Your photo was not analyzed; please try again "
    "in a few minutes."
)


class VisionUnavailable(RuntimeError):
    """The configured vision backend cannot serve requests right now.

    str(exc) is user-presentable; the technical cause is already logged."""


# Config is read at call time, not import time, so tests and long-running
# processes can switch backends without re-importing the module.
def _backend() -> str:
    return os.getenv("VISION_BACKEND", "stub").lower()


def _ollama_host() -> str:
    return os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")


def _model() -> str:
    return os.getenv("OLLAMA_VISION_MODEL", DEFAULT_VISION_MODEL)


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


def prepare_image(image_bytes: bytes) -> bytes:
    """Normalize a photo for vision inference: apply EXIF rotation, downscale
    to MAX_IMAGE_DIM on the long side, re-encode as JPEG.

    Falls back to the original bytes if Pillow is missing or the bytes don't
    decode -- the backend then sees exactly what the client sent."""
    try:
        from PIL import Image, ImageOps
    except ImportError:
        logger.warning("Pillow not installed; sending original photo bytes")
        return image_bytes

    try:
        img = Image.open(io.BytesIO(image_bytes))
        img = ImageOps.exif_transpose(img)
        img.thumbnail((MAX_IMAGE_DIM, MAX_IMAGE_DIM))
        out = io.BytesIO()
        img.convert("RGB").save(out, format="JPEG", quality=JPEG_QUALITY)
        prepared = out.getvalue()
    except Exception as e:
        logger.warning("Photo preprocessing failed (%s); sending original bytes", e)
        return image_bytes

    logger.info(
        "Prepared photo for inference: %d -> %d bytes", len(image_bytes), len(prepared)
    )
    return prepared


async def _ollama_chat(system: str, prompt: str, image_bytes: bytes, purpose: str) -> str:
    """One vision-chat round trip to Ollama. Raises VisionUnavailable (with a
    user-safe message) on any failure; logs the technical cause."""
    host, model = _ollama_host(), _model()
    image_b64 = base64.b64encode(prepare_image(image_bytes)).decode("ascii")
    timeout = httpx.Timeout(
        connect=CONNECT_TIMEOUT, read=READ_TIMEOUT, write=30.0, pool=5.0
    )
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                f"{host}/api/chat",
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt, "images": [image_b64]},
                    ],
                    "stream": False,
                    "keep_alive": KEEP_ALIVE,
                    "options": {"temperature": TEMPERATURE},
                },
            )
            resp.raise_for_status()
            content = resp.json()["message"]["content"].strip()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            logger.error(
                "Ollama %s failed: model '%s' not found at %s — run `ollama pull %s`",
                purpose, model, host, model,
            )
        else:
            logger.error(
                "Ollama %s failed: HTTP %d from %s: %s",
                purpose, e.response.status_code, host, e.response.text[:500],
            )
        raise VisionUnavailable(UNAVAILABLE_MESSAGE) from e
    except httpx.HTTPError as e:
        logger.error(
            "Ollama %s failed: %s: %s. Is `ollama serve` running at %s and has "
            "'%s' been pulled?",
            purpose, type(e).__name__, e, host, model,
        )
        raise VisionUnavailable(UNAVAILABLE_MESSAGE) from e
    except (KeyError, TypeError, ValueError) as e:
        logger.error("Ollama %s returned an unexpected payload: %s", purpose, e)
        raise VisionUnavailable(UNAVAILABLE_MESSAGE) from e

    if not content:
        logger.error("Ollama %s returned an empty response", purpose)
        raise VisionUnavailable(UNAVAILABLE_MESSAGE)
    return content


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


async def _diagnose_stub(
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
        f"(`ollama pull {_model()}`) to enable photo diagnosis."
    )


async def _diagnose_ollama(
    species: Species,
    plant: Plant,
    care_schedules: list[CareSchedule],
    image_bytes: bytes,
    user_notes: str,
) -> str:
    prompt = _build_context(species, plant, care_schedules)
    if user_notes.strip():
        prompt += f"\nOWNER NOTES:\n{user_notes.strip()}\n"
    prompt += "\nWhat do you observe in the photo, and what's the likely cause?"
    return await _ollama_chat(SYSTEM_INSTRUCTION, prompt, image_bytes, "diagnosis")


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


async def _identify_stub(image_bytes: bytes, catalog: list[Species]) -> tuple[str, list[str]]:
    return (
        "📷 Photo received! AI identification isn't enabled yet, so pick "
        "your plant from the search below — automatic identification will "
        "light up once a vision backend is turned on.",
        [],
    )


async def _identify_ollama(image_bytes: bytes, catalog: list[Species]) -> tuple[str, list[str]]:
    names = "\n".join(f"- {s.common_name} ({s.scientific_name})" for s in catalog)
    prompt = f"CANDIDATE SPECIES:\n{names}\n\nWhich species is in the photo?"
    text = await _ollama_chat(IDENTIFY_INSTRUCTION, prompt, image_bytes, "identification")

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
    "ollama": _diagnose_ollama,
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

    ready=True means a photo request right now would reach a model: backend
    is ollama, the host answers, and the configured model is pulled. Detail
    strings are operator-facing but contain no hosts or secrets."""
    backend = _backend()
    if backend != "ollama":
        return {
            "backend": backend,
            "model": None,
            "ready": False,
            "detail": "No vision backend configured; photo features return a not-enabled message.",
        }

    model = _model()
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
            resp = await client.get(f"{_ollama_host()}/api/tags")
            resp.raise_for_status()
            tags = resp.json().get("models", [])
    except (httpx.HTTPError, ValueError) as e:
        logger.warning("Ollama not reachable at %s: %s", _ollama_host(), e)
        return {
            "backend": backend,
            "model": model,
            "ready": False,
            "detail": "Ollama is not reachable.",
        }

    pulled_names = {str(m.get("name", "")) for m in tags if isinstance(m, dict)}
    if not any(n == model or n.split(":")[0] == model for n in pulled_names):
        return {
            "backend": backend,
            "model": model,
            "ready": False,
            "detail": f"Model '{model}' is not pulled.",
        }
    return {"backend": backend, "model": model, "ready": True, "detail": "ok"}
