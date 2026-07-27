"""Amazon Associates link building.

Two deliberate choices here:

**Search links, not pinned ASINs.** Every outbound link is a scoped Amazon
search rather than a specific product id. An ASIN goes dead the moment a
seller delists it, and a dead link in a care recommendation is worse than no
link — it reads as the app being wrong about the plant. A search stays valid
forever and, under the Associates program, still earns on whatever the visitor
buys within the cookie window. `AMAZON_PINNED_ASINS` exists as the upgrade path
once specific products have been verified (see AMAZON-AFFILIATE.md).

**No tag means no tag.** If `AMAZON_ASSOCIATE_TAG` is unset the links are built
without any tag at all. The alternative — shipping a plausible-looking
placeholder — would send real customer traffic to whichever stranger happens to
own that tag. Callers can check `is_configured()` and the API reports it, so an
unconfigured deployment is visible rather than silently unpaid.
"""
from __future__ import annotations

import re
from typing import Optional
from urllib.parse import quote_plus

from app.config import get_settings

# Amazon locales this app knows how to build links for. Each Associates
# account is per-marketplace: a .com tag earns nothing on a .co.uk sale, so the
# host and the tag have to move together.
MARKETPLACE_HOSTS = {
    "amazon.com": "www.amazon.com",
    "amazon.co.uk": "www.amazon.co.uk",
    "amazon.ca": "www.amazon.ca",
    "amazon.de": "www.amazon.de",
    "amazon.fr": "www.amazon.fr",
    "amazon.it": "www.amazon.it",
    "amazon.es": "www.amazon.es",
    "amazon.com.au": "www.amazon.com.au",
    "amazon.co.jp": "www.amazon.co.jp",
    "amazon.in": "www.amazon.in",
}
DEFAULT_MARKETPLACE = "amazon.com"

# Amazon search-index aliases (the `i=` parameter). Restricting to an allowlist
# keeps a typo in the product catalog from producing a search that silently
# returns nothing.
DEPARTMENTS = {
    "lawngarden",  # Garden & Outdoor
    "kitchen",     # Home & Kitchen
    "tools",       # Tools & Home Improvement
    "pets",        # Pet Supplies
    "grocery",     # Grocery & Gourmet Food
    "hpc",         # Health & Household
}

# Associates tags are of the form <storeid>-<number>, e.g. "plantadvocate-20".
_TAG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{1,48}-[0-9]{2}$")

DISCLOSURE = (
    "As an Amazon Associate, PlantAdvocate earns from qualifying purchases. "
    "Product links are suggestions based on this plant's care record — they "
    "never change the care advice itself."
)

DISCLOSURE_SHORT = "Paid link — we may earn a commission."


def associate_tag() -> str:
    """The configured Associates tracking id, or '' if none is set."""
    return (get_settings().amazon_associate_tag or "").strip()


def is_configured() -> bool:
    """True when a syntactically valid Associates tag is configured.

    Format is checked but not verified against Amazon — a malformed tag earns
    nothing and there is no API to confirm one without an approved account, so
    the shape check is the most that can be done here."""
    return bool(_TAG_RE.match(associate_tag()))


def marketplace() -> str:
    mk = (get_settings().amazon_marketplace or DEFAULT_MARKETPLACE).strip().lower()
    return mk if mk in MARKETPLACE_HOSTS else DEFAULT_MARKETPLACE


def _host() -> str:
    return MARKETPLACE_HOSTS[marketplace()]


def build_search_url(keywords: str, department: Optional[str] = None) -> str:
    """A tagged Amazon search URL for `keywords`.

    Raises ValueError on empty keywords — an untargeted search link is a
    recommendation to buy nothing in particular, which is worse than omitting
    the product."""
    terms = " ".join(keywords.split())
    if not terms:
        raise ValueError("keywords must not be empty")

    url = f"https://{_host()}/s?k={quote_plus(terms)}"
    if department and department in DEPARTMENTS:
        url += f"&i={department}"
    tag = associate_tag()
    if is_configured():
        url += f"&tag={quote_plus(tag)}"
    return url


def build_product_url(asin: str) -> str:
    """A tagged product-detail URL for a verified ASIN.

    Unused by the default catalog (which is search-only) and kept for the
    pinned-ASIN upgrade path once specific products have been checked as live."""
    asin = asin.strip().upper()
    if not re.fullmatch(r"[A-Z0-9]{10}", asin):
        raise ValueError(f"not a valid ASIN: {asin!r}")
    url = f"https://{_host()}/dp/{asin}"
    if is_configured():
        url += f"?tag={quote_plus(associate_tag())}"
    return url


def link_meta() -> dict:
    """Affiliate status for API responses — lets the client render the right
    disclosure and lets us see at a glance whether a deployment is earning."""
    return {
        "marketplace": marketplace(),
        "affiliate_configured": is_configured(),
        "disclosure": DISCLOSURE,
        "disclosure_short": DISCLOSURE_SHORT,
    }
