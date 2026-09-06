"""Bring the verified tranche into the catalog: evidence, rows, resolved values.

`ingest` stores what the citations said and `recompute` resolves it onto the
rows that exist. Neither creates a row, so a species the researchers covered
but the catalog never had was researched into a void -- 342 of the tranche's
469 species when this was written. This module closes that gap and is the
only thing allowed to (ADR 0005). It runs on every cold start, from seed.py,
so everything here is built to be re-run: one transaction, a skip gate so an
unchanged tranche over a catalog already in step costs two cheap reads, and a
report that says what moved.

The rows it mints follow three rules, all about not inventing:
  * every legacy care column is null -- no light label, humidity band or soil
    string was ever sourced for these species; the resolved columns carry
    what was;
  * `toxic_to_pets` is null unless a claim resolves it -- null reads as "no
    record", and a default of False would read as "safe" (ADR 0002);
  * a bare genus subject never becomes a row -- genus evidence feeds its
    congeners through the resolver and describes no plant on its own.

Linking, for species the catalog already holds under an older name, sets
`scientific_name_accepted` and nothing else. `scientific_name` is what users'
plants and toxicity.lookup key on and is never renamed here; common names and
legacy values are never overwritten.
"""
import hashlib
import re
import time
from dataclasses import dataclass, field as dc_field
from pathlib import Path

from sqlmodel import Session, col, or_, select

from app.models.models import ReviewStatus, Species, SpeciesSource, SyncState

from .ingest import VERIFIED_DIR, ingest_tranche, tranche_records
from .recompute import RESOLVER_VERSION, RecomputeReport, recompute_all

#: Bumped when the sync's own rules change -- what it mints, how it links --
#: so an unchanged tranche is re-synced once under the new rules.
SYNC_VERSION = "1"
FINGERPRINT_KEY = "tranche_fingerprint"


@dataclass
class SyncReport:
    skipped: bool = False
    dry_run: bool = False
    fingerprint: str = ""
    claims_written: int = 0
    claims_already_present: int = 0
    species_created: int = 0
    species_linked: int = 0
    #: subjects that matched more than one row; none of them was linked
    ambiguous: list[str] = dc_field(default_factory=list)
    #: single-word subjects -- genus-level evidence, never a row
    genus_subjects: list[str] = dc_field(default_factory=list)
    #: (common_name, subject) minted although the name was already in use
    common_name_collisions: list[tuple[str, str]] = dc_field(default_factory=list)
    recompute: RecomputeReport | None = None
    seconds: float = 0.0


def binomial_key(name: str | None) -> str:
    """One key for the spellings of one name.

    'Abelia × grandiflora' and 'Abelia x grandiflora', stray whitespace, case:
    the same normaliser test_tranche_invariants uses to catch a species
    researched twice, so the sync and the corpus check agree on identity.
    """
    return re.sub(r"\s+", " ", (name or "").replace("×", "x")).strip().casefold()


def tranche_fingerprint(directory: Path | None = None) -> str:
    """What the outcome of a sync depends on: the batch files' bytes and the
    rules that turn them into rows. A digest of the files alone would skip a
    re-sync after a resolver change -- the case a version bump exists to force."""
    directory = directory or VERIFIED_DIR
    digest = hashlib.sha256()
    for path in sorted(directory.glob("b*.json")):
        digest.update(path.read_bytes())
    return f"{digest.hexdigest()}:{RESOLVER_VERSION}:{SYNC_VERSION}"


def _rows_in_step(session: Session) -> bool:
    """Whether every species row was resolved under the current rules.

    The fingerprint sees the tranche and the rules, not the table: seed()
    runs before this on every boot and inserts any new catalog entry, and
    POST /species adds a row at any time. Such a row carries no resolver
    version until a recompute reaches it, and skipping on the fingerprint
    alone would leave it unlinked and unresolved until the tranche happened
    to move. So a skip also needs no row out of step."""
    stale = session.exec(select(Species.id).where(or_(
        col(Species.resolver_version).is_(None),
        col(Species.resolver_version) != RESOLVER_VERSION)).limit(1)).first()
    return stale is None


def _subject_of(record: dict) -> str:
    return (record.get("scientific_name_accepted")
            or record.get("scientific_name_given") or "").strip()


def _index(rows) -> dict[str, list[Species]]:
    """Every row under every spelling of every name it carries."""
    index: dict[str, list[Species]] = {}
    for row in rows:
        keys = {binomial_key(row.scientific_name),
                binomial_key(row.scientific_name_accepted)} - {""}
        for key in keys:
            index.setdefault(key, []).append(row)
    return index


def _matches(index: dict[str, list[Species]], record: dict) -> list[Species]:
    found: dict[int, Species] = {}
    for name in (record.get("scientific_name_accepted"),
                 record.get("scientific_name_given")):
        for row in index.get(binomial_key(name), []):
            found[id(row)] = row
    return list(found.values())


