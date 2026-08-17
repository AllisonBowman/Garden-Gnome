"""Write the verified tranche into the catalog as evidence.

The only module that creates Claims, so it carries the same obligations plan
3.1 put on `apply_review`, the only module that writes resolved values: it
refuses what it cannot account for, re-running it changes nothing, and
`dry_run` leaves the database byte-identical.

Nothing here decides what a value should be. It stores what a citation said,
and resolution happens later and separately.
"""
import json
from dataclasses import dataclass, field as dc_field
from pathlib import Path

from sqlmodel import Session, select

from app.models.models import Authority as AuthorityRow
from app.models.models import Claim as ClaimRow

from .authorities import licence_of
from .tranche import claims_from_record


@dataclass
class IngestReport:
    claims_written: int = 0
    claims_already_present: int = 0
    authorities_created: int = 0
    #: subject -> the fields whose values no vetted citation supports
    unsupported: dict[str, list[str]] = dc_field(default_factory=dict)

    @property
    def unsupported_count(self) -> int:
        return sum(len(v) for v in self.unsupported.values())


def _authority_row(session: Session, name: str, tier: int,
                   report: IngestReport) -> AuthorityRow:
    row = session.exec(
        select(AuthorityRow).where(AuthorityRow.name == name)).first()
    if row is None:
        row = AuthorityRow(name=name, tier=tier, licence=licence_of(name))
        session.add(row)
        session.flush()
        report.authorities_created += 1
    return row


def ingest_records(session: Session, records, *,
                   dry_run: bool = False) -> IngestReport:
    """Store every supported value in `records` as a Claim.

    Values no vetted citation supports are collected in the report rather than
    written -- an unsupported value is exactly what this pipeline exists to
    stop the catalog asserting.
    """
    report = IngestReport()

    for record in records:
        extracted, unsupported = claims_from_record(record)
        if unsupported:
            subject = (record.get("scientific_name_accepted")
                       or record.get("scientific_name_given") or "?")
            report.unsupported[subject] = unsupported

        for claim in extracted:
            authority = _authority_row(
                session, claim.authority.name, claim.authority.tier, report)
            # The table's uniqueness is (subject, field, citation_url), so a
            # re-run recognises its own previous work instead of doubling it.
            existing = session.exec(
                select(ClaimRow).where(
                    ClaimRow.subject == claim.subject,
                    ClaimRow.field == claim.field,
                    ClaimRow.citation_url == claim.citation_url)).first()
            if existing is not None:
                report.claims_already_present += 1
                continue
            session.add(ClaimRow(
                subject=claim.subject,
                field=claim.field,
                value_json=json.dumps(claim.value),
                authority_id=authority.id,
                citation_title=claim.citation_title,
                citation_url=claim.citation_url,
                quote=claim.quote,
            ))
            report.claims_written += 1

    if dry_run:
        session.rollback()
    else:
        session.commit()
    return report


VERIFIED_DIR = Path(__file__).resolve().parents[1] / "verified"


def ingest_tranche(session: Session, directory: Path | None = None, *,
                   dry_run: bool = False) -> IngestReport:
    """Ingest every verified batch file, in a stable order."""
    directory = directory or VERIFIED_DIR
    records = []
    for path in sorted(directory.glob("b*.json")):
        records.extend(json.loads(path.read_text())["records"])
    return ingest_records(session, records, dry_run=dry_run)


def main() -> None:
    """Load the verified tranche into the catalog.

    Usage (from garden-gnome/):
      python -m app.data.claims.ingest --dry-run
      python -m app.data.claims.ingest
    On the deployed backend:
      flyctl ssh console -a garden-gnome-api \
        -C "python -m app.data.claims.ingest --dry-run"
    """
    import argparse

    from app.db.database import engine

    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="report what would be written, change nothing")
    args = parser.parse_args()

    with Session(engine) as session:
        report = ingest_tranche(session, dry_run=args.dry_run)

    print(f"{'DRY RUN — nothing written' if args.dry_run else 'written'}")
    print(f"  claims stored          {report.claims_written}")
    print(f"  already present        {report.claims_already_present}")
    print(f"  authorities created    {report.authorities_created}")
    print(f"  values left unsupported {report.unsupported_count} "
          f"across {len(report.unsupported)} species")
    for subject, fields in sorted(report.unsupported.items()):
        print(f"    {subject}: {', '.join(fields)}")


if __name__ == "__main__":
    main()
