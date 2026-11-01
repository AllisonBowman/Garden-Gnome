"""Feed the resolver from the catalog.

The adapter between stored evidence and the rules that judge it. It carries
claims across and nothing else — every decision about what may be asserted
lives in resolve.py, so this module has no opinions to drift out of step.
"""
import json
import threading
from dataclasses import dataclass
from typing import Any

from sqlalchemy import func
from sqlmodel import Session, select

from app.models.models import Authority as AuthorityRow
from app.models.models import Claim as ClaimRow

from .resolve import Authority, Claim, Resolution, genus_of, resolve
from .tranche import WEED_FIELD

#: The fields whose cited passages say what a plant does to whoever eats or
#: handles it. NC State files its poison block -- severity, symptoms, the
#: "Poisonous to Humans" heading -- under the pet flag's citation, and RHS
#: puts "TOXIC if eaten" beside the edibility it denies, so the facts a
#: caretaker most needs about people sit in these quotes and nowhere else.
SAFETY_FIELDS = ("toxic_to_pets", "toxicity_detail", "is_edible")
_SAFETY_CACHE_KEY = "claims.safety_passages"

#: The two listings that keep a species off every candidate list
#: (toxicity.never_put_forward) are stored as claims of their own at ingest,
#: from every vetted citation that holds the phrase (tranche.WEED_FIELD, ADR
#: 0011), so the safety code reads them here without opening the tranche
#: files. Species scope only, as with the safety passages: a genus page does
#: not list this plant. Only those quotes are cached, so the cache is small.
_WEED_CACHE_KEY = "claims.weed_quotes"


@dataclass(frozen=True)
class Passage:
    """One cited passage on a safety field, as the server reads it.

    The quote never leaves the server (ADR 0003): the toxicity code reads
    facts out of it -- a severity rating, who is at risk, a preparation
    condition -- and states those, with the authority's name."""
    field: str
    value: Any
    quote: str
    authority: str


def _load_safety_passages(session: Session) -> dict[str, list[Passage]]:
    cache: dict[str, list[Passage]] = {}
    rows = session.exec(
        select(ClaimRow, AuthorityRow)
        .join(AuthorityRow, ClaimRow.authority_id == AuthorityRow.id)  # type: ignore[arg-type]
        .where(ClaimRow.field.in_(SAFETY_FIELDS))  # type: ignore[attr-defined]
    ).all()
    for claim_row, authority in rows:
        if (authority.allowed_fields is not None
                and claim_row.field not in authority.allowed_fields):
            continue
        cache.setdefault(claim_row.subject, []).append(Passage(
            field=claim_row.field,
            value=json.loads(claim_row.value_json),
            quote=claim_row.quote or "",
            authority=authority.name,
        ))
    return cache


def _load_weed_quotes(session: Session) -> dict[str, list[str]]:
    cache: dict[str, list[str]] = {}
    rows = session.exec(
        select(ClaimRow, AuthorityRow)
        .join(AuthorityRow, ClaimRow.authority_id == AuthorityRow.id)  # type: ignore[arg-type]
        .where(ClaimRow.field == WEED_FIELD)  # type: ignore[attr-defined]
    ).all()
    for claim_row, authority in rows:
        if (authority.allowed_fields is not None
                and claim_row.field not in authority.allowed_fields):
            continue
        if claim_row.quote:
            cache.setdefault(claim_row.subject, []).append(claim_row.quote)
    return cache


def _claims_key(session: Session) -> tuple:
    """Changes whenever the safety passages can have: the catalog generation
    (a fresh token on every ORM write to a claim or an authority, in any
    process), and the claim and authority counts and highest ids for a write
    that bypassed it. Four cheap reads."""
    from app.db.catalog_state import generation

    claims = session.exec(select(func.count(ClaimRow.id), func.max(ClaimRow.id))).one()
    authorities = session.exec(
        select(func.count(AuthorityRow.id), func.max(AuthorityRow.id))).one()
    return (str(session.get_bind().url), generation(session), *claims, *authorities)


#: The parsed passages for one catalog version, shared by every request in
#: this process. A request used to parse the whole table for itself -- 1,453
#: claims, 4 MB of Passage objects -- for a single species.
_shared: tuple[tuple, dict[str, list[Passage]]] | None = None
_shared_lock = threading.Lock()
#: The weed quotes, the same way: one scan of every quote per catalog version.
_shared_weeds: tuple[tuple, dict[str, list[str]]] | None = None


def _shared_passages(session: Session) -> dict[str, list[Passage]]:
    global _shared
    key = _claims_key(session)
    held = _shared
    if held is not None and held[0] == key:
        return held[1]
    with _shared_lock:
        held = _shared
        if held is not None and held[0] == key:
            return held[1]
        passages = _load_safety_passages(session)
        _shared = (key, passages)
        return passages


def _shared_weed_quotes(session: Session) -> dict[str, list[str]]:
    global _shared_weeds
    key = _claims_key(session)
    held = _shared_weeds
    if held is not None and held[0] == key:
        return held[1]
    with _shared_lock:
        held = _shared_weeds
        if held is not None and held[0] == key:
            return held[1]
        quotes = _load_weed_quotes(session)
        _shared_weeds = (key, quotes)
        return quotes


def weed_quotes(session: Session, subject: str) -> list[str]:
    """Every cited quote about `subject` itself that names it a noxious weed
    or an invasive species, whatever field it was filed under. Cached like
    `safety_passages`, and forgotten with them."""
    cache = session.info.get(_WEED_CACHE_KEY)
    if cache is None:
        cache = _shared_weed_quotes(session)
        session.info[_WEED_CACHE_KEY] = cache
    return cache.get(subject, [])


def safety_passages(session: Session, subject: str) -> list[Passage]:
    """Every cited passage on a safety field about `subject` itself.

    Species scope only: a genus page never speaks for a species on toxicity
    (ADR 0002), so a congener's warning is not this plant's either way. The
    scope rule `load_claims` applies holds here too.

    Parsed once per catalog version for the whole process (`_claims_key`),
    because every species a response carries asks for its toxicity sentence
    and every request used to pay for the whole table. Each session then
    holds its copy in `session.info`, so a request reads one consistent
    version; `forget_safety_passages` drops that copy whenever claims are
    written or withdrawn, and the next read keys on the new generation. The
    dict is shared: callers must not change it."""
    cache = session.info.get(_SAFETY_CACHE_KEY)
    if cache is None:
        cache = _shared_passages(session)
        session.info[_SAFETY_CACHE_KEY] = cache
    return cache.get(subject, [])


def forget_safety_passages(session: Session) -> None:
    """Drop the cached passages, and the weed quotes with them, so the next
    read sees the claims as stored."""
    session.info.pop(_SAFETY_CACHE_KEY, None)
    session.info.pop(_WEED_CACHE_KEY, None)


def _to_claim(row: ClaimRow, authority: AuthorityRow) -> Claim:
    return Claim(
        subject=row.subject,
        field=row.field,
        value=json.loads(row.value_json),
        authority=Authority(name=authority.name, tier=authority.tier),
        citation_url=row.citation_url,
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
    forget_safety_passages(session)
    return len(rows)
