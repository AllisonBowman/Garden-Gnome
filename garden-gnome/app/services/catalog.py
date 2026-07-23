"""LLM-assisted species profile generation.

Given a plant name, produces a draft species record (species fields, care
schedules, traits) in the same shape as SpeciesCreate / species_catalog.json.

The output is a review-and-confirm draft — not saved automatically. Caller
should POST the returned dict to POST /species/ after verification.

Uses the same ADVISOR_BACKEND settings as advisor.py, so no extra
configuration is needed if text advice is already working."""
import json
import logging
import os
import re

from app.services.advisor import AdvisorUnavailable, UNAVAILABLE_MESSAGE

logger = logging.getLogger("plantadvocate.catalog")

BACKEND = os.getenv("ADVISOR_BACKEND", "stub")

_PROMPT = """\
You are a plant care database assistant. Given a plant name, produce a single \
JSON object with complete, accurate indoor care data for that species.

Respond ONLY with valid JSON — no markdown fences, no explanation, no extra text.

Required structure (all fields are required):
{{
  "common_name": "most widely used common name",
  "scientific_name": "Genus species [cultivar if needed]",
  "light_need": "low | medium | bright_indirect | direct",
  "humidity_pct_min": integer 0-100,
  "humidity_pct_max": integer 0-100,
  "temp_f_min": integer (Fahrenheit),
  "temp_f_max": integer (Fahrenheit),
  "soil_type": "specific mix recommendation",
  "toxic_to_pets": true or false,
  "care_notes": "1-2 sentence summary of the most important care quirks",
  "schedules": [
    {{
      "care_type": "water | fertilize | mist | prune | repot | rotate | clean | other",
      "interval_days_min": integer,
      "interval_days_max": integer,
      "notes": "specific guidance for this care type and species"
    }}
  ],
  "traits": [
    {{
      "trait": "growth_rate | max_height_inches | propagation | native_region",
      "value": "string value",
      "unit": "inches if max_height_inches, otherwise empty string"
    }}
  ]
}}

Rules:
- schedules must include at least water and fertilize.
- Add mist, clean, prune, repot, rotate only where genuinely relevant.
- traits should include all four types if known.
- All interval values must be integers (days), not ranges expressed as strings.

Plant name: {name}
"""

_STUB_TEMPLATE = {
    "common_name": "",
    "scientific_name": "",
    "light_need": "medium",
    "humidity_pct_min": 40,
    "humidity_pct_max": 60,
    "temp_f_min": 65,
    "temp_f_max": 80,
    "soil_type": "Well-draining potting mix",
    "toxic_to_pets": False,
    "care_notes": "Review and fill in all fields. Set ADVISOR_BACKEND=anthropic for AI-generated profiles.",
    "schedules": [
        {"care_type": "water", "interval_days_min": 7, "interval_days_max": 14, "notes": "Fill in watering guidance."},
        {"care_type": "fertilize", "interval_days_min": 30, "interval_days_max": 60, "notes": "Fill in fertilizing guidance."},
    ],
    "traits": [
        {"trait": "growth_rate", "value": "moderate", "unit": ""},
        {"trait": "native_region", "value": "Unknown", "unit": ""},
    ],
}


def _extract_json(text: str) -> dict:
    """Strip optional markdown fences and parse JSON from LLM output."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    return json.loads(text.strip())


def _wrap_for_api(species_dict: dict) -> dict:
    """Separate top-level species fields from nested schedules/traits.

    The SpeciesCreate schema expects a flat dict with schedules and traits
    as top-level keys; the LLM produces exactly this shape already."""
    # Validate that required top-level keys are present
    required = {
        "common_name", "scientific_name", "light_need",
        "humidity_pct_min", "humidity_pct_max", "temp_f_min", "temp_f_max",
        "soil_type", "toxic_to_pets", "care_notes",
    }
    missing = required - species_dict.keys()
    if missing:
        logger.error("Model profile response missing fields: %s", sorted(missing))
        raise AdvisorUnavailable(UNAVAILABLE_MESSAGE)
    return species_dict


def generate_species_profile(name: str) -> dict:
    """Return a draft SpeciesCreate-compatible dict for the given plant name.

    Stub backend returns a template with placeholder values.
    The Anthropic backend asks the model to produce structured JSON.
    The caller must review and POST to POST /species/ to persist."""
    if BACKEND == "stub":
        draft = json.loads(json.dumps(_STUB_TEMPLATE))
        draft["common_name"] = name
        draft["scientific_name"] = f"(scientific name for {name} — fill in)"
        return draft

    if BACKEND == "anthropic":
        return _generate_anthropic(name)

    logger.error("Unknown ADVISOR_BACKEND: %r", BACKEND)
    raise AdvisorUnavailable(UNAVAILABLE_MESSAGE)


def _generate_anthropic(name: str) -> dict:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    model = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY not set in .env")
        raise AdvisorUnavailable(UNAVAILABLE_MESSAGE)
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": _PROMPT.format(name=name)}],
        )
        text = msg.content[0].text
        return _wrap_for_api(_extract_json(text))
    except AdvisorUnavailable:
        raise  # already logged and already user-safe
    except Exception as exc:
        logger.error("Anthropic profile request failed: %s", exc)
        raise AdvisorUnavailable(UNAVAILABLE_MESSAGE) from exc
