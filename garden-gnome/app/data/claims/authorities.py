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
# they serve from. All present entries are university extension services or
# major botanical gardens: reputable, editorially reviewed, and copyrighted —
# we may state their facts with attribution, but their words stay server-side
# (ADR 0003).
#
# Tier 1 is reserved for open bulk taxonomic sources (WFO, WCVP, USDA PLANTS)
# and tier 3 for boolean-only fallbacks (Wikipedia, Perenual). Neither appears
# in the verified tranche, so everything here is tier 2 — and because we have
# no principled basis for ranking one extension service above another, they
# stay level and their disagreements are settled by resolve.py's deterministic
# tie-break rather than by an invented pecking order.
EXTENSION_LICENCE = "copyright; facts cited with attribution, quotes not redistributed"

REGISTRY: dict[str, tuple[str, int, str]] = {
    "plants.ces.ncsu.edu": ("NC State Extension", 2, EXTENSION_LICENCE),
    "hgic.clemson.edu": ("Clemson Cooperative Extension", 2, EXTENSION_LICENCE),
    "plantfinder.mobot.org": ("Missouri Botanical Garden", 2, EXTENSION_LICENCE),
    "www.missouribotanicalgarden.org": (
        "Missouri Botanical Garden", 2, EXTENSION_LICENCE),
    "edis.ifas.ufl.edu": ("UF/IFAS Extension", 2, EXTENSION_LICENCE),
    "www.rhs.org.uk": ("Royal Horticultural Society", 2, EXTENSION_LICENCE),
    "extension.psu.edu": ("Penn State Extension", 2, EXTENSION_LICENCE),
    "extension.umd.edu": (
        "University of Maryland Extension", 2, EXTENSION_LICENCE),
    "fieldreport.caes.uga.edu": (
        "UGA Cooperative Extension", 2, EXTENSION_LICENCE),
}


def domain_of(url: str | None) -> str:
    if not url:
        return ""
    return (urlparse(url).netloc or "").lower()


def licence_of(name: str) -> str:
    """The licence recorded for an Authority, by name."""
    for authority_name, _tier, licence in REGISTRY.values():
        if authority_name == name:
            return licence
    return ""


def authority_for(url: str | None, source_title: str) -> Authority | None:
    """The Authority behind a citation, or None if its publisher is unvetted.

    `source_title` is accepted so callers can pass what they have, but it is
    deliberately not consulted — see the module docstring.
    """
    entry = REGISTRY.get(domain_of(url))
    if entry is None:
        return None
    name, tier, _licence = entry
    return Authority(name=name, tier=tier)