def _mint_and_link(session: Session, directory: Path, report: SyncReport) -> None:
    rows = session.exec(select(Species)).all()
    index = _index(rows)
    common_names = {row.common_name.casefold() for row in rows}

    for batch, record in tranche_records(directory):
        subject = _subject_of(record)
        if len(subject.split()) < 2:
            report.genus_subjects.append(subject)
            continue

        matches = _matches(index, record)
        if len(matches) > 1:
            # Two rows already answer to this name. Picking one would be a
            # guess about which plant the evidence describes; link neither.
            report.ambiguous.append(subject)
            continue
        if matches:
            row = matches[0]
            # `accepted or scientific_name` must be exactly the claim subject,
            # so the accepted name is stored only when it actually differs.
            wanted = subject if subject != row.scientific_name else None
            if row.scientific_name_accepted != wanted:
                row.scientific_name_accepted = wanted
                session.add(row)
                report.species_linked += 1
            continue

        common = (record.get("common_name") or "").strip()
        if common.casefold() in common_names:
            report.common_name_collisions.append((common, subject))
        row = Species(
            common_name=common, scientific_name=subject,
            source=SpeciesSource.claims, source_ref=batch,
            review_status=ReviewStatus.approved,
            toxic_to_pets=None, care_notes="")
        session.add(row)
        report.species_created += 1
        index.setdefault(binomial_key(subject), []).append(row)
        common_names.add(common.casefold())


def sync_catalog(session: Session, *, directory: Path | None = None,
                 dry_run: bool = False, force: bool = False) -> SyncReport:
    """Ingest, mint or link, recompute -- as one transaction, or not at all.

    An unchanged tranche under unchanged rules, over a table every row of
    which the last run reached, returns `skipped=True` without touching
    anything; `force` runs it anyway and, on a catalog already in step,
    reports nothing created, linked or updated. `dry_run` does the whole
    walk and rolls it back, fingerprint included, so the next real run is not
    fooled into skipping.
    """
    started = time.monotonic()
    directory = directory or VERIFIED_DIR
    report = SyncReport(dry_run=dry_run, fingerprint=tranche_fingerprint(directory))

    state = session.get(SyncState, FINGERPRINT_KEY)
    if (state is not None and state.value == report.fingerprint and not force
            and _rows_in_step(session)):
        report.skipped = True
        report.seconds = time.monotonic() - started
        return report

    ingested = ingest_tranche(session, directory, commit=False)
    report.claims_written = ingested.claims_written
    report.claims_already_present = ingested.claims_already_present

    _mint_and_link(session, directory, report)

    report.recompute = recompute_all(session, commit=False)

    if dry_run:
        session.rollback()
    else:
        if state is None:
            session.add(SyncState(key=FINGERPRINT_KEY, value=report.fingerprint))
        elif state.value != report.fingerprint:
            state.value = report.fingerprint
            session.add(state)
        session.commit()
    report.seconds = time.monotonic() - started
    return report


def describe(report: SyncReport) -> str:
    """The report as the lines a cold-start log or the CLI prints."""
    if report.skipped:
        return "claim sync: tranche unchanged, nothing to do"
    lines = ["claim sync: DRY RUN — nothing written" if report.dry_run
             else "claim sync: written"]
    lines += [
        f"  claims stored           {report.claims_written}",
        f"  claims already present  {report.claims_already_present}",
        f"  species created         {report.species_created}",
        f"  species linked          {report.species_linked}",
        f"  ambiguous, not linked   {len(report.ambiguous)}",
        f"  genus subjects skipped  {len(report.genus_subjects)}",
        f"  common-name collisions  {len(report.common_name_collisions)}",
    ]
    if report.recompute is not None:
        lines += [
            f"  species updated         {report.recompute.species_updated}",
            f"  fields refused          {report.recompute.fields_refused}",
        ]
    for subject in report.ambiguous:
        lines.append(f"    ambiguous: {subject}")
    for subject in report.genus_subjects:
        lines.append(f"    genus subject: {subject}")
    for common, subject in report.common_name_collisions:
        lines.append(f"    collision: {common!r} already in use ({subject} minted)")
    lines.append(f"  took {report.seconds:.1f}s")
    return "\n".join(lines)


def main() -> None:
    """Sync the verified tranche into the catalog.

    Usage (from garden-gnome/):
      python -m app.data.claims.sync --dry-run
      python -m app.data.claims.sync
      python -m app.data.claims.sync --force     # ignore the fingerprint gate
    """
    import argparse

    from app.db.database import engine

    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="walk the whole sync, write nothing")
    parser.add_argument("--force", action="store_true",
                        help="run even when the tranche fingerprint is unchanged")
    args = parser.parse_args()

    with Session(engine) as session:
        report = sync_catalog(session, dry_run=args.dry_run, force=args.force)
    print(describe(report))


if __name__ == "__main__":
    main()
