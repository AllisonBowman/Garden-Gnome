"""Writing the verified tranche into the catalog as evidence.

This is a writer, so it follows the same rules plan 3.1 imposed on
`apply_review`: it refuses what it cannot account for, it can be re-run without
doubling anything, and `--dry-run` leaves the database exactly as it found it.
"""
import json

import pytest
from sqlmodel import select

from app.data.claims.ingest import ingest_records
from app.models.models import Authority, Claim

NCSU_URL = "https://plants.ces.ncsu.edu/plants/dracaena-trifasciata/"

RECORD = {
    "common_name": "Snake Plant",
    "scientific_name_accepted": "Dracaena trifasciata",
    "humidity_need": "low",
    "light_fc_min": 100,
    "toxic_to_pets": True,
    "citations": [
        {"claim": "humidity_need low; light_fc_min 100; toxic_to_pets true",
         "source": "NC State Extension Gardener Plant Toolbox",
         "url": NCSU_URL, "quote": "Tolerates low humidity"},
    ],
}


@pytest.fixture(autouse=True)
def empty_evidence(session):
    for model in (Claim, Authority):
        for row in session.exec(select(model)).all():
            session.delete(row)
    session.commit()
    yield


def stored_claims(session):
    return session.exec(select(Claim)).all()


def test_ingesting_a_record_stores_its_claims_and_their_publisher(session):
    report = ingest_records(session, [RECORD])

    claims = stored_claims(session)
    assert {c.field for c in claims} == {
        "humidity_need", "light_fc_min", "toxic_to_pets"}
    assert report.claims_written == 3

    # Types survive: the value is JSON, not str().
    by_field = {c.field: json.loads(c.value_json) for c in claims}
    assert by_field["light_fc_min"] == 100
    assert by_field["toxic_to_pets"] is True

    authority = session.exec(select(Authority)).one()
    assert authority.name == "NC State Extension"
    assert authority.tier == 2
    # ADR 0001 -- the terms we accepted a source under are stored, not recalled.
    assert authority.licence


def test_the_quote_is_stored_even_though_it_is_never_shipped(session):
    ingest_records(session, [RECORD])

    assert all(c.quote for c in stored_claims(session))


def test_running_it_twice_does_not_double_the_evidence(session):
    first = ingest_records(session, [RECORD])
    second = ingest_records(session, [RECORD])

    assert first.claims_written == 3
    assert second.claims_written == 0
    assert second.claims_already_present == 3
    assert len(stored_claims(session)) == 3
    # And the publisher is not re-created either.
    assert len(session.exec(select(Authority)).all()) == 1


def test_a_value_without_vetted_support_is_reported_and_not_written(session):
    # `soil_base` has a value but no citation naming it; the blog citation is
    # from a publisher with no tier and no licence, so it supports nothing.
    record = dict(RECORD, soil_base="standard_potting", humidity_pct_min=40,
                  citations=RECORD["citations"] + [
                      {"claim": "humidity_pct_min 40", "source": "A Blog",
                       "url": "https://some-plant-blog.example/x",
                       "quote": "about 40%"}])

    report = ingest_records(session, [record])

    assert set(report.unsupported["Dracaena trifasciata"]) == {
        "soil_base", "humidity_pct_min"}
    assert {c.field for c in stored_claims(session)} == {
        "humidity_need", "light_fc_min", "toxic_to_pets"}


def test_dry_run_leaves_the_database_exactly_as_it_found_it(session):
    report = ingest_records(session, [RECORD], dry_run=True)

    # It still reports what it *would* have done, which is the point of it.
    assert report.claims_written == 3
    assert stored_claims(session) == []
    assert session.exec(select(Authority)).all() == []


def test_the_whole_verified_tranche_lands_and_resolves(session):
    """End to end: 88 researched species become queryable, cited evidence."""
    from app.data.claims.ingest import ingest_tranche
    from app.data.claims.store import resolve_from_db

    report = ingest_tranche(session)

    # 349 (b1-b5) + 81 (b6) + 42 (b7) + 41 (b8) + 54 (b9) + 47 (b10) + 51
    # (b11) = 665. Batches land as part of an ongoing /loop run over the
    # remaining curated catalog; each one is re-verified against the strict
    # loader before landing here -- see each batch's own normalizations entry
    # for what, if anything, that pass caught.
    assert report.claims_written == 665
    assert len(session.exec(select(Authority)).all()) == 8

    # A species picked out of the batch resolves to its researched values,
    # each carrying the citation it came from.
    snake = resolve_from_db(session, "Dracaena trifasciata")
    assert snake.values["humidity_need"] == "low"
    assert snake.values["water_regime"] == "dry_thoroughly_between"
    assert snake.values["toxic_to_pets"] is True
    assert snake.provenance["humidity_need"] == "sourced"


def test_two_stored_sources_disagreeing_on_cold_tolerance_refuse(session):
    """The refusal path works on stored evidence, not just in the pure layer.

    Resolving the real tranche produces no refusals, which is a fact about the
    data rather than proof the guard is connected. This wires two genuinely
    conflicting claims through the database to show it is.
    """
    from app.data.claims.store import resolve_from_db

    conflicting = {
        "scientific_name_accepted": "Testus conflictus",
        "chill_damage_f": 50,
        "citations": [
            {"claim": "chill_damage_f 50", "source": "NC State",
             "url": "https://plants.ces.ncsu.edu/testus/", "quote": "below 50"},
            {"claim": "chill_damage_f 32", "source": "Clemson",
             "url": "https://hgic.clemson.edu/testus/", "quote": "below 32"},
        ],
    }
    ingest_records(session, [conflicting])
    # The second citation asserts a different value for the same field; store
    # it directly, since one record can only carry one value per field.
    clemson = session.exec(
        select(Authority).where(Authority.name == "Clemson Cooperative Extension")
    ).first()
    if clemson is None:
        clemson = Authority(name="Clemson Cooperative Extension", tier=2)
        session.add(clemson)
        session.commit()
        session.refresh(clemson)
    session.add(Claim(
        subject="Testus conflictus", field="chill_damage_f", value_json="32",
        authority_id=clemson.id, citation_url="https://hgic.clemson.edu/testus/",
        citation_title="Clemson", quote="below 32"))
    session.commit()

    result = resolve_from_db(session, "Testus conflictus")

    assert "chill_damage_f" not in result.values
    assert [r.field for r in result.refusals] == ["chill_damage_f"]
