"""Read the verified tranche as evidence rather than as values.

Each record in `app/data/verified/b*.json` carries the fields a researcher
filled in and the citations they worked from. This module pairs them back up:
a field becomes a Claim only when some citation actually mentions it.

The pairing is by name. Citation text in the tranche leads with the field it
supports ("humidity_need low", "water_regime dry_thoroughly_between;
water_dormant_days_est 45"), and some cite a range once for a pair of columns
("day_f 70-85" covers day_f_min and day_f_max), which is what STEMS handles.
"""
from dataclasses import dataclass
from typing import Any

# Bookkeeping on the record, not claims about the plant.
NOT_A_FIELD = frozenset({
    "common_name", "scientific_name_given", "scientific_name_accepted",
    "name_note", "citations", "unknowns", "is_houseplant",
    # The researcher's own reasoning about an estimate -- which pot, which
    # medium, what light. No source said it, so filing it as evidence would
    # attribute our assumptions to an authority.
    "water_estimate_basis", "cool_rest_note",
})

# Fields that are the readable restatement of a structured neighbour: one fact
# recorded twice, from one citation. They inherit that citation rather than
# counting as unsupported.
COMPANIONS = {
    "toxicity_detail": "toxic_to_pets",
    "water_dry_down_target": "water_regime",
}

# A citation may name the stem once and thereby support both columns.
STEMS = {
    "day_f_min": "day_f", "day_f_max": "day_f",
    "night_f_min": "night_f", "night_f_max": "night_f",
    "soil_ph_min": "soil_ph", "soil_ph_max": "soil_ph",
    "humidity_pct_min": "humidity_pct", "humidity_pct_max": "humidity_pct",
}


@dataclass(frozen=True)
class ExtractedClaim:
    """One field's value with the citation that supports it, ready to store."""
    subject: str
    field: str
    value: Any
    authority_name: str
    citation_title: str
    citation_url: str
    quote: str


def _supports(citation_text: str, field: str) -> bool:
    for name in (field, COMPANIONS.get(field), STEMS.get(field)):
        if name and name in citation_text:
            return True
    return False


def claims_from_record(record: dict) -> tuple[list[ExtractedClaim], list[str]]:
    """Split one tranche record into supported Claims and unsupported fields.

    Returns the claims, and the names of any field that held a value no
    citation mentions — those are reported rather than loaded, because a value
    with nothing behind it is the thing this whole exercise exists to remove.
    """
    subject = (record.get("scientific_name_accepted")
               or record.get("scientific_name_given") or "").strip()
    citations = record.get("citations") or []

    claims: list[ExtractedClaim] = []
    unsupported: list[str] = []

    for field, value in record.items():
        if field in NOT_A_FIELD or value in (None, "", []):
            continue
        support = next(
            (c for c in citations if _supports(c.get("claim", ""), field)), None)
        if support is None:
            unsupported.append(field)
            continue
        claims.append(ExtractedClaim(
            subject=subject,
            field=field,
            value=value,
            authority_name=support.get("source", ""),
            citation_title=support.get("source", ""),
            citation_url=support.get("url", ""),
            quote=support.get("quote", ""),
        ))
    return claims, unsupported
