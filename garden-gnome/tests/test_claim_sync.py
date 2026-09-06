"""Bringing the verified tranche into the catalog as rows, not only as evidence.

`ingest` stores claims and `recompute` resolves them onto whatever Species rows
exist, so a researched species with no row was researched into a void. sync.py
is the one path that mints such a row (ADR 0005), and because it runs on every
cold start it has to be safe to run again and again: it invents nothing a claim
did not say, it never renames a row, a bare genus never becomes a species, and
an unchanged tranche is a fingerprint skip rather than a rewrite.
"""
import json
import shutil
import sqlite3
from pathlib import Path

import pytest
from sqlmodel import Session, create_engine, select

from app.data.claims.ingest import ingest_records
from app.data.claims.recompute import RESOLVER_VERSION
from app.data.claims.sync import (
    FINGERPRINT_KEY, SYNC_VERSION, binomial_key, sync_catalog,
    tranche_fingerprint,
)
from app.models.models import (
    Authority, CareLog, CareSchedule, Claim, Plant, ReviewStatus, Species,
    SpeciesSource, SpeciesTrait, SyncState,
)
from tests.conftest import ROOT

NCSU = "https://plants.ces.ncsu.edu/plants/"
LEGACY = ("light_need", "humidity_pct_min", "humidity_pct_max",
          "temp_f_min", "temp_f_max", "soil_type")


@pytest.fixture()
def db(migrated_db_url, tmp_path):
    """A private, empty, compacted catalog per test.

    The sync walks and writes the whole species table, so it cannot share the
    session-scoped database with the API tests without minting rows into
    their fixtures. A copy is cheap and lets the byte-identical checks below
    mean what they say -- once it is compacted. Emptying a copy that other
    tests had filled leaves thousands of free pages, and SQLite reuses free
    pages inside a transaction without journaling their stale contents, so a
    rolled-back write leaves the file logically unchanged but not physically.
    VACUUM first, and byte equality is exactly "nothing was written".
    """
    work = tmp_path / "sync.db"
    shutil.copy(Path(migrated_db_url.removeprefix("sqlite:///")), work)
    engine = create_engine(f"sqlite:///{work.as_posix()}")
    with Session(engine) as s:
        for model in (Claim, Authority, CareLog, CareSchedule, SpeciesTrait,
                      Plant, Species, SyncState):
            for row in s.exec(select(model)).all():
                s.delete(row)
        s.commit()
    compact = sqlite3.connect(work)
    compact.execute("VACUUM")
    compact.close()
    yield engine, work
    engine.dispose()


def legacy_species(name, common="Test Plant", **over):
    fields = dict(
        common_name=common, scientific_name=name, light_need="medium",
        humidity_pct_min=40, humidity_pct_max=60, temp_f_min=60,
        temp_f_max=80, soil_type="mix", toxic_to_pets=False)
    fields.update(over)
    return Species(**fields)


def record(common, given, accepted=None, **fields):
    """One tranche record whose every value one NC State page supports."""
    url = f"{NCSU}{given.lower().replace(' ', '-')}/"
    return {
        "common_name": common,
        "scientific_name_given": given,
        "scientific_name_accepted": accepted,
        **fields,
        "citations": [{
            "claim": "; ".join(f"{k} {v}" for k, v in fields.items()),
            "source": "NC State Extension Gardener Plant Toolbox",
            "url": url, "quote": "the passage that supports it",
        }],
    }


def write_batch(directory, name, records):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).write_text(json.dumps(
        {"batch": name, "records": records}, ensure_ascii=False))


def rows(engine, name=None):
    with Session(engine) as s:
        query = select(Species)
        if name is not None:
            query = query.where(Species.scientific_name == name)
        found = s.exec(query).all()
        for sp in found:
            s.refresh(sp)
        s.expunge_all()
    return found


# --- minting ---------------------------------------------------------------

