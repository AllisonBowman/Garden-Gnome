"""Photo vision service — species identification and photo diagnosis.

This module is the ONLY place that talks to a vision model. Mirrors
app/services/advisor.py's backend-swap pattern: the rest of the app calls
`identify_species(...)` / `diagnose_photo(...)` and gets back a dict; swapping
backends is a config change here, nothing else.

Backend is chosen by the VISION_BACKEND environment variable:
    stub      - no model; returns a placeholder explaining the feature isn't
                enabled yet (the default)
    anthropic - Claude API (cloud, paid per photo, no infrastructure to run)

`stub` remains the default: photo species identification also runs on-device
in the mobile app (Apple Foundation Models / Gemini Nano), so the server-side
backend is an opt-in enhancement rather than a requirement.

Core principle (same as advisor.py): the species row + care schedules are
authoritative ground truth. The model describes what it observes in the photo
and reasons about likely causes using ONLY the provided care facts -- it does
not invent diagnoses unsupported by the image or the data.
"""
from __future__ import annotations

import base64
import io
import logging
import os

from app.models.models import Species, Plant, CareSchedule
from app.services.grounding import grounding_failures, log_rejection
from app.services.name_match import classify_matches, match_species
from app.services.persona import PERSONA_PREAMBLE

logger = logging.getLogger("plantadvocate.vision")

# Cloud vision defaults. Sonnet was chosen over Haiku for identification:
# picking between visually similar species (Pothos vs. Heartleaf Philodendron)
# is exactly where the cheaper tier struggles, and that is the failure this
# backend exists to fix.
DEFAULT_ANTHROPIC_VISION_MODEL = "claude-sonnet-5"
# Effort bounds how much the model thinks (and therefore what a photo costs).
# medium is the balance point; raise to high if similar species still confuse it.
DEFAULT_ANTHROPIC_EFFORT = "medium"
# Generous enough that adaptive thinking can't crowd out the answer -- thinking
# tokens count against max_tokens, and a truncated diagnosis is worse than a
# slightly pricier one.
ANTHROPIC_MAX_TOKENS = 2048

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


def _anthropic_model() -> str:
    return os.getenv("ANTHROPIC_VISION_MODEL", DEFAULT_ANTHROPIC_VISION_MODEL)


def _anthropic_effort() -> str:
    return os.getenv("ANTHROPIC_VISION_EFFORT", DEFAULT_ANTHROPIC_EFFORT).lower()


SYSTEM_INSTRUCTION = (
    PERSONA_PREAMBLE
    + "You are a careful houseplant diagnosis assistant. You are given a photo "
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


def _media_type(image_bytes: bytes) -> str:
    """Sniff the media type from magic bytes.

    prepare_image normally re-encodes to JPEG, but falls back to the original
    bytes when Pillow is missing or the image won't decode -- so the format
    isn't guaranteed. Anthropic rejects a mismatched media_type, so sniff
    rather than assume."""
    if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
        return "image/webp"
    if image_bytes.startswith(b"GIF8"):
        return "image/gif"
    return "image/jpeg"


async def _anthropic_vision_chat(
    system: str, prompt: str, image_bytes: bytes, purpose: str
) -> str:
    """One vision round trip to the Claude API. Raises VisionUnavailable (with a
    user-safe message) on any failure; logs the technical cause.

    Async on purpose: this module promises never to block the FastAPI event
    loop, so use AsyncAnthropic rather than the sync client advisor.py uses."""
    try:
        import anthropic
    except ImportError:
        logger.error("anthropic package not installed; cannot use the anthropic vision backend")
        raise VisionUnavailable(UNAVAILABLE_MESSAGE)

    if not os.getenv("ANTHROPIC_API_KEY", ""):
        logger.error("ANTHROPIC_API_KEY is not set; cannot use the anthropic vision backend")
        raise VisionUnavailable(UNAVAILABLE_MESSAGE)

    prepared = prepare_image(image_bytes)
    model = _anthropic_model()
    try:
        client = anthropic.AsyncAnthropic()
        message = await client.messages.create(
            model=model,
            max_tokens=ANTHROPIC_MAX_TOKENS,
            system=system,
            # Adaptive thinking helps most on the case this backend exists for:
            # telling visually similar species apart. Effort bounds the spend.
            # Note: Sonnet 5 rejects temperature/top_p/top_k -- don't add them.
            thinking={"type": "adaptive"},
            output_config={"effort": _anthropic_effort()},
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": _media_type(prepared),
                            "data": base64.b64encode(prepared).decode("ascii"),
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }],
        )
    except anthropic.APIError as e:
        logger.error("Anthropic %s failed: %s", purpose, e)
        raise VisionUnavailable(UNAVAILABLE_MESSAGE) from e
    except Exception as e:  # missing/invalid key surfaces at client construction
        logger.error("Anthropic %s client error: %s", purpose, e)
        raise VisionUnavailable(UNAVAILABLE_MESSAGE) from e

    # A safety decline returns HTTP 200 with empty content -- check before reading.
    if message.stop_reason == "refusal":
        logger.error("Anthropic %s was declined by safety classifiers", purpose)
        raise VisionUnavailable(UNAVAILABLE_MESSAGE)

    content = "".join(b.text for b in message.content if b.type == "text").strip()
    if not content:
        logger.error("Anthropic %s returned no text (stop_reason=%s)", purpose, message.stop_reason)
        raise VisionUnavailable(UNAVAILABLE_MESSAGE)

    logger.info(
        "Anthropic %s with %s: in=%d out=%d tokens",
        purpose, model, message.usage.input_tokens, message.usage.output_tokens,
    )
    return content


