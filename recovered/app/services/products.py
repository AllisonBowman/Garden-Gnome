"""Map a species (and optionally one user's plant) to Amazon product picks.

The rules live in `app/data/product_catalog.json`; the tags they match against
are derived in `plant_profile.py` from the species' own database record. This
module is the evaluator and the ranker — it holds no plant knowledge of its
own, so adding a product means editing JSON, not Python.

Ranking is deliberately conservative. A recommendation carries the app's voice,
so a weak match that merely *could* apply is worse than an empty category: it
teaches users that the suggestions are filler. Products are capped per category
and every one returned carries the species fields that justify it.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Optional

from app.services import affiliate
from app.services.plant_profile import PlantProfile, derive_profile, explain

CATALOG_PATH = Path(__file__).resolve().parent.parent / "data" / "product_catalog.json"

DEFAULT_PER_CATEGORY = 3
# A plant whose care is due gets its matching gear pushed up the list.
DUE_CARE_BONUS = 25
# Products whose care_types line up with schedules this species actually has.
SCHEDULE_MATCH_BONUS = 12


@lru_cache(maxsize=1)
def load_catalog() -> dict:
    with open(CATALOG_PATH, encoding="utf-8") as f:
        return json.load(f)


def _matches(rule: Optional[dict], tags: set[str]) -> tuple[bool, list[str]]:
    """Evaluate a match rule, returning (matched, tags that carried it).

    Empty/absent rule never matches — a product with no rule would attach to
    every plant in the catalog, which is exactly the filler we don't want."""
    if not rule:
        return False, []
    any_of = set(rule.get("any_of") or [])
    all_of = set(rule.get("all_of") or [])
    none_of = set(rule.get("none_of") or [])

    if not any_of and not all_of:
        return False, []
    if none_of & tags:
        return False, []
    if all_of and not all_of <= tags:
        return False, []
    if any_of and not (any_of & tags):
        return False, []
    return True, sorted((any_of & tags) | (all_of & tags))


def _score(product: dict, matched_tags: list[str], profile: PlantProfile,
           due_care_types: Iterable[str]) -> int:
    score = int(product.get("priority", 50))
    care_types = set(product.get("care_types") or [])
    if care_types & profile.care_types:
        score += SCHEDULE_MATCH_BONUS
    if care_types & set(due_care_types or ()):
        score += DUE_CARE_BONUS
    # Two independent reasons to recommend beats one.
    score += min(len(matched_tags), 3)
    return score


def recommend_for_profile(
    profile: PlantProfile,
    per_category: int = DEFAULT_PER_CATEGORY,
    categories: Optional[Iterable[str]] = None,
    due_care_types: Optional[Iterable[str]] = None,
) -> list[dict]:
    """Ranked product recommendations, grouped into categories."""
    catalog = load_catalog()
    wanted = set(categories) if categories else None
    due = set(due_care_types or ())

    by_category: dict[str, list[dict]] = {}
    for product in catalog["products"]:
        cat = product["category"]
        if wanted and cat not in wanted:
            continue
        ok, matched_tags = _matches(product.get("match"), profile.tags)
        if not ok:
            continue
        by_category.setdefault(cat, []).append({
            "id": product["id"],
            "title": product["title"],
            "why": product["why"],
            "url": affiliate.build_search_url(
                product["keywords"], product.get("department")),
            "search_terms": product["keywords"],
            "care_types": product.get("care_types") or [],
            "grounded_on": product.get("grounded_on") or [],
            "matched_on": explain(profile, matched_tags),
            "matched_tags": matched_tags,
            "is_due": bool(set(product.get("care_types") or []) & due),
            "_score": _score(product, matched_tags, profile, due),
        })

    meta = {c["id"]: c for c in catalog["categories"]}
    out = []
    for cat_id, items in by_category.items():
        items.sort(key=lambda i: (-i["_score"], i["title"]))
        trimmed = items[:per_category]
        for i in trimmed:
            i.pop("_score", None)
        info = meta.get(cat_id, {"id": cat_id, "label": cat_id, "sort": 999})
        out.append({
            "id": cat_id,
            "label": info.get("label", cat_id),
            "blurb": info.get("blurb", ""),
            "sort": info.get("sort", 999),
            "products": trimmed,
        })

    # Companions come from their own section of the catalog and are already
    # ordered by relevance within a group, so they skip scoring entirely.
    if not wanted or "companion" in wanted:
        companions = _companions_for(profile, profile.common_name)
        if companions:
            info = meta.get("companion", {})
            out.append({
                "id": "companion",
                "label": info.get("label", "Companion plants"),
                "blurb": info.get("blurb", ""),
                "sort": info.get("sort", 999),
                "products": companions[:per_category],
            })
    out.sort(key=lambda c: c["sort"])
    for c in out:
        c.pop("sort", None)
    return out


def _companions_for(profile: PlantProfile, own_name: str = "") -> list[dict]:
    """Companion-planting suggestions, as seed links.

    Only the first matching group is used. Companion planting is
    context-specific — stacking every group that technically matches would
    produce a list nobody could act on."""
    catalog = load_catalog()
    own = own_name.strip().lower()
    for group in catalog.get("companions", []):
        ok, matched_tags = _matches(group.get("match"), profile.tags)
        if not ok:
            continue
        # A plant is not its own companion. Zinnia is in the cut-flower
        # companion group and is itself a cut flower, so without this the
        # suggestion for Zinnia includes Zinnia.
        plants = [p for p in group.get("plants", [])
                  if p["name"].strip().lower() != own]
        return [{
            "id": f"{group['id']}-{p['name'].lower().replace(' ', '-')}",
            "title": p["name"],
            "why": p["why"],
            "url": affiliate.build_search_url(p["keywords"], "lawngarden"),
            "search_terms": p["keywords"],
            "care_types": [],
            "grounded_on": ["companion planting"],
            "matched_on": explain(profile, matched_tags),
            "matched_tags": matched_tags,
            "is_due": False,
        } for p in plants]
    return []


def recommend_for_species(
    species,
    schedules=None,
    traits=None,
    per_category: int = DEFAULT_PER_CATEGORY,
    categories: Optional[Iterable[str]] = None,
    due_care_types: Optional[Iterable[str]] = None,
) -> dict:
    """Full recommendation payload for one species."""
    profile = derive_profile(species, schedules, traits)
    cats = recommend_for_profile(
        profile, per_category=per_category, categories=categories,
        due_care_types=due_care_types)
    return {
        "species": {
            "id": getattr(species, "id", None),
            "common_name": getattr(species, "common_name", ""),
            "scientific_name": getattr(species, "scientific_name", ""),
        },
        "profile_tags": sorted(profile.tags),
        "categories": cats,
        "product_count": sum(len(c["products"]) for c in cats),
        **affiliate.link_meta(),
    }


def category_list() -> list[dict]:
    return [
        {k: v for k, v in c.items() if k != "sort"}
        for c in sorted(load_catalog()["categories"], key=lambda c: c["sort"])
    ]