def test_a_researched_species_with_no_row_is_minted_with_nothing_invented(db, tmp_path):
    engine, _ = db
    tranche = tmp_path / "tranche"
    write_batch(tranche, "b1-test.json",
                [record("Test Plant", "Testus novus", humidity_need="low")])

    with Session(engine) as s:
        report = sync_catalog(s, directory=tranche)

    sp, = rows(engine, "Testus novus")
    assert report.species_created == 1 and report.species_linked == 0
    assert sp.source == SpeciesSource.claims
    assert sp.source_ref == "b1-test.json"
    assert sp.review_status == ReviewStatus.approved
    assert sp.common_name == "Test Plant" and sp.care_notes == ""
    # No legacy value was made up to fill the old NOT NULL columns, and above
    # all no safety verdict: null means "no record", never "safe" (ADR 0002).
    assert all(getattr(sp, col) is None for col in LEGACY)
    assert sp.toxic_to_pets is None
    # What a claim did say is resolved onto the row, with its attribution.
    assert sp.humidity_need == "low"
    assert sp.care_sources == [{
        "authority": "NC State Extension", "url": f"{NCSU}testus-novus/",
        "fields": ["humidity_need"], "inferred": False}]
    assert sp.resolver_version == RESOLVER_VERSION


def test_a_genus_subject_feeds_its_congeners_but_never_becomes_a_row(db, tmp_path):
    engine, _ = db
    tranche = tmp_path / "tranche"
    write_batch(tranche, "b1-test.json", [
        record("Amaryllis", "Hippeastrum", humidity_need="average"),
    ])
    with Session(engine) as s:
        s.add(legacy_species("Hippeastrum papilio", "Butterfly Amaryllis"))
        s.commit()

    with Session(engine) as s:
        report = sync_catalog(s, directory=tranche)

    assert report.genus_subjects == ["Hippeastrum"]
    assert report.species_created == 0
    assert rows(engine, "Hippeastrum") == []
    congener, = rows(engine, "Hippeastrum papilio")
    assert congener.humidity_need == "average"
    assert congener.care_provenance["humidity_need"] == "genus_inferred"


def test_a_shared_common_name_is_reported_and_the_row_is_minted_anyway(db, tmp_path):
    engine, _ = db
    tranche = tmp_path / "tranche"
    write_batch(tranche, "b1-test.json", [
        record("Blackberry", "Rubus fruticosus", humidity_need="average"),
    ])
    with Session(engine) as s:
        s.add(legacy_species("Rubus allegheniensis", "Blackberry"))
        s.commit()

    with Session(engine) as s:
        report = sync_catalog(s, directory=tranche)

    assert report.common_name_collisions == [("Blackberry", "Rubus fruticosus")]
    assert report.species_created == 1
    assert len(rows(engine, "Rubus fruticosus")) == 1


# --- linking ---------------------------------------------------------------

def test_a_row_known_by_its_older_name_is_linked_never_renamed(db, tmp_path):
    engine, _ = db
    tranche = tmp_path / "tranche"
    write_batch(tranche, "b1-test.json", [
        record("Snake Plant", "Sansevieria trifasciata",
               accepted="Dracaena trifasciata", humidity_need="low"),
    ])
    with Session(engine) as s:
        s.add(legacy_species("Sansevieria trifasciata", "Snake Plant",
                             light_need="low", care_notes="Tough."))
        s.commit()

    with Session(engine) as s:
        report = sync_catalog(s, directory=tranche)

    assert report.species_linked == 1 and report.species_created == 0
    assert rows(engine, "Dracaena trifasciata") == []
    sp, = rows(engine, "Sansevieria trifasciata")
    # toxicity.lookup and every user's plants key on scientific_name; the
    # accepted name rides beside it so claims keyed by it resolve here.
    assert sp.scientific_name_accepted == "Dracaena trifasciata"
    assert sp.humidity_need == "low"
    # Linking touches identity only: the legacy values stay exactly as found.
    assert sp.light_need == "low" and sp.care_notes == "Tough."
    assert sp.toxic_to_pets is False


