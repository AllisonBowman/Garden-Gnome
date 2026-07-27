"""Derive a set of descriptive tags from a species' own catalog record.

This is the join between the species database and the product network. Nothing
here invents facts about a plant: every tag traces to a field the curated
catalog already stores — `soil_type`, `light_need`, the humidity and
temperature bounds, `toxic_to_pets`, `care_notes`, the per-care-type schedules,
and the traits table. `explain()` returns that provenance so the API can tell a
user which part of the record produced a recommendation.

Why tags rather than a per-species product list: the catalog holds ~130 curated
species and the expansion pipeline admits thousands more. A hand-maintained
mapping would cover the first group and silently return nothing for the second.
Rules over derived tags cover every species the database will ever hold, and
the misses degrade to "fewer recommendations", never to wrong ones.

Classification order matters. Botanical identity (genus, and where the genus is
mixed, the full binomial) is checked first because it is unambiguous; free-text
cues in `care_notes` are a fallback for species outside the known sets.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Iterable, Optional

# --- Botanical groups ---------------------------------------------------------
# Genus-level sets. A genus lands here only when every species in it that a
# plant app would plausibly hold shares the same care hardware; genera that mix
# (Salvia = sage, rosemary AND a bedding annual) are resolved by binomial below.

AROID_GENERA = {
    "monstera", "philodendron", "epipremnum", "aglaonema", "dieffenbachia",
    "spathiphyllum", "anthurium", "alocasia", "colocasia", "zamioculcas",
    "syngonium", "scindapsus", "caladium", "xanthosoma", "rhaphidophora",
    "zantedeschia", "amorphophallus", "homalomena", "aglaonemas",
}
CLIMBING_AROIDS = {
    "monstera", "philodendron", "epipremnum", "syngonium", "scindapsus",
    "rhaphidophora", "anthurium",
}
SUCCULENT_GENERA = {
    "aloe", "crassula", "echeveria", "haworthia", "haworthiopsis", "sedum",
    "sempervivum", "kalanchoe", "curio", "senecio", "agave", "gasteria",
    "lithops", "portulacaria", "graptopetalum", "pachyphytum", "adromischus",
    "aeonium", "cotyledon", "delosperma", "fenestraria", "peperomia",
    "hoya", "sansevieria", "yucca", "pachypodium",
}
CACTUS_GENERA = {
    "mammillaria", "opuntia", "echinopsis", "schlumbergera", "rhipsalis",
    "cereus", "ferocactus", "gymnocalycium", "astrophytum", "epiphyllum",
    "parodia", "rebutia", "hatiora", "selenicereus", "espostoa",
}
ORCHID_GENERA = {
    "phalaenopsis", "cattleya", "dendrobium", "oncidium", "paphiopedilum",
    "vanda", "miltonia", "cymbidium", "zygopetalum", "bulbophyllum",
    "brassavola", "encyclia", "ludisia",
}
FERN_GENERA = {
    "nephrolepis", "adiantum", "asplenium", "platycerium", "pteris",
    "davallia", "polystichum", "dryopteris", "athyrium", "blechnum",
    "cyrtomium", "microsorum", "phlebodium",
}
PALM_GENERA = {
    "chamaedorea", "howea", "dypsis", "rhapis", "phoenix", "livistona",
    "caryota", "washingtonia", "areca", "chrysalidocarpus", "trachycarpus",
}

# Edible crop families
BRASSICA_GENERA = {"brassica", "raphanus", "armoracia", "eruca"}
NIGHTSHADE_GENERA = {"solanum", "capsicum", "physalis", "lycopersicon"}
ALLIUM_GENERA = {"allium"}
CUCURBIT_GENERA = {"cucumis", "cucurbita", "citrullus", "lagenaria", "luffa"}
LEGUME_GENERA = {
    "phaseolus", "pisum", "vigna", "glycine", "lens", "cicer", "arachis",
    "lablab", "vicia",
}
ROOT_CROP_GENERA = {
    "daucus", "beta", "raphanus", "pastinaca", "apium", "scorzonera",
    "tragopogon", "ipomoea_batatas",
}
GRAIN_GENERA = {"zea", "hordeum", "triticum", "avena", "oryza"}

FRUIT_GENERA = {
    "fragaria", "vaccinium", "rubus", "vitis", "citrus", "malus", "prunus",
    "musa", "ananas", "ribes", "morus", "punica", "diospyros", "actinidia",
    "passiflora", "carica", "psidium", "olea",
}

HERB_GENERA = {
    "ocimum", "mentha", "thymus", "origanum", "petroselinum", "coriandrum",
    "anethum", "lavandula", "cymbopogon", "stevia", "nepeta", "melissa",
    "satureja", "levisticum", "borago", "artemisia", "foeniculum",
    "pimpinella", "carum", "ruta", "hyssopus", "marrubium",
}

# Grown for their flowers rather than eaten
ORNAMENTAL_FLOWER_GENERA = {
    "tagetes", "zinnia", "cosmos", "helianthus", "petunia", "viola",
    "impatiens", "ageratum", "celosia", "amaranthus", "centaurea",
    "gypsophila", "callistephus", "bellis", "pelargonium", "tropaeolum",
    "lobularia", "catharanthus", "dahlia", "echinacea", "rudbeckia",
    "achillea", "gaillardia", "asclepias", "iberis", "coreopsis",
    "leucanthemum", "delphinium", "dianthus", "digitalis", "geranium",
    "hosta", "alcea", "lupinus", "penstemon", "phlox", "papaver", "primula",
    "tanacetum", "plectranthus", "antirrhinum", "calendula", "nigella",
    "rudbeckias", "lathyrus", "ipomoea", "clematis", "rosa", "hydrangea",
    "hemerocallis", "iris", "narcissus", "tulipa", "lilium", "begonia",
}
CUT_FLOWER_GENERA = {
    "zinnia", "cosmos", "dahlia", "helianthus", "gypsophila", "callistephus",
    "delphinium", "dianthus", "phlox", "echinacea", "rudbeckia",
    "leucanthemum", "antirrhinum", "lathyrus", "rosa", "lilium",
}
# Vining growers that want something to climb, outdoors
OUTDOOR_VINE_GENERA = {
    "ipomoea", "lathyrus", "pisum", "phaseolus", "vigna", "vitis", "cucumis",
    "cucurbita", "citrullus", "passiflora", "clematis", "lonicera", "humulus",
    "lagenaria", "luffa",
}
# Trailing/vining houseplants that are not the aerial-root climbers above
INDOOR_VINE_GENERA = {
    "tradescantia", "hoya", "cissus", "senecio", "curio", "ceropegia",
    "peperomia", "chlorophytum", "saxifraga",
}

# Genera that mix edible and ornamental species — resolved on the full name.
BINOMIAL_OVERRIDES: dict[str, set[str]] = {
    "salvia officinalis": {"herb"},
    "salvia rosmarinus": {"herb"},
    "rosmarinus officinalis": {"herb"},
    "salvia splendens": {"ornamental"},
    "allium schoenoprasum": {"herb"},
    "beta vulgaris": {"root-crop", "vegetable"},
    "solanum tuberosum": {"root-crop", "vegetable"},
    "ipomoea batatas": {"root-crop", "vegetable"},
    "ipomoea alba": {"ornamental"},
    "ipomoea purpurea": {"ornamental"},
    "tropaeolum majus": {"ornamental", "edible-flower"},
    "cucumis melo": {"fruit", "cucurbit"},
    "citrullus lanatus": {"fruit", "cucurbit"},
    "zea mays": {"vegetable"},
    "asparagus officinalis": {"vegetable"},
    "cynara scolymus": {"vegetable"},
    "lactuca sativa": {"vegetable", "leafy-green"},
    "spinacia oleracea": {"vegetable", "leafy-green"},
    "abelmoschus esculentus": {"vegetable"},
}

# --- Free-text cues -----------------------------------------------------------
# Fallbacks for species outside the genus sets (the expansion-sourced records,
# mostly). Matched case-insensitively against care_notes + schedule notes.

OUTDOOR_CUES = (
    "last frost", "first frost", "frost", "hardiness", "usda", "zone",
    "direct sow", "sow outdoors", "transplant outdoors", "row",
    "harvest", "overwinter", "crop rotation", "rotate crops", "garden bed",
    "raised bed", "full sun", "mulch", "deadhead", "self-sow", "perennial bed",
    "spacing", "in the garden",
)
# Deliberately excludes a bare "indoors": "start seeds indoors before last
# frost" describes an outdoor crop's sowing step, not an indoor plant. Only
# signals that mean the plant *lives* inside count here.
INDOOR_CUES = (
    "houseplant", "humidifier", "pebble tray", "damp cloth",
    "bright indirect", "away from drafts", "north-facing", "windowsill",
)
HARD_WATER_CUES = (
    "filtered", "distilled", "fluoride", "chlorine", "chloride", "hard water",
    "brown tip", "crispy",
)
SUPPORT_CUES = (
    "stake", "staking", "support", "trellis", "cage", "moss pole", "tie up",
    "tall stems", "flops",
)
CLIMB_CUES = ("moss pole", "climb", "aerial root", "totem")
VINE_CUES = ("vine", "vining", "trailing", "climb", "runner")
SEED_CUES = ("seed", "sow", "germinat")
# Checked against the propagation trait, where "cutting" can only mean the
# propagation method. In free-text care notes it also means "cutting garden"
# and "cutting back", so notes are matched on the fuller phrases only.
CUTTING_TRAIT_CUES = ("cutting", "cuttings", "air layering")
CUTTING_NOTE_CUES = ("stem cutting", "leaf cutting", "root in water",
                     "roots in water", "propagate from cutting")

_SOIL_CLASSES = (
    # (tag, substrings). First match wins, so the specific ones come first.
    ("soil-orchid", ("orchid bark", "coarse orchid", "bark (not potting")),
    ("soil-cactus", ("cactus", "succulent mix")),
    ("soil-aroid", ("aroid", "bark, perlite", "coco coir")),
    ("soil-acidic", ("acidic", "ph 4.", "ph 5.0", "ph 5.2", "acid soil")),
    ("soil-seed-start", ("sprouter", "no soil needed", "peat moss growing medium")),
    ("soil-moisture-retentive", ("moisture-retentive", "moisture retentive",
                                 "moist,", "consistently moist", "peat-based")),
)


def _norm(text: Optional[str]) -> str:
    return (text or "").lower()


@lru_cache(maxsize=512)
def _cue_pattern(cue: str) -> re.Pattern:
    """Word-start match for a cue phrase.

    Anchored at the front only, so "sow" still catches "sows"/"sowing" and
    "row" catches "rows" — but not "grow", which naive substring matching hit
    and which appears in nearly every care note in the catalog."""
    return re.compile(r"\b" + re.escape(cue))


def _has_any(haystack, needles: Iterable[str]) -> bool:
    """Cue search over text, or plain membership when given a tag set."""
    if isinstance(haystack, (set, frozenset, dict)):
        return any(n in haystack for n in needles)
    return any(_cue_pattern(n).search(haystack) for n in needles)


@dataclass
class PlantProfile:
    """Derived tags plus the evidence for each one."""
    tags: set[str] = field(default_factory=set)
    evidence: dict[str, str] = field(default_factory=dict)
    genus: str = ""
    common_name: str = ""
    care_types: set[str] = field(default_factory=set)

    def add(self, tag: str, why: str) -> None:
        self.tags.add(tag)
        self.evidence.setdefault(tag, why)

    def has(self, tag: str) -> bool:
        return tag in self.tags


def _lowest_zone(zone_text: str) -> Optional[int]:
    """The coldest USDA zone in a trait value like '9-10' or '4a to 8b'."""
    numbers = [int(n) for n in re.findall(r"\d+", zone_text or "")]
    return min(numbers) if numbers else None


def _binomial(scientific_name: str) -> tuple[str, str]:
    """(genus, 'genus species') in lowercase, punctuation stripped."""
    cleaned = re.sub(r"[^a-zA-Z ]+", " ", _norm(scientific_name))
    parts = [p for p in cleaned.split() if p]
    genus = parts[0] if parts else ""
    binom = " ".join(parts[:2]) if len(parts) >= 2 else genus
    return genus, binom


def derive_profile(species, schedules=None, traits=None) -> PlantProfile:
    """Classify a species record into product-matching tags.

    `species` is anything with the Species field names (the SQLModel row, or a
    simple namespace in tests). `schedules` and `traits` default to whatever
    the object carries as relationships."""
    schedules = list(schedules if schedules is not None
                     else getattr(species, "care_schedules", []) or [])
    traits = list(traits if traits is not None
                  else getattr(species, "traits", []) or [])

    p = PlantProfile()
    genus, binom = _binomial(getattr(species, "scientific_name", ""))
    p.genus = genus
    p.common_name = getattr(species, "common_name", "") or ""

    trait_map = {
        _norm(getattr(t, "trait", "")): _norm(getattr(t, "value", ""))
        for t in traits
    }
    notes = " ".join([
        _norm(getattr(species, "care_notes", "")),
        " ".join(_norm(getattr(s, "notes", "")) for s in schedules),
    ])
    soil = _norm(getattr(species, "soil_type", ""))
    common = _norm(getattr(species, "common_name", ""))

    # --- Soil class -----------------------------------------------------------
    for tag, needles in _SOIL_CLASSES:
        if _has_any(soil, needles):
            p.add(tag, f"soil_type: {getattr(species, 'soil_type', '')}")
            break
    if "ph" in soil:
        p.add("soil-ph-specified", f"soil_type names a pH range")
    if _has_any(soil, ("rich", "fertile")):
        p.add("soil-rich", f"soil_type: {getattr(species, 'soil_type', '')}")
    if _has_any(soil, ("garden", "loam", "raised bed", "average soil",
                       "well-drained soil", "well-draining soil")):
        p.add("soil-garden", f"soil_type: {getattr(species, 'soil_type', '')}")
    # Anything with no more specific class falls back to a standard mix.
    if not any(t.startswith("soil-") and t not in
               ("soil-ph-specified", "soil-rich", "soil-garden")
               for t in p.tags):
        p.add("soil-standard", f"soil_type: {getattr(species, 'soil_type', '')}")

    # --- Light ----------------------------------------------------------------
    light = _norm(getattr(getattr(species, "light_need", ""), "value",
                          getattr(species, "light_need", "")))
    light_tag = {
        "low": "light-low", "medium": "light-medium",
        "bright_indirect": "light-bright-indirect", "direct": "light-direct",
    }.get(light)
    if light_tag:
        p.add(light_tag, f"light_need: {light}")

    # --- Humidity -------------------------------------------------------------
    h_min = getattr(species, "humidity_pct_min", 0) or 0
    h_max = getattr(species, "humidity_pct_max", 0) or 0
    if h_min >= 55 or h_max >= 75:
        p.add("humidity-high", f"humidity range {h_min}-{h_max}%")
    elif h_max <= 45:
        p.add("humidity-low", f"humidity range {h_min}-{h_max}%")
    else:
        p.add("humidity-moderate", f"humidity range {h_min}-{h_max}%")

    # --- Care schedules -------------------------------------------------------
    for s in schedules:
        ct = _norm(getattr(getattr(s, "care_type", ""), "value",
                           getattr(s, "care_type", "")))
        if not ct:
            continue
        p.care_types.add(ct)
        p.add(f"care-{ct}", f"has a {ct} schedule")
        if ct == "water":
            lo = getattr(s, "interval_days_min", 0) or 0
            if lo and lo <= 4:
                p.add("water-frequent", f"waters every {lo}+ days")
            elif lo >= 14:
                p.add("water-infrequent", f"waters every {lo}+ days")
            else:
                p.add("water-regular", f"waters every {lo}+ days")
        if ct == "fertilize":
            lo = getattr(s, "interval_days_min", 0) or 0
            if lo and lo <= 21:
                p.add("feeder-heavy", f"fertilizes every {lo}+ days")
            elif lo >= 60:
                p.add("feeder-light", f"fertilizes every {lo}+ days")

    # --- Toxicity -------------------------------------------------------------
    if getattr(species, "toxic_to_pets", False):
        p.add("pet-toxic", "toxic_to_pets is true")
    else:
        p.add("pet-safe", "toxic_to_pets is false")

    # --- Botanical form -------------------------------------------------------
    if genus in AROID_GENERA:
        p.add("aroid", f"{genus.title()} is an aroid (Araceae)")
        if not any(t.startswith("soil-") and t == "soil-aroid" for t in p.tags):
            p.add("soil-aroid", f"{genus.title()} wants a chunky aroid mix")
    if genus in CLIMBING_AROIDS or _has_any(notes, CLIMB_CUES):
        p.add("climber", "climbs — aerial roots grip a pole")
    if genus in SUCCULENT_GENERA:
        p.add("succulent", f"{genus.title()} is a succulent")
    if genus in CACTUS_GENERA:
        p.add("cactus", f"{genus.title()} is a cactus (Cactaceae)")
        p.add("succulent", f"{genus.title()} is a cactus (Cactaceae)")
    if genus in ORCHID_GENERA:
        p.add("orchid", f"{genus.title()} is an orchid")
        p.add("soil-orchid", "orchids are potted in bark, not soil")
    if genus in FERN_GENERA:
        p.add("fern", f"{genus.title()} is a fern")
    if genus in PALM_GENERA:
        p.add("palm", f"{genus.title()} is a palm")

    # --- Use / crop group -----------------------------------------------------
    overrides = BINOMIAL_OVERRIDES.get(binom, set())
    for tag in overrides:
        p.add(tag, f"{binom.title()} classified by species")

    if genus in BRASSICA_GENERA:
        p.add("brassica", f"{genus.title()} is a brassica")
        p.add("vegetable", f"{genus.title()} is a brassica crop")
    if genus in NIGHTSHADE_GENERA:
        p.add("nightshade", f"{genus.title()} is a nightshade (Solanaceae)")
        p.add("vegetable", f"{genus.title()} is grown as a vegetable crop")
    if genus in ALLIUM_GENERA and "herb" not in overrides:
        p.add("allium", f"{genus.title()} is an allium")
        p.add("vegetable", f"{genus.title()} is an allium crop")
    if genus in CUCURBIT_GENERA:
        p.add("cucurbit", f"{genus.title()} is a cucurbit")
        if "fruit" not in p.tags:
            p.add("vegetable", f"{genus.title()} is a cucurbit crop")
    if genus in LEGUME_GENERA:
        p.add("legume", f"{genus.title()} is a legume")
        if "ornamental" not in overrides and genus not in ORNAMENTAL_FLOWER_GENERA:
            p.add("vegetable", f"{genus.title()} is a legume crop")
    if genus in ROOT_CROP_GENERA:
        p.add("root-crop", f"{genus.title()} is grown for its root")
        p.add("vegetable", f"{genus.title()} is a root crop")
    if genus in GRAIN_GENERA:
        p.add("vegetable", f"{genus.title()} is a field crop")
    if genus in FRUIT_GENERA:
        p.add("fruit", f"{genus.title()} is grown for fruit")
    if genus in HERB_GENERA or "herb" in overrides:
        p.add("herb", f"{genus.title()} is a culinary herb")
    if genus in ORNAMENTAL_FLOWER_GENERA and "herb" not in p.tags \
            and "vegetable" not in p.tags:
        p.add("ornamental", f"{genus.title()} is grown ornamentally")
        p.add("flowering", f"{genus.title()} is grown for its flowers")
    if genus in CUT_FLOWER_GENERA:
        p.add("cut-flower", f"{genus.title()} is a cutting-garden flower")

    if _has_any(p.tags, {"vegetable", "fruit", "herb"}):
        p.add("edible", "grown to eat")

    # Text fallback for species outside every genus set above.
    if not _has_any(p.tags, {"ornamental", "edible", "aroid", "succulent",
                             "orchid", "fern", "palm", "cactus"}):
        if _has_any(notes + " " + common, ("bloom", "flower", "deadhead", "petal")):
            p.add("flowering", "care notes describe flowering")
            p.add("ornamental", "care notes describe flowering")

    # --- Vining / support -----------------------------------------------------
    if genus in OUTDOOR_VINE_GENERA or genus in INDOOR_VINE_GENERA \
            or _has_any(notes, VINE_CUES):
        p.add("vine", "vining or trailing growth")
    if _has_any(notes, SUPPORT_CUES):
        p.add("needs-support", "care notes call for staking or support")

    height_raw = trait_map.get("max_height_inches", "")
    try:
        if height_raw and float(re.sub(r"[^0-9.]", "", height_raw) or 0) >= 48:
            p.add("tall", f"grows to {height_raw} inches")
    except ValueError:
        pass

    # --- Setting: indoor vs outdoor -------------------------------------------
    outdoor_evidence = []
    if "hardiness_zone" in trait_map:
        outdoor_evidence.append("has a hardiness zone")
    if _has_any(notes, OUTDOOR_CUES):
        outdoor_evidence.append("care notes describe outdoor growing")
    if _has_any(p.tags, {"vegetable", "fruit", "cut-flower"}):
        outdoor_evidence.append("grown as an outdoor crop")
    if genus in OUTDOOR_VINE_GENERA or genus in ORNAMENTAL_FLOWER_GENERA:
        outdoor_evidence.append("grown as a garden plant")

    indoor_evidence = []
    if _has_any(notes, INDOOR_CUES):
        indoor_evidence.append("care notes describe indoor growing")
    if _has_any(p.tags, {"aroid", "orchid", "fern", "palm"}):
        indoor_evidence.append("kept as a houseplant")
    if _has_any(p.tags, {"succulent", "cactus"}):
        indoor_evidence.append("commonly kept indoors")

    if outdoor_evidence:
        p.add("outdoor", outdoor_evidence[0])
    if indoor_evidence or not outdoor_evidence:
        # Default to indoor: this is a houseplant app, and an indoor
        # recommendation for an outdoor plant is a smaller error than the
        # reverse (frost cloth for a Monstera).
        p.add("indoor", indoor_evidence[0] if indoor_evidence
              else "kept as a container/houseplant by default")
    if "outdoor" in p.tags and "indoor" not in p.tags:
        p.add("outdoor-only", "grown outdoors")
    if "indoor" in p.tags and "outdoor" not in p.tags:
        p.add("indoor-only", "grown indoors")

    # --- Miscellaneous flags --------------------------------------------------
    if _has_any(notes, HARD_WATER_CUES):
        p.add("hard-water-sensitive",
              "care notes flag tap-water sensitivity or brown tips")
    # Frost sensitivity: a stated minimum above freezing, unless the hardiness
    # zone says otherwise. The expansion pipeline defaults temp_f_min to 40 for
    # records with no temperature data, which would otherwise tag a zone-4
    # perennial as needing frost protection — the zone is the better evidence
    # wherever both exist.
    temp_min = getattr(species, "temp_f_min", 0) or 0
    zone_low = _lowest_zone(trait_map.get("hardiness_zone", ""))
    if "outdoor" in p.tags and temp_min >= 35 and (zone_low is None or zone_low >= 8):
        p.add("frost-sensitive",
              f"minimum temperature {temp_min}F is above freezing"
              + (f" (hardiness zone {trait_map['hardiness_zone']})"
                 if zone_low is not None else ""))
    elif zone_low is not None and zone_low <= 6:
        p.add("frost-hardy", f"hardy to zone {trait_map['hardiness_zone']}")

    prop = trait_map.get("propagation", "")
    if _has_any(prop + " " + notes, SEED_CUES):
        p.add("seed-started", f"propagation: {prop}" if prop
              else "care notes describe sowing")
    if _has_any(prop, CUTTING_TRAIT_CUES) or _has_any(notes, CUTTING_NOTE_CUES):
        p.add("cutting-propagated", f"propagation: {prop}" if prop
              else "care notes describe cuttings")

    return p


def explain(profile: PlantProfile, tags: Iterable[str]) -> list[str]:
    """The evidence lines behind the given tags, de-duplicated, in order."""
    seen, out = set(), []
    for t in tags:
        why = profile.evidence.get(t)
        if why and why not in seen:
            seen.add(why)
            out.append(why)
    return out
