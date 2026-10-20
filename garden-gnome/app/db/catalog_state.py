"""What state the species catalog in this database is in, cheaply.

Two readers. GET /species/ keys its cached body on `catalog_key`, so the
catalog is built once per version instead of once per request. GET / reports
`catalog_status`, so a deploy's smoke check can tell a boot whose claim sync
ran from one whose sync was skipped -- seed.py swallows a sync failure on
purpose, so the API still answering 200 says nothing about the catalog.

Both read only counts, maxima, one indexed probe and a few sync_state rows.
Nothing here walks the catalog or exposes anything a client could not
already infer: how many species and claims there are, and a digest of
catalog files that ship in every build.
"""
from functools import lru_cache

from sqlalchemy import func
from sqlmodel import Session, col, or_, select

from app.models.models import (
    CATALOG_GENERATION_KEY, Claim, Species, SpeciesTrait, SyncState,
)

#: The highest species id the last claim sync reached (sync.py writes it).
SYNCED_THROUGH_KEY = "synced_through_species_id"


@lru_cache(maxsize=1)
def shipped_fingerprint() -> str:
    """The tranche fingerprint of the catalog files this process ships with.

    Hashing them reads every batch file (about 16 MB), so it is done once per
    process; the files in an image do not change while it runs."""
    from app.data.claims.sync import tranche_fingerprint
    return tranche_fingerprint()


def stored_fingerprint(session: Session) -> str | None:
    """The fingerprint the last successful claim sync recorded, if any."""
    from app.data.claims.sync import FINGERPRINT_KEY
    state = session.get(SyncState, FINGERPRINT_KEY)
    return state.value if state is not None else None


def generation(session: Session) -> str | None:
    """The catalog's generation: a fresh token on every flush that writes a
    catalog row, in any process (models.stamp_catalog_generation)."""
    state = session.get(SyncState, CATALOG_GENERATION_KEY)
    return state.value if state is not None else None


def _synced_through(session: Session) -> int | None:
    state = session.get(SyncState, SYNCED_THROUGH_KEY)
    try:
        return int(state.value) if state is not None else None
    except ValueError:
        return None


def _rows_out_of_step(session: Session, through: int | None = None) -> bool:
    """Whether any species row was not resolved under the current rules (the
    same test the claim sync uses to decide it cannot skip) -- among rows up
    to `through`, when given."""
    from app.data.claims.recompute import RESOLVER_VERSION
    query = select(Species.id).where(or_(
        col(Species.resolver_version).is_(None),
        col(Species.resolver_version) != RESOLVER_VERSION))
    if through is not None:
        query = query.where(col(Species.id) <= through)
    return session.exec(query.limit(1)).first() is not None


def catalog_key(session: Session) -> tuple:
    """Changes whenever what GET /species/ would return can have changed.

    The generation moves with every write to a catalog row through the ORM,
    in this process or another: a sync's in-place rewrite, an operator's
    POST /species/, an authority's claims withdrawn. The fingerprint, the
    row count and the highest row and trait ids stay in the key for writes
    that bypass it; an edit made with raw SQL that moves none of these still
    needs a restart to show."""
    species_count, species_max = session.exec(
        select(func.count(Species.id), func.max(Species.id))).one()
    trait_max = session.exec(select(func.max(SpeciesTrait.id))).one()
    return (stored_fingerprint(session), generation(session),
            species_count, species_max, trait_max)


def catalog_status(session: Session) -> dict:
    """The catalog as the public root reports it.

    `synced` is true when the last claim sync recorded the fingerprint of the
    files this build ships and reached every row it found: the catalog
    serving is the catalog this build carries. False means the boot's sync
    was skipped or failed, or has not run, and production is serving older
    care data. A row added after that sync -- an operator's POST /species/ --
    is not counted against it: nothing older is being served, and the next
    boot's sync resolves it. (Before any sync has recorded how far it
    reached, every row counts, as it always did.)"""
    stored = stored_fingerprint(session)
    shipped = shipped_fingerprint()
    species = session.exec(select(func.count(Species.id))).one()
    claims = session.exec(select(func.count(Claim.id))).one()
    return {
        # The digest's first 12 hex characters and the rule versions: enough
        # to tell two builds' catalogs apart, short enough to read in a log.
        "version": _short(shipped),
        "synced": stored == shipped and not _rows_out_of_step(
            session, _synced_through(session)),
        "species": species,
        "claims": claims,
    }


def _short(fingerprint: str) -> str:
    digest, _, versions = fingerprint.partition(":")
    return f"{digest[:12]}:{versions}" if versions else digest[:12]
