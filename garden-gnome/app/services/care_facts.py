"""One fact block for every surface that describes a species.

The advisor prompt, the vision prompt and the deterministic stub each tell
someone -- a model or a caretaker -- what a species needs, and until now each
read the six legacy columns as if every row had them. A row minted from the
claim tranche has none (ADR 0005); a row the tranche resolved holds something
better in the resolved columns; and a value borrowed from the genus must say
so wherever it appears (ADR 0002). So the block is built once, here, from what
the row actually holds: a resolved concept replaces its legacy line, no
concept is stated twice, nothing absent is invented, and the authorities are
named -- the name only, never the passage (ADR 0003).
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Callable

from app.models.models import Species

#: Suffix on any value the resolver borrowed from the genus (ADR 0002).
GENUS_LABEL = " (genus-inferred)"
#: The same fact in the caretaker's voice, for the stub and weather nudges.
BORROWED_LABEL = " (borrowed from the genus)"

LEGACY_COLUMNS = ("light_need", "humidity_pct_min", "humidity_pct_max",
                  "temp_f_min", "temp_f_max", "soil_type")
#: The resolved care columns this block reads. Toxicity is a verdict, not a
#: care value, and has its own line.
RESOLVED_COLUMNS = (
    "light_fc_min", "light_fc_good", "direct_sun_hours_max",
    "humidity_need",
    "day_f_min", "day_f_max", "night_f_min", "night_f_max", "chill_damage_f",
    "soil_base", "soil_drainage", "soil_ph_min", "soil_ph_max",
    "water_regime", "water_check_depth_cm", "water_growing_days_est",
    "water_dormant_days_est",
    "fertilize_active_months", "fertilize_interval_days", "fertilize_strength",
    "outdoor_sun_exposure", "hardiness_zones",
)

# Wording for the categorical fields. A token like `chunky_aroid` is a column
# value, not a fact anyone can act on, so none of these leak through as-is.
WATER_REGIME_TEXT = {
    "keep_moist": "keep the medium evenly moist",
    "keep_barely_moist": "keep the medium barely moist",
    "dry_surface_between": "let the surface dry between waterings",
    "dry_thoroughly_between": "let the medium dry thoroughly between waterings",
}
_HUMIDITY_TEXT = {
    "low": "low; tolerates dry air",
    "average": "average room humidity",
    "high": "high; wants humid air",
}
_SOIL_BASE_TEXT = {
    "standard_potting": "standard potting mix",
    "chunky_aroid": "chunky aroid mix",
    "cactus_succulent": "cactus and succulent mix",
    "ericaceous": "ericaceous (acid) mix",
    "orchid_bark": "orchid bark",
    "african_violet": "African violet mix",
    "semi_hydro": "semi-hydro (inert medium)",
    "garden_bed": "garden bed soil",
}
_DRAINAGE_TEXT = {
    "fast": "fast-draining",
    "moderate": "moderately draining",
    "moisture_retentive": "moisture-retentive",
}
_STRENGTH_TEXT = {
    "full": "full strength", "half": "half strength", "quarter": "quarter strength",
}
_SUN_TEXT = {
    "full_sun": "full sun", "part_sun": "part sun",
    "part_shade": "part shade", "full_shade": "full shade",
}
_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

Tag = Callable[..., str]
#: What one concept contributes: its lines, and the concept's name when a
#: legacy column supplied them -- so the care-data line can say so.
Told = tuple[list[str], str]


def token(value: Any) -> Any:
    """An enum's value, or the value itself.

    A row loaded from the table carries enums; a row built in code carries
    the raw strings, because table models do not validate on construction.
    The wording tables key on the string either way."""
    return value.value if isinstance(value, Enum) else value


def is_genus_inferred(species: Species, *fields: str) -> bool:
    """Whether any of `fields` was borrowed from the genus (ADR 0002)."""
    provenance = species.care_provenance or {}
    return any(provenance.get(f) == "genus_inferred" for f in fields)


def water_regime_sentence(species: Species) -> str | None:
    """The regime as a caretaker would say it; None when nothing resolved."""
    return WATER_REGIME_TEXT.get(token(species.water_regime))


def month_span(months: list[int]) -> str:
    """'Mar-Oct' when the months run without a gap -- wrapping through
    December counts, 'Nov-Mar' -- otherwise listed: 'Mar and Sep'."""
    ordered = sorted({int(m) for m in months if 1 <= int(m) <= 12})
    names = [_MONTHS[m - 1] for m in ordered]
    if len(names) <= 1:
        return "".join(names)
    if len(names) == 12:
        return "all year"
    # Around the circle of the year a contiguous run has exactly one gap that
    # is not a single month; the span starts just after it and ends on it.
    gaps = [(b - a) % 12 for a, b in zip(ordered, ordered[1:] + ordered[:1])]
    breaks = [i for i, gap in enumerate(gaps) if gap != 1]
    if len(breaks) == 1:
        i = breaks[0]
        return f"{names[(i + 1) % len(names)]}-{names[i]}"
    return ", ".join(names[:-1]) + " and " + names[-1]


def _num(value: float | int) -> str:
    """3.0 -> '3', 2.5 -> '2.5': depths and hours read as counts."""
    return f"{value:g}"


def _band(low, high, unit: str) -> str:
    if low is not None and high is not None:
        return f"{_num(low)}-{_num(high)}{unit}"
    if low is not None:
        return f"from {_num(low)}{unit}"
    return f"up to {_num(high)}{unit}"


def _tagger(species: Species) -> Tag:
    provenance = species.care_provenance or {}

    def tag(text: str, *fields: str) -> str:
        borrowed = any(provenance.get(f) == "genus_inferred" for f in fields)
        return text + GENUS_LABEL if borrowed else text
    return tag


def _light(sp: Species, tag: Tag) -> Told:
    parts = []
    if sp.light_fc_min is not None:
        parts.append(tag(f"at least {_num(sp.light_fc_min)} footcandles",
                         "light_fc_min"))
    if sp.light_fc_good is not None:
        parts.append(tag(f"{_num(sp.light_fc_good)} footcandles is comfortable",
                         "light_fc_good"))
    if sp.direct_sun_hours_max is not None:
        # "Up to 0 hours" is true and not how anyone says it.
        sun = ("no direct sun" if sp.direct_sun_hours_max == 0 else
               f"up to {_num(sp.direct_sun_hours_max)} hours of direct sun")
        parts.append(tag(sun, "direct_sun_hours_max"))
    if parts:
        return [f"- Light: {'; '.join(parts)}"], ""
    if sp.light_need is not None:
        return [f"- Light need: {token(sp.light_need)}"], "light"
    return [], ""


def _humidity(sp: Species, tag: Tag) -> Told:
    need = _HUMIDITY_TEXT.get(token(sp.humidity_need))
    if need:
        return [f"- Humidity: {tag(need, 'humidity_need')}"], ""
    # The legacy band only when the numbers came from a source: imported rows
    # derived theirs from a watering category, and a block headed
    # "authoritative" must not hand a model derived numbers as facts.
    if (sp.humidity_pct_min is not None and sp.humidity_pct_max is not None
            and sp.humidity_sourced):
        return [f"- Humidity: {sp.humidity_pct_min}-{sp.humidity_pct_max}%"], "humidity"
    return [], ""


def _temperature(sp: Species, tag: Tag) -> Told:
    parts = []
    if sp.day_f_min is not None or sp.day_f_max is not None:
        parts.append(tag(f"days {_band(sp.day_f_min, sp.day_f_max, ' F')}",
                         "day_f_min", "day_f_max"))
    if sp.night_f_min is not None or sp.night_f_max is not None:
        parts.append(tag(f"nights {_band(sp.night_f_min, sp.night_f_max, ' F')}",
                         "night_f_min", "night_f_max"))
    if sp.chill_damage_f is not None:
        parts.append(tag(f"cold damage below {_num(sp.chill_damage_f)} F",
                         "chill_damage_f"))
    if parts:
        return [f"- Temperature: {'; '.join(parts)}"], ""
    if sp.temp_f_min is not None or sp.temp_f_max is not None:
        return ([f"- Temperature: {_band(sp.temp_f_min, sp.temp_f_max, ' F')}"],
                "temperature")
    return [], ""


def _soil(sp: Species, tag: Tag) -> Told:
    parts = []
    base = _SOIL_BASE_TEXT.get(token(sp.soil_base))
    if base:
        parts.append(tag(base, "soil_base"))
    drainage = _DRAINAGE_TEXT.get(token(sp.soil_drainage))
    if drainage:
        parts.append(tag(drainage, "soil_drainage"))
    if sp.soil_ph_min is not None or sp.soil_ph_max is not None:
        parts.append(tag(f"pH {_band(sp.soil_ph_min, sp.soil_ph_max, '')}",
                         "soil_ph_min", "soil_ph_max"))
    if parts:
        return [f"- Soil: {'; '.join(parts)}"], ""
    if sp.soil_type:
        return [f"- Soil: {sp.soil_type}"], "soil"
    return [], ""


def _water(sp: Species, tag: Tag) -> Told:
    """The regime, the check depth and the day estimate -- never the
    dry-down target, which is a verbatim passage (ADR 0003)."""
    parts = []
    regime = water_regime_sentence(sp)
    if regime:
        parts.append(tag(regime, "water_regime"))
    if sp.water_check_depth_cm is not None:
        parts.append(tag(f"check {_num(sp.water_check_depth_cm)} cm down",
                         "water_check_depth_cm"))
    growing, dormant = sp.water_growing_days_est, sp.water_dormant_days_est
    if growing is not None and dormant is not None:
        estimate = (f"roughly every {growing} days in growth, {dormant} in "
                    "dormancy (estimate)")
    elif growing is not None:
        estimate = f"roughly every {growing} days in growth (estimate)"
    elif dormant is not None:
        estimate = f"roughly every {dormant} days in dormancy (estimate)"
    else:
        estimate = ""
    if estimate:
        parts.append(tag(estimate, "water_growing_days_est",
                         "water_dormant_days_est"))
    return ([f"- Water: {'; '.join(parts)}"] if parts else []), ""


def _fertilize(sp: Species, tag: Tag) -> Told:
    parts = []
    span = month_span(sp.fertilize_active_months or [])
    if span:
        parts.append(tag(span, "fertilize_active_months"))
    if sp.fertilize_interval_days is not None:
        parts.append(tag(f"every {sp.fertilize_interval_days} days",
                         "fertilize_interval_days"))
    strength = _STRENGTH_TEXT.get(token(sp.fertilize_strength))
    if strength:
        parts.append(tag(strength, "fertilize_strength"))
    return ([f"- Fertilize: {'; '.join(parts)}"] if parts else []), ""


def _outdoors(sp: Species, tag: Tag) -> Told:
    lines = []
    if sp.outdoor_sun_exposure:
        words = [_SUN_TEXT.get(token(v), str(token(v)).replace("_", " "))
                 for v in sp.outdoor_sun_exposure]
        lines.append(f"- Outdoor sun: {tag(', '.join(words), 'outdoor_sun_exposure')}")
    if sp.hardiness_zones:
        zones = ", ".join(str(z) for z in sp.hardiness_zones)
        lines.append(f"- Hardiness zones: {tag(zones, 'hardiness_zones')}")
    return lines, ""


def _toxicity_word(flag: bool | None) -> str:
    # Null is "no record", never "no": a default read as safety is the
    # invented verdict ADR 0002 forbids.
    if flag is None:
        return "no record"
    return "yes" if flag else "no"


def _listed(words: list[str]) -> str:
    """'light', 'light and soil', 'light, humidity and soil'."""
    if len(words) <= 1:
        return "".join(words)
    return ", ".join(words[:-1]) + " and " + words[-1]


def _catalog_caveat(legacy: list[str]) -> str:
    """The legacy lines sit under "cited to ..." looking equally cited.
    They are catalog values no claim backs, and the line has to say which."""
    if not legacy:
        return ""
    verb = "is a catalog value" if len(legacy) == 1 else "are catalog values"
    return f"; {_listed(legacy)} above {verb}, not cited"


def _care_data_line(sp: Species, legacy: list[str]) -> str | None:
    """How well-backed the block above is, in the words CONTEXT.md allows
    ("verified" is not one of them). `legacy` names the concepts whose line
    came from a legacy column rather than a claim."""
    status = token(sp.care_data_status)
    if status in ("sourced", "inferred"):
        sources = sp.care_sources or []
        names = sorted({s.get("authority") for s in sources
                        if s.get("authority") and not s.get("inferred")})
        if names:
            backing = f"cited to {', '.join(names)}"
        elif sources or status == "inferred":
            backing = "borrowed from the genus, not confirmed for this species"
        else:
            # Resolved under an older resolver, before sources were materialised.
            backing = "cited to published sources"
        return f"- Care data: {backing}{_catalog_caveat(legacy)}"
    has_resolved = any(getattr(sp, f) is not None for f in RESOLVED_COLUMNS)
    has_legacy = any(getattr(sp, f) is not None for f in LEGACY_COLUMNS)
    if not has_resolved and not has_legacy:
        return "- Care data: none cited for this species yet"
    return None


def species_fact_lines(species: Species) -> list[str]:
    """The care facts, one line per concept the row can actually back.

    Resolved columns win: light_fc_*/direct_sun_hours_max replace light_need,
    humidity_need replaces the humidity band, day/night/chill replace
    temp_f_*, and soil_base/drainage/pH replace soil_type. A legacy line
    appears only when its concept has no resolved counterpart, and then in
    exactly its old wording -- tests pin those strings.
    """
    tag = _tagger(species)
    lines = [f"- Common name: {species.common_name}",
             f"- Scientific name: {species.scientific_name}"]
    legacy: list[str] = []
    for concept in (_light, _humidity, _temperature, _soil, _water,
                    _fertilize, _outdoors):
        told, from_legacy = concept(species, tag)
        lines.extend(told)
        if from_legacy:
            legacy.append(from_legacy)
    lines.append(f"- Toxic to pets: {_toxicity_word(species.toxic_to_pets)}")
    care_data = _care_data_line(species, legacy)
    if care_data:
        lines.append(care_data)
    if species.care_notes:
        lines.append(f"- Curated notes: {species.care_notes}")
    return lines
