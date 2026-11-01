"""Read the verified tranche as evidence rather than as values.

Each record in `app/data/verified/b*.json` carries the fields a researcher
filled in and the citations they worked from. This module pairs them back up:
a field becomes a Claim only when some citation actually mentions it.

The pairing is by name. Citation text in the tranche leads with the field it
supports ("humidity_need low", "water_regime dry_thoroughly_between;
water_dormant_days_est 45"), and some cite a range once for a pair of columns
("day_f 70-85" covers day_f_min and day_f_max), which is what STEMS handles.
"""
import re
from dataclasses import dataclass
from typing import Any

from .authorities import authority_for, authority_may_claim
from .names import canonical
from .resolve import Authority

# Bookkeeping on the record, not claims about the plant.
NOT_A_FIELD = frozenset({
    "common_name", "scientific_name_given", "scientific_name_accepted",
    "name_note", "citations", "unknowns",
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

# A listing that keeps a plant off every candidate list -- a noxious weed, an
# invasive species (toxicity.never_put_forward, ADR 0009) -- is evidence
# wherever the researcher filed the citation that holds it: NC State's tag
# sits under the pet flag, but a source's sentence on invasiveness is as often
# behind a name note or a size, and those never became claims. So any vetted
# citation whose quote holds one of the two phrases is stored as a claim of
# its own on this field (ADR 0011). No column takes it (it is not in
# recompute.RESOLVED_FIELDS); the safety code reads the quotes back.
WEED_FIELD = "weed_listing"
WEED_RE = re.compile(r"\bnoxious weed|\binvasive species\b", re.I)

# A citation may name the stem once and thereby support both columns.
STEMS = {
    "day_f_min": "day_f", "day_f_max": "day_f",
    "night_f_min": "night_f", "night_f_max": "night_f",
    "soil_ph_min": "soil_ph", "soil_ph_max": "soil_ph",
    "humidity_pct_min": "humidity_pct", "humidity_pct_max": "humidity_pct",
    # Sources publish mature size as a range in one breath -- "3 to 6 feet" --
    # so one citation reading `mature_height_in 36-72` supports both bounds.
    "mature_height_in_min": "mature_height_in",
    "mature_height_in_max": "mature_height_in",
    "mature_spread_in_min": "mature_spread_in",
    "mature_spread_in_max": "mature_spread_in",
}


@dataclass(frozen=True)
class ExtractedClaim:
    """One field's value with the citation that supports it, ready to store.

    `authority` is the organisation, resolved from the citation's URL;
    `citation_title` is the individual document. Keeping them apart is what
    lets tier mean something — see authorities.py.
    """
    subject: str
    field: str
    value: Any
    authority: Authority
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
    # Canonical spelling (the hybrid marker spaced), so one plant has one
    # subject string however its sources spelled it; sync._subject_of is the
    # same expression and the two must not drift.
    subject = canonical(record.get("scientific_name_accepted")
                        or record.get("scientific_name_given"))
    citations = record.get("citations") or []

    claims: list[ExtractedClaim] = []
    unsupported: list[str] = []

    for field, value in record.items():
        if field in NOT_A_FIELD or value in (None, "", []):
            continue
        # Only citations from a vetted publisher can support a value, and only
        # for the fields that publisher is trusted on. One from an unknown
        # domain has no tier to weigh it by and no licence on record; one from
        # a scoped authority (USDA PLANTS, trusted for names and a minimum
        # outdoor temperature only) is not a general care-data source just
        # because its URL resolves. Either way the field is reported, not
        # silently dropped.
        support = None
        for c in citations:
            authority = authority_for(c.get("url"), c.get("source", ""))
            if (authority is not None
                    and _supports(c.get("claim", ""), field)
                    and authority_may_claim(authority.name, field)):
                support = c
                break
        if support is None:
            unsupported.append(field)
            continue
        claims.append(ExtractedClaim(
            subject=subject,
            field=field,
            value=value,
            authority=authority_for(support.get("url"), support.get("source", "")),
            citation_title=support.get("source", ""),
            citation_url=support.get("url", ""),
            quote=support.get("quote", ""),
        ))

    for c in citations:
        if not WEED_RE.search(c.get("quote") or ""):
            continue
        authority = authority_for(c.get("url"), c.get("source", ""))
        if authority is None or not authority_may_claim(authority.name, WEED_FIELD):
            continue
        claims.append(ExtractedClaim(
            subject=subject, field=WEED_FIELD, value=True, authority=authority,
            citation_title=c.get("source", ""), citation_url=c.get("url", ""),
            quote=c.get("quote", "")))
    return claims, unsupported