def test_the_hybrid_sign_does_not_split_one_name_into_two_rows(db, tmp_path):
    engine, _ = db
    tranche = tmp_path / "tranche"
    write_batch(tranche, "b1-test.json", [
        record("Glossy Abelia", "Abelia x grandiflora",
               accepted="Abelia × grandiflora", humidity_need="average"),
    ])
    with Session(engine) as s:
        s.add(legacy_species("Abelia  X grandiflora", "Glossy Abelia"))
        s.commit()

    with Session(engine) as s:
        report = sync_catalog(s, directory=tranche)

    assert report.species_created == 0 and report.species_linked == 1
    sp, = rows(engine, "Abelia  X grandiflora")
    assert sp.scientific_name_accepted == "Abelia × grandiflora"
    assert sp.humidity_need == "average"


def test_an_ambiguous_match_links_nothing_and_says_so(db, tmp_path):
    engine, _ = db
    tranche = tmp_path / "tranche"
    write_batch(tranche, "b1-test.json", [
        record("Snake Plant", "Sansevieria trifasciata",
               accepted="Dracaena trifasciata", humidity_need="low"),
    ])
    with Session(engine) as s:
        s.add(legacy_species("Sansevieria trifasciata", "One"))
        s.add(legacy_species("Sansevieria trifasciata", "Two"))
        s.commit()

    with Session(engine) as s:
        report = sync_catalog(s, directory=tranche)

    assert report.ambiguous == ["Dracaena trifasciata"]
    assert report.species_linked == 0 and report.species_created == 0
    assert all(sp.scientific_name_accepted is None
               for sp in rows(engine, "Sansevieria trifasciata"))


# --- re-running ------------------------------------------------------------

def test_a_second_run_is_a_fingerprint_skip_and_force_changes_nothing(db, tmp_path):
    engine, work = db
    tranche = tmp_path / "tranche"
    write_batch(tranche, "b1-test.json", [
        record("Test Plant", "Testus novus", humidity_need="low"),
        record("Snake Plant", "Sansevieria trifasciata",
               accepted="Dracaena trifasciata", light_fc_min=100),
    ])
    with Session(engine) as s:
        s.add(legacy_species("Sansevieria trifasciata", "Snake Plant"))
        s.commit()

    with Session(engine) as s:
        first = sync_catalog(s, directory=tranche)
    before = work.read_bytes()

    with Session(engine) as s:
        second = sync_catalog(s, directory=tranche)
    assert second.skipped is True
    assert work.read_bytes() == before

    with Session(engine) as s:
        forced = sync_catalog(s, directory=tranche, force=True)
    assert forced.skipped is False
    assert forced.claims_written == 0 and forced.claims_already_present == first.claims_written
    assert forced.species_created == 0 and forced.species_linked == 0
    assert forced.recompute.species_updated == 0
    assert work.read_bytes() == before


def test_a_changed_tranche_is_not_a_skip(db, tmp_path):
    engine, _ = db
    tranche = tmp_path / "tranche"
    write_batch(tranche, "b1-test.json",
                [record("Test Plant", "Testus novus", humidity_need="low")])
    with Session(engine) as s:
        sync_catalog(s, directory=tranche)

    write_batch(tranche, "b2-test.json",
                [record("Other Plant", "Testus alter", humidity_need="high")])
    with Session(engine) as s:
        report = sync_catalog(s, directory=tranche)

    assert report.skipped is False
    assert report.species_created == 1
    assert len(rows(engine, "Testus alter")) == 1


def test_the_fingerprint_moves_with_the_rules_not_only_the_files(tmp_path):
    tranche = tmp_path / "tranche"
    write_batch(tranche, "b1-test.json", [record("A", "Testus a")])

    fingerprint = tranche_fingerprint(tranche)

    assert fingerprint.endswith(f":{RESOLVER_VERSION}:{SYNC_VERSION}")
    write_batch(tranche, "b1-test.json", [record("A", "Testus a", humidity_need="low")])
    assert tranche_fingerprint(tranche) != fingerprint


