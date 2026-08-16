"""Claims persisted in the catalog resolve by exactly the rules in resolve.py.

The pure layer decides what may be asserted; this is the adapter that feeds it
from the database and must not develop opinions of its own. Everything here is
about faithful carriage — types survive the round trip, genus-level claims are
found, and a withdrawn Authority takes its values with it.
"""
import json

import pytest
from sqlmodel import Session, select

from app.data.claims.store import resolve_from_db, withdraw_authority
from app.models.models import Authority, Claim


@pytest.fixture(autouse=True)
def empty_evidence(session):
    """Start each test with no claims at all.

    `migrated_db_url` is session-scoped and these helpers commit, so without
    this a test inherits whatever its predecessors asserted — and a stray
    species-level claim would quietly mask the genus-inheritance it is
    supposed to be proving.
    """
    for model in (Claim, Authority):
        for row in session.exec(select(model)).all():
            session.delete(row)
    session.commit()
    yield


def add_authority(session: Session, name: str, tier: int, licence: str = "") -> Authority:
    row = Authority(name=name, tier=tier, licence=licence)
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def add_claim(session: Session, authority, subject, field, value, url="https://example.test/a"):
    session.add(Claim(
        subject=subject, field=field, value_json=json.dumps(value),
        authority_id=authority.id, citation_title="A factsheet",
        citation_url=url, quote="the passage that supports it",
    ))
    session.commit()


def test_a_stored_claim_resolves_with_its_type_intact(session):
    nc_state = add_authority(session, "NC State Extension", tier=2)
    add_claim(session, nc_state, "Dracaena trifasciata", "humidity_need", "low")
    add_claim(session, nc_state, "Dracaena trifasciata", "light_fc_min", 100)
    add_claim(session, nc_state, "Dracaena trifasciata", "toxic_to_pets", True)

    result = resolve_from_db(session, "Dracaena trifasciata")

    # JSON round trip, not str() — a stored True must not come back as "True",
    # and 100 must not come back as "100".
    assert result.values["humidity_need"] == "low"
    assert result.values["light_fc_min"] == 100
    assert result.values["toxic_to_pets"] is True
    assert result.provenance["light_fc_min"] == "sourced"


def test_a_genus_claim_is_found_but_a_family_claim_is_never_loaded(session):
    clemson = add_authority(session, "Clemson HGIC", tier=2)
    add_claim(session, clemson, "Dracaena", "light_fc_min", 100,
              url="https://example.test/genus")
    add_claim(session, clemson, "Asparagaceae", "soil_ph_min", 6.0,
              url="https://example.test/family")

    result = resolve_from_db(session, "Dracaena trifasciata")

    assert result.values["light_fc_min"] == 100
    assert result.provenance["light_fc_min"] == "genus_inferred"
    assert "soil_ph_min" not in result.values


def test_withdrawing_an_authority_moves_the_value_to_whoever_is_left(session):
    # The licence-problem drill. Values must fall back to surviving evidence,
    # not sit there sourced to an authority we can no longer use.
    wfo = add_authority(session, "World Flora Online", tier=1, licence="CC0")
    nc_state = add_authority(session, "NC State Extension", tier=2)
    add_claim(session, wfo, "Dracaena trifasciata", "soil_ph_min", 5.5,
              url="https://example.test/wfo")
    add_claim(session, nc_state, "Dracaena trifasciata", "soil_ph_min", 6.5,
              url="https://example.test/ncstate")

    assert resolve_from_db(
        session, "Dracaena trifasciata").values["soil_ph_min"] == 5.5

    removed = withdraw_authority(session, "World Flora Online")

    assert removed == 1
    assert resolve_from_db(
        session, "Dracaena trifasciata").values["soil_ph_min"] == 6.5


def test_withdrawing_the_only_authority_leaves_no_value_at_all(session):
    wfo = add_authority(session, "World Flora Online", tier=1, licence="CC0")
    add_claim(session, wfo, "Dracaena trifasciata", "soil_ph_min", 5.5)

    withdraw_authority(session, "World Flora Online")

    assert "soil_ph_min" not in resolve_from_db(
        session, "Dracaena trifasciata").values