def _build_context(
    species: Species, plant: Plant, care_schedules: list[CareSchedule]
) -> str:
    # Same rule as the advisor: derived humidity (imported rows) never enters
    # a block headed "authoritative".
    humidity_line = (
        f"- Humidity: {species.humidity_pct_min}-{species.humidity_pct_max}%\n"
        if species.humidity_sourced else ""
    )
    facts = (
        f"SPECIES CARE FACTS (authoritative):\n"
        f"- Common name: {species.common_name}\n"
        f"- Scientific name: {species.scientific_name}\n"
        f"- Light need: {species.light_need.value}\n"
        f"{humidity_line}"
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


def _build_diagnose_prompt(
    species: Species,
    plant: Plant,
    care_schedules: list[CareSchedule],
    user_notes: str,
) -> str:
    prompt = _build_context(species, plant, care_schedules)
    if user_notes.strip():
        prompt += f"\nOWNER NOTES:\n{user_notes.strip()}\n"
    return prompt + "\nWhat do you observe in the photo, and what's the likely cause?"


async def _diagnose_anthropic(
    species: Species,
    plant: Plant,
    care_schedules: list[CareSchedule],
    image_bytes: bytes,
    user_notes: str,
) -> str:
    prompt = _build_diagnose_prompt(species, plant, care_schedules, user_notes)

    # A diagnosis legitimately describes things no fact mentions (spots,
    # wilting, pests), so the care-stem check is off here. The number,
    # template, first-person, and commitment checks still apply: those govern
    # care *claims*, which must stay grounded in the fact block. One retry,
    # then the honest unavailable message -- never an ungrounded diagnosis.
    for attempt in (1, 2):
        text = await _anthropic_vision_chat(
            SYSTEM_INSTRUCTION, prompt, image_bytes, "diagnosis"
        )
        failures = grounding_failures(prompt, text, check_care_stems=False)
        if not failures:
            return text
        log_rejection(f"diagnosis (attempt {attempt})", failures, text)

    raise VisionUnavailable(UNAVAILABLE_MESSAGE)


IDENTIFY_INSTRUCTION = (
    "You are a houseplant identification assistant. Identify the plant in the "
    "photo. Respond with up to three candidate species, one per line, most "
    "likely first, each as 'Scientific name (Common name)'. Prefer the "
    "botanical binomial — it is how the answer is looked up. If you cannot "
    "identify the plant, or the photo is too unclear to judge, respond with "
    "the single word: UNKNOWN. Then, on a new line starting with 'OBSERVED:', "
    "briefly describe the identifying features you can see (leaf shape, "
    "venation, pattern, growth habit)."
)

IDENTIFY_PROMPT = "What plant is in this photo?"


async def _identify_stub(image_bytes: bytes, catalog: list[Species]) -> tuple[str, list[str]]:
    return (
        "📷 Photo received! AI identification isn't enabled yet, so pick "
        "your plant from the search below — automatic identification will "
        "light up once a vision backend is turned on.",
        [],
    )


def _build_identify_prompt(catalog: list[Species]) -> str:
    """Ask the model to name the plant. The catalog is deliberately NOT sent.

    Listing every species costs tens of thousands of tokens per request and
    asks the model to scan a long flat list, which is a harder task than naming
    the plant outright. Grounding happens after the fact, in name_match."""
    return IDENTIFY_PROMPT


def _parse_identify_response(text: str) -> list[str]:
    """Pull the candidate name lines out of a model reply.

    The name lines come before the OBSERVED: line; keep order (most likely
    first). UNKNOWN yields no names, which the UI renders as manual search."""
    return [
        line.strip("- ").strip()
        for line in text.splitlines()
        if line.strip() and not line.upper().startswith(("OBSERVED:", "UNKNOWN"))
    ]


async def _identify_anthropic(image_bytes: bytes, catalog: list[Species]) -> tuple[str, list[str]]:
    prompt = _build_identify_prompt(catalog)
    text = await _anthropic_vision_chat(
        IDENTIFY_INSTRUCTION, prompt, image_bytes, "identification"
    )
    return text, _parse_identify_response(text)


_IDENTIFY_BACKENDS = {
    "stub": _identify_stub,
    "anthropic": _identify_anthropic,
}


async def identify_species(image_bytes: bytes, catalog: list[Species]) -> dict:
    """Identify which catalog species a photo most likely shows.

    Returns {"backend", "observation", "candidate_ids", "tier", "unreviewed_ids"}.
    candidate_ids are Species.id values, most likely first; the stub backend
    returns none.

    The model names the plant freely and name_match decides whether that name
    corresponds to a record we hold -- a weak match yields no candidates rather
    than a wrong one, so an out-of-catalog plant degrades to manual search."""
    backend = _backend()
    fn = _IDENTIFY_BACKENDS.get(backend, _identify_stub)
    observation, names = await fn(image_bytes, catalog)

    # Score every named candidate against the catalog, keeping the best score
    # per species and preserving the model's ordering across candidates.
    candidate_ids: list[int] = []
    tier = "none"
    unreviewed: list[int] = []
    for name in names:
        result = classify_matches(match_species(name, catalog))
        if result.tier == "none":
            continue
        if tier == "none":
            tier = result.tier
        for match in result.candidates:
            sid = match.species.id
            if sid is None or sid in candidate_ids:
                continue
            candidate_ids.append(sid)
            if not match.reviewed:
                unreviewed.append(sid)

    return {
        "backend": backend,
        "observation": observation,
        "candidate_ids": candidate_ids,
        # "confident" means the top match is strong enough to pre-select.
        "tier": tier,
        # Matches whose care data no human has checked yet -- the client should
        # hedge rather than present these as settled fact.
        "unreviewed_ids": unreviewed,
    }


_BACKENDS = {
    "stub": _diagnose_stub,
    "anthropic": _diagnose_anthropic,
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

    ready=True means a photo request right now would reach a model. Detail
    strings are operator-facing but contain no hosts or secrets."""
    backend = _backend()
    if backend == "anthropic":
        # No network probe: a readiness call would cost tokens on every poll.
        # Key presence is the only thing checkable for free.
        has_key = bool(os.getenv("ANTHROPIC_API_KEY", ""))
        return {
            "backend": backend,
            "model": _anthropic_model(),
            "ready": has_key,
            "detail": "ok" if has_key else "API key is not configured.",
        }

    return {
        "backend": backend,
        "model": None,
        "ready": False,
        "detail": "No vision backend configured; photo features return a not-enabled message.",
    }