def test_dry_run_leaves_the_database_byte_identical(db):
    """On the real tranche, so the transaction is as large as it will ever be."""
    engine, work = db
    with Session(engine) as s:
        s.add(legacy_species("Dracaena trifasciata", "Snake Plant"))
        s.commit()
    before = work.read_bytes()

    with Session(engine) as s:
        report = sync_catalog(s, dry_run=True)

    # The walk happened -- counters prove it -- and nothing was written, not
    # even the fingerprint that would make the next real run a skip.
    assert report.skipped is False
    assert report.species_created > 100 and report.species_linked == 0
    assert work.read_bytes() == before
    with Session(engine) as s:
        assert s.get(SyncState, FINGERPRINT_KEY) is None


# --- the real tranche ------------------------------------------------------

def _seed_curated_catalog(session):
    catalog = json.loads(
        (ROOT / "app" / "data" / "species_catalog.json").read_text(encoding="utf-8"))
    for entry in catalog:
        session.add(Species(**entry["species"]))
    session.commit()


def test_every_researched_species_ends_up_on_exactly_one_row(db):
    """The invariant the whole slice rests on, checked over the real corpus.

    After a sync, `scientific_name_accepted or scientific_name` on some row is
    byte-for-byte a `Claim.subject` for every species-level tranche record --
    that is what lets the resolver find a row's evidence -- and there is one
    such row, never two. Counts are deliberately not asserted: the research
    loop owns them.
    """
    from app.data.claims.ingest import tranche_records

    engine, _ = db
    with Session(engine) as s:
        _seed_curated_catalog(s)
        curated_before = {sp.scientific_name: sp.toxic_to_pets
                          for sp in s.exec(select(Species)).all()}

    with Session(engine) as s:
        report = sync_catalog(s)
        species = s.exec(select(Species)).all()
        claims = s.exec(select(Claim)).all()
        by_subject = {}
        for sp in species:
            by_subject.setdefault(
                sp.scientific_name_accepted or sp.scientific_name, []).append(sp)
        toxic_claims = {c.subject for c in claims if c.field == "toxic_to_pets"}

        assert report.skipped is False and report.ambiguous == []
        assert report.species_created > 0 and report.species_linked > 0
        for _batch, rec in tranche_records():
            subject = (rec.get("scientific_name_accepted")
                       or rec.get("scientific_name_given")).strip()
            if len(subject.split()) < 2:
                assert subject in report.genus_subjects
                assert subject not in by_subject
                continue
            assert len(by_subject.get(subject, [])) == 1, subject

        minted = [sp for sp in species if sp.source == SpeciesSource.claims]
        for sp in minted:
            assert all(getattr(sp, col) is None for col in LEGACY), sp.scientific_name
            # False only ever comes from a citation -- never from a default.
            if sp.toxic_to_pets is False:
                assert sp.scientific_name in toxic_claims, sp.scientific_name
        # Legacy rows keep their toxicity flag: nothing here backfills it.
        for sp in species:
            if sp.scientific_name in curated_before and sp.scientific_name not in toxic_claims:
                assert sp.toxic_to_pets == curated_before[sp.scientific_name]

    with Session(engine) as s:
        assert sync_catalog(s).skipped is True


# --- the pieces the sync leans on ------------------------------------------

@pytest.mark.parametrize("a,b", [
    ("Abelia × grandiflora", "abelia x grandiflora"),
    ("Dracaena  trifasciata ", "Dracaena trifasciata"),
])
def test_binomial_key_treats_spelling_variants_as_one_name(a, b):
    assert binomial_key(a) == binomial_key(b)


def test_ingest_with_commit_false_leaves_the_transaction_to_the_caller(session):
    for model in (Claim, Authority):
        for row in session.exec(select(model)).all():
            session.delete(row)
    session.commit()

    report = ingest_records(
        session, [record("Test Plant", "Testus novus", humidity_need="low")],
        commit=False)

    assert report.claims_written == 1
    assert len(session.exec(select(Claim)).all()) == 1
    session.rollback()
    assert session.exec(select(Claim)).all() == []
