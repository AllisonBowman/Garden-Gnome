"""Recompute bidirectional cross-reference traits over the whole catalog.

Two derived traits, keyed on the catalog's current contents:
  shares_common_name_with : other species with the same common name
  related_variant_of      : the base species a cultivar/variant relates to

Idempotent (upserts), so it's safe to re-run any time the catalog changes —
e.g. after a bulk import that skipped existing species and therefore left
their back-references stale.

Usage (from garden-gnome/):
  python -m app.data.expansion.recompute_xrefs
On the deployed backend:
  flyctl ssh console -a garden-gnome-api -C "python -m app.data.expansion.recompute_xrefs"
"""
from sqlmodel import Session, select

from app.db.database import engine
from app.models.models import Species, SpeciesTrait
from app.data.expansion.validate import _name_key

SHARES = "shares_common_name_with"
VARIANT = "related_variant_of"


def _upsert_trait(session: Session, species_id: int, trait: str, value: str) -> None:
    row = session.exec(select(SpeciesTrait).where(
        SpeciesTrait.species_id == species_id,
        SpeciesTrait.trait == trait)).first()
    if row:
        row.value = value
        session.add(row)
    else:
        session.add(SpeciesTrait(species_id=species_id, trait=trait, value=value))


def recompute_cross_references(session: Session) -> tuple[int, int]:
    """Add/update shares_common_name_with and related_variant_of traits over
    every species. Returns (shared_common_name_groups, variant_links)."""
    all_species = session.exec(select(Species)).all()

    # Shared common names
    by_common: dict[str, list[Species]] = {}
    for s in all_species:
        by_common.setdefault(_name_key(s.common_name), []).append(s)
    groups = 0
    for key, members in by_common.items():
        if not key or len(members) < 2:
            continue
        groups += 1
        for s in members:
            others = "; ".join(sorted(
                m.scientific_name for m in members if m.id != s.id))[:800]
            _upsert_trait(session, s.id, SHARES, others)

    # Cultivar/variant adjacency by normalized-name containment
    keyed = sorted(((_name_key(s.scientific_name), s) for s in all_species),
                   key=lambda ks: len(ks[0]))
    links = 0
    for i, (k_short, s_short) in enumerate(keyed):
        if not k_short:
            continue
        for k_long, s_long in keyed[i + 1:]:
            if k_long.startswith(k_short + " "):
                links += 1
                _upsert_trait(session, s_long.id, VARIANT, s_short.scientific_name)

    return groups, links


def main() -> int:
    with Session(engine) as session:
        groups, links = recompute_cross_references(session)
        session.commit()
    print(f"recomputed cross-references: {groups} shared-common-name groups, "
          f"{links} variant links")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
