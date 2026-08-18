"""Materialise resolved values onto the catalog.

`claim` holds the evidence, `species` holds the columns, and this is the only
thing that connects them. Values are derived from whatever claims exist right
now (ADR 0001), so this is safe to re-run at any time and re-running is how a
rule change reaches the catalog -- not a migration.

Idempotent by construction: it computes the whole row from the claims and
writes only where the answer differs, so a second pass over unchanged evidence
touches nothing at all.
"""
from dataclasses import dataclass, field as dc_field

from sqlmodel import Session, select

from app.models.models import CareDataStatus
from app.models.models import Claim as ClaimRow
from app.models.models import Species

from .resolve import genus_of
from .store import resolve_from_db

#: Bumped when the resolution rules change. Rows carrying an older version are
#: stale, which makes finding them a query instead of a guess.
RESOLVER_VERSION = "1"

#: The only columns a Claim is allowed to set. An allowlist rather than a
#: denylist: a claim naming `scientific_name` or `review_status` must not be
#: able to reach them, and a field added to the table later should stay
#: unwritable until someone decides otherwise.
RESOLVED_FIELDS = frozenset({
    "light_fc_min", "light_fc_good", "direct_sun_hours_max",
    "outdoor_sun_exposure",
    "water_regime", "water_dry_down_target", "water_check_depth_cm",
    "water_growing_days_est", "water_dormant_days_est",
    "humidity_need",
    "day_f_min", "day_f_max", "night_f_min", "night_f_max", "chill_damage_f",
    "soil_base", "soil_drainage", "soil_ph_min", "soil_ph_max",
    "fertilize_active_months", "fertilize_interval_days", "fertilize_strength",
    "toxic_to_pets", "toxicity_detail",
})

#: Fields this recompute may set from a claim but must never clear.
#:
#: `toxic_to_pets` is NOT NULL on the legacy schema and defaults to False --
#: which is exactly the "absence read as safety" defect plan 3.2 exists to fix
#: by making the column nullable. Until it is, clearing a withdrawn toxicity
#: claim would write False, and False here reads as "this plant is safe for
#: your cat". Leaving the old value is wrong too, but it is wrong in the
#: direction that does not tell someone a toxic plant is harmless.
CANNOT_CLEAR = frozenset({"toxic_to_pets"})


@dataclass
class RecomputeReport:
    species_seen: int = 0
    species_updated: int = 0
    values_written: int = 0
    fields_refused: int = 0
    by_status: dict[str, int] = dc_field(default_factory=dict)


def _status(provenance: dict[str, str]) -> CareDataStatus:
    if not provenance:
        return CareDataStatus.none
    if any(p == "sourced" for p in provenance.values()):
        return CareDataStatus.sourced
    return CareDataStatus.inferred


def recompute_species(session: Session, species: Species,
                      report: RecomputeReport) -> bool:
    """Rewrite one species' resolved values. True if anything changed."""
    resolution = resolve_from_db(session, species.scientific_name)

    values = {f: v for f, v in resolution.values.items() if f in RESOLVED_FIELDS}
    provenance = {f: p for f, p in resolution.provenance.items()
                  if f in RESOLVED_FIELDS}
    report.fields_refused += len(resolution.refusals)

    changed = False
    for name in RESOLVED_FIELDS:
        new = values.get(name)
        # A field with no surviving claim goes back to null rather than
        # keeping what an earlier run put there -- that is what makes
        # withdrawing an authority actually remove its influence. The
        # exception is a column that cannot hold null yet; see CANNOT_CLEAR.
        if new is None and name in CANNOT_CLEAR:
            continue
        if getattr(species, name) != new:
            setattr(species, name, new)
            changed = True
        if new is not None:
            report.values_written += 1

    status = _status(provenance)
    for name, new in (("care_data_status", status),
                      ("care_provenance", provenance or None),
                      ("resolver_version", RESOLVER_VERSION)):
        if getattr(species, name) != new:
            setattr(species, name, new)
            changed = True

    report.by_status[status.value] = report.by_status.get(status.value, 0) + 1
    return changed


def recompute_all(session: Session, *, dry_run: bool = False) -> RecomputeReport:
    """Recompute every species that has claims, or has had them before."""
    report = RecomputeReport()

    for species in session.exec(select(Species)).all():
        report.species_seen += 1
        if recompute_species(session, species, report):
            session.add(species)
            report.species_updated += 1

    if dry_run:
        session.rollback()
    else:
        session.commit()
    return report


def subjects_with_claims(session: Session) -> set[str]:
    """Every name any stored claim speaks about, species and genus alike."""
    return {row for (row,) in session.exec(select(ClaimRow.subject).distinct())}


def main() -> None:
    """Resolve stored claims onto the catalog.

    Usage (from garden-gnome/):
      python -m app.data.claims.recompute --dry-run
      python -m app.data.claims.recompute
    """
    import argparse

    from app.db.database import engine

    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="report what would change, write nothing")
    args = parser.parse_args()

    with Session(engine) as session:
        report = recompute_all(session, dry_run=args.dry_run)

    print("DRY RUN — nothing written" if args.dry_run else "written")
    print(f"  species seen       {report.species_seen}")
    print(f"  species updated    {report.species_updated}")
    print(f"  values written     {report.values_written}")
    print(f"  fields refused     {report.fields_refused}")
    for status, n in sorted(report.by_status.items()):
        print(f"  care_data_status {status:9} {n}")


if __name__ == "__main__":
    main()
