"""Feed the resolver from the catalog.

The adapter between stored evidence and the rules that judge it. It carries
claims across and nothing else — every decision about what may be asserted
lives in resolve.py, so this module has no opinions to drift out of step.
"""
import json

from sqlmodel import Session, select

from app.models.models import Authority as AuthorityRow
from app.models.models import Claim as ClaimRow

from .resolve import Authority, Claim, Resolution, genus_of, resolve


def _to_claim(row: ClaimRow, authority: AuthorityRow) -> Claim:
    return Claim(
        subject=row.subject,
        field=row.field,
        value=json.loads(row.value_json),
        authority=Authority(name=authority.name, tier=authority.tier),
    )


def load_claims(session: Session, subject: str) -> list[Claim]:
    """Every stored Claim that could bear on `subject` — its own and its genus'.

    Two admissions are decided here, not downstream. A family-level claim is
    never loaded, which is how ADR 0002's limit on inference survives someone
    editing the resolver. And a claim naming a field outside its authority's
    scope is excluded the same way — read off `Authority.allowed_fields`,
    which was set once when the row was created (ingest.py) rather than
    re-derived from the live registry here. That keeps this in step with how
    tier and licence already work: a fact stored on the row, not recalled
    (ADR 0001). `claims_from_record` already refuses to write an out-of-scope
    claim, but a row that reaches `claim` by any other path -- a future
    ingestion source, a manual repair -- must not silently resolve just
    because it is sitting in the table.
    """
    subjects = {subject, genus_of(subject)}
    rows = session.exec(
        select(ClaimRow, AuthorityRow)
        .join(AuthorityRow, ClaimRow.authority_id == AuthorityRow.id)  # type: ignore[arg-type]
        .where(ClaimRow.subject.in_(subjects))  # type: ignore[attr-defined]
    ).all()
    return [_to_claim(claim_row, authority) for claim_row, authority in rows
            if authority.allowed_fields is None
            or claim_row.field in authority.allowed_fields]


def resolve_from_db(session: Session, subject: str) -> Resolution:
    """Resolved values for one species, derived from the claims stored today."""
    return resolve(subject, load_claims(session, subject))


def withdraw_authority(session: Session, name: str) -> int:
    """Drop every Claim from one Authority. Returns how many were removed.

    The remedy when a source turns out to be unusable — a licence we misread,
    terms that changed. Because values are derived rather than stored (ADR
    0001), removing the evidence is enough: whatever it was supporting falls
    back to surviving claims, or stops being asserted at all. The Authority
    row itself stays, so the withdrawal is on the record.
    """
    authority = session.exec(
        select(AuthorityRow).where(AuthorityRow.name == name)).first()
    if authority is None:
        return 0
    rows = session.exec(
        select(ClaimRow).where(ClaimRow.authority_id == authority.id)).all()
    for row in rows:
        session.delete(row)
    session.commit()
    return len(rows)
