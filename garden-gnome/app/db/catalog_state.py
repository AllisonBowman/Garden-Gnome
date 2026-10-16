"""What state the species catalog in this database is in, cheaply.

GET /species/ keys its cached body on `catalog_key`, so the catalog is built
once per version instead of once per request. It reads only counts, maxima
and one sync_state row; nothing here walks the catalog.
"""
from sqlalchemy import func
from sqlmodel import Session, select

from app.models.models import Species, SpeciesTrait, SyncState


def stored_fingerprint(session: Session) -> str | None:
    """The fingerprint the last successful claim sync recorded, if any."""
    from app.data.claims.sync import FINGERPRINT_KEY
    state = session.get(SyncState, FINGERPRINT_KEY)
    return state.value if state is not None else None


def catalog_key(session: Session) -> tuple:
    """Changes whenever what GET /species/ would return can have changed.

    The claim sync rewrites rows only at boot, and records its fingerprint
    when it does. The seed and the species write routes add rows, and every
    row arrives with its traits, so the row count and the highest row and
    trait ids move with them. An in-place edit that does none of these (a
    hand-run script against a live database) needs a restart to show."""
    species_count, species_max = session.exec(
        select(func.count(Species.id), func.max(Species.id))).one()
    trait_max = session.exec(select(func.max(SpeciesTrait.id))).one()
    return (stored_fingerprint(session), species_count, species_max, trait_max)
