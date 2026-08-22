"""Who published a citation.

An Authority is the organisation; the Citation is the document. Tier attaches
to the organisation, so a claim's weight does not depend on which factsheet it
came off.

Resolution is by domain. The `source` title in the tranche is prose written per
citation — Clemson Cooperative Extension appears under seventeen different
title strings, and one citation credits two bodies in its title while linking
to a page belonging to only one of them. A domain is canonical; a title is not.

A domain that is not registered here resolves to nothing. That is deliberate:
an unvetted publisher has no tier to weigh its claims by and no licence on
record, and admitting it would put both problems into the catalog silently.
"""
from urllib.parse import urlparse

from .resolve import Authority

# Every publisher whose claims the catalog will accept, keyed by the domains
# they serve from. Tier 2 entries are university extension services and major
# botanical gardens: reputable, editorially reviewed, and copyrighted — we may
# state their facts with attribution, but their words stay server-side
# (ADR 0003). We have no principled basis for ranking one above another, so
# they stay level and their disagreements are settled by resolve.py's
# deterministic tie-break rather than an invented pecking order.
EXTENSION_LICENCE = "copyright; facts cited with attribution, quotes not redistributed"

# A federal work carries no copyright at all (17 U.S.C. § 105), which is a
# stronger position than "cited with attribution" — nothing here needs
# holding back the way an extension service's prose does.
PUBLIC_DOMAIN_LICENCE = "U.S. government work; public domain (17 U.S.C. § 105)"

# Tier 1: open, bulk, and — for USDA PLANTS — deliberately narrow. It was
# investigated as a general care-data source and rejected: most of this
# catalog (Monstera, Pothos, Snake Plant, the tropical houseplant majority)
# does not appear in it at all, since it tracks native, agricultural and
# conservation species, not foreign ornamentals. Where it does carry a
# species, its Characteristics schema measures rangeland-establishment
# traits — moisture use, drought tolerance, precipitation range — which
# answer a different question than a potted plant's care. It earns tier 1
# for exactly what it is authoritative on: accepted names and USDA hardiness
# zones. `ALLOWED_FIELDS` below is what makes that scope a fact enforced by
# the loader rather than an intention that erodes the first time a citation
# happens to name a care field.
USDA_PLANTS_ALLOWED_FIELDS = frozenset({"hardiness_zones"})

REGISTRY: dict[str, tuple[str, int, str, frozenset[str] | None]] = {
    "plants.ces.ncsu.edu": ("NC State Extension", 2, EXTENSION_LICENCE, None),
    "hgic.clemson.edu": (
        "Clemson Cooperative Extension", 2, EXTENSION_LICENCE, None),
    "plantfinder.mobot.org": (
        "Missouri Botanical Garden", 2, EXTENSION_LICENCE, None),
    "www.missouribotanicalgarden.org": (
        "Missouri Botanical Garden", 2, EXTENSION_LICENCE, None),
    "edis.ifas.ufl.edu": ("UF/IFAS Extension", 2, EXTENSION_LICENCE, None),
    # Ask IFAS serves the same EDIS documents from a second domain -- caught
    # when a citation for FP512 turned up under ask.ifas.ufl.edu, attributed
    # to "UF/IFAS Extension (EDIS FPS512/FP512)", the identical publication.
    "ask.ifas.ufl.edu": ("UF/IFAS Extension", 2, EXTENSION_LICENCE, None),
    "www.rhs.org.uk": (
        "Royal Horticultural Society", 2, EXTENSION_LICENCE, None),
    "extension.psu.edu": ("Penn State Extension", 2, EXTENSION_LICENCE, None),
    "extension.umd.edu": (
        "University of Maryland Extension", 2, EXTENSION_LICENCE, None),
    "fieldreport.caes.uga.edu": (
        "UGA Cooperative Extension", 2, EXTENSION_LICENCE, None),
    # plants.usda.gov 301s to plants.sc.egov.usda.gov; a citation may carry
    # either, and both must resolve to the one authority.
    "plants.usda.gov": (
        "USDA PLANTS Database", 1, PUBLIC_DOMAIN_LICENCE,
        USDA_PLANTS_ALLOWED_FIELDS),
    "plants.sc.egov.usda.gov": (
        "USDA PLANTS Database", 1, PUBLIC_DOMAIN_LICENCE,
        USDA_PLANTS_ALLOWED_FIELDS),
}


def domain_of(url: str | None) -> str:
    if not url:
        return ""
    return (urlparse(url).netloc or "").lower()


def licence_of(name: str) -> str:
    """The licence recorded for an Authority, by name."""
    for authority_name, _tier, licence, _allowed in REGISTRY.values():
        if authority_name == name:
            return licence
    return ""


def allowed_fields_of(name: str) -> frozenset[str] | None:
    """The field scope for an Authority, by name. None means unrestricted.

    Consulted once, when a row is minted (ingest.py) -- not at resolution
    time. See Authority.allowed_fields on the model for why.
    """
    for authority_name, _tier, _licence, allowed in REGISTRY.values():
        if authority_name == name:
            return allowed
    return None


def authority_may_claim(name: str, field: str) -> bool:
    """Whether an Authority, by name, is trusted to support this field.

    Most authorities are unrestricted: an extension service that is vetted at
    all is vetted for the whole care schema. A registry entry may narrow that
    with an explicit allowlist — see USDA_PLANTS_ALLOWED_FIELDS above — and an
    unregistered name is trusted for nothing.
    """
    for authority_name, _tier, _licence, allowed in REGISTRY.values():
        if authority_name == name:
            return allowed is None or field in allowed
    return False


def authority_for(url: str | None, source_title: str) -> Authority | None:
    """The Authority behind a citation, or None if its publisher is unvetted.

    `source_title` is accepted so callers can pass what they have, but it is
    deliberately not consulted — see the module docstring.
    """
    entry = REGISTRY.get(domain_of(url))
    if entry is None:
        return None
    name, tier, _licence, _allowed = entry
    return Authority(name=name, tier=tier)
