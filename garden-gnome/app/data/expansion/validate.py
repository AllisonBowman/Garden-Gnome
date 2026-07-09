"""Automated validation for catalog records, regardless of source.

Three families of checks:
  1. Missing/placeholder fields
  2. Biologically implausible values (houseplant context)
  3. Near-duplicate names (within the batch and against the existing catalog)

Records with any issue are routed to the review queue, never auto-approved.
"""
import re
from difflib import SequenceMatcher

VALID_LIGHT = {"low", "medium", "bright_indirect", "direct"}

# Plausibility windows (days) per care type: (min allowed, max allowed)
SCHEDULE_WINDOWS = {
    "water": (1, 90),
    "fertilize": (7, 365),
    "mist": (1, 30),
    "prune": (1, 730),  # herbs get pinched weekly; bloomers deadheaded daily
    "repot": (90, 2200),
    "rotate": (7, 120),
    "clean": (7, 180),
    "other": (1, 3650),
}

_PLACEHOLDER = re.compile(
    r"fill in|placeholder|\bunknown\b|\btbd\b|(?:^|\s)n/?a$", re.IGNORECASE
)


def validate_record(rec: dict) -> list[str]:
    """Return a list of issues; empty list means the record passes."""
    issues: list[str] = []

    # -- Missing / placeholder fields ----------------------------------------
    for field in ("common_name", "scientific_name", "soil_type", "care_notes"):
        val = str(rec.get(field, "")).strip()
        if not val:
            issues.append(f"missing {field}")
        elif _PLACEHOLDER.search(val):
            issues.append(f"placeholder text in {field}: {val[:60]!r}")

    sci = str(rec.get("scientific_name", "")).strip()
    if sci and not re.match(r"^[A-Z][a-zA-Z-]+( [a-z×'.‘’-]+)?", sci):
        issues.append(f"scientific_name doesn't look like binomial nomenclature: {sci!r}")

    if rec.get("light_need") not in VALID_LIGHT:
        issues.append(f"invalid light_need: {rec.get('light_need')!r}")

    # -- Biologically implausible values --------------------------------------
    try:
        h_lo, h_hi = int(rec["humidity_pct_min"]), int(rec["humidity_pct_max"])
        if not (0 <= h_lo < h_hi <= 100):
            issues.append(f"implausible humidity range {h_lo}-{h_hi}%")
        elif h_hi - h_lo < 5:
            issues.append(f"suspiciously narrow humidity range {h_lo}-{h_hi}%")
    except (KeyError, TypeError, ValueError):
        issues.append("humidity values missing or non-numeric")

    try:
        t_lo, t_hi = int(rec["temp_f_min"]), int(rec["temp_f_max"])
        if not (t_lo < t_hi):
            issues.append(f"temp min >= max ({t_lo} >= {t_hi})")
        if t_lo < 25 or t_lo > 75:
            issues.append(f"implausible houseplant temp_f_min {t_lo}")
        if t_hi < 60 or t_hi > 115:
            issues.append(f"implausible houseplant temp_f_max {t_hi}")
    except (KeyError, TypeError, ValueError):
        issues.append("temperature values missing or non-numeric")

    # -- Schedules -------------------------------------------------------------
    schedules = rec.get("schedules") or []
    types = [s.get("care_type") for s in schedules]
    if "water" not in types:
        issues.append("no water schedule")
    if len(types) != len(set(types)):
        issues.append("duplicate care_type in schedules")
    for s in schedules:
        ct = s.get("care_type", "?")
        try:
            lo, hi = int(s["interval_days_min"]), int(s["interval_days_max"])
        except (KeyError, TypeError, ValueError):
            issues.append(f"{ct}: interval missing or non-numeric")
            continue
        if lo > hi:
            issues.append(f"{ct}: interval min {lo} > max {hi}")
        window = SCHEDULE_WINDOWS.get(ct)
        if window and not (window[0] <= lo and hi <= window[1]):
            issues.append(
                f"{ct}: interval {lo}-{hi}d outside plausible window "
                f"{window[0]}-{window[1]}d"
            )

    if not isinstance(rec.get("toxic_to_pets"), bool):
        issues.append("toxic_to_pets is not a boolean")

    return issues


# ── Near-duplicate detection ──────────────────────────────────────────────────

def _name_key(name: str) -> str:
    """Normalize for exact-duplicate comparison: case, whitespace, cultivar
    quotes, and the abbreviation dot in 'var.' etc."""
    s = (name or "").lower().strip()
    s = re.sub(r"['‘’\"]", "", s)
    s = re.sub(r"\s+", " ", s)
    return s


def find_near_duplicates(
    new_records: list[dict],
    existing_names: list[tuple[str, str]],
    threshold: float = 0.94,
) -> dict[str, list[str]]:
    """Detect exact-normalized and fuzzy near-duplicate names.

    new_records: SpeciesCreate-shaped dicts (compared to each other AND to
    existing). existing_names: (common_name, scientific_name) already in DB.
    Returns {scientific_name_of_new_record: [reasons]}.
    """
    flags: dict[str, list[str]] = {}

    def add(rec_sci: str, reason: str) -> None:
        flags.setdefault(rec_sci, []).append(reason)

    existing_sci = {_name_key(s): s for _, s in existing_names if s}
    existing_common = {_name_key(c): c for c, _ in existing_names if c}

    seen_sci: dict[str, str] = {}
    seen_common: dict[str, str] = {}
    all_sci_keys: list[tuple[str, str]] = list(existing_sci.items())

    for rec in new_records:
        sci_raw = rec.get("scientific_name", "")
        sci = _name_key(sci_raw)
        common = _name_key(rec.get("common_name", ""))

        if sci in existing_sci:
            add(sci_raw, f"scientific name already in catalog: {existing_sci[sci]!r}")
        if sci in seen_sci:
            add(sci_raw, f"duplicate scientific name within batch: {seen_sci[sci]!r}")
        if common and common in existing_common:
            add(sci_raw, f"common name already in catalog: {existing_common[common]!r}")
        if common and common in seen_common:
            add(sci_raw, f"duplicate common name within batch: {seen_common[common]!r}")

        for other_key, other_raw in all_sci_keys:
            if not sci or sci == other_key:
                continue
            # Cultivar/variant containment: "epipremnum aureum golden" vs
            # "epipremnum aureum" — fuzzy ratio misses these, prefix test doesn't
            if sci.startswith(other_key + " ") or other_key.startswith(sci + " "):
                add(sci_raw, f"near-duplicate of {other_raw!r} (cultivar/variant)")
                continue
            # Fuzzy pass for typo-level duplicates (quick length/prefix
            # prefilter keeps the O(n²) comparison cheap at ~2k records)
            if abs(len(sci) - len(other_key)) > 6 or sci[0] != other_key[0]:
                continue
            if SequenceMatcher(None, sci, other_key).ratio() >= threshold:
                add(sci_raw, f"near-duplicate of {other_raw!r}")

        seen_sci.setdefault(sci, sci_raw)
        if common:
            seen_common.setdefault(common, rec.get("common_name", ""))
        all_sci_keys.append((sci, sci_raw))

    return flags
