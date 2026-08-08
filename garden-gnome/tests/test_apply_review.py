"""Plan 3.1 acceptance: the only module that writes to the catalog is safe.

`uncertain` is not applied; a true -> false toxicity move is refused;
`rejected` is refused while a plant references the species; an ambiguous
name is refused rather than silently picked; --dry-run leaves the database
byte-identical; and the allowlist is imported, not duplicated.
"""
import shutil
from pathlib import Path

import pytest
from sqlmodel import Session, create_engine, select

from app.data.expansion import apply_review, research_review
from app.data.expansion.apply_review import apply_reviews
from app.models.models import Plant, ReviewStatus, Species


def make_species(name, common="Test Plant", toxic=False):
    return Species(
        common_name=common, scientific_name=name, light_need="medium",
        humidity_pct_min=40, humidity_pct_max=60, temp_f_min=60,
        temp_f_max=80, soil_type="mix", toxic_to_pets=toxic,
        review_status=ReviewStatus.needs_review,
    )


def entry(name, verdict, corrections=None, **extra):
    review = {"verdict": verdict, **extra}
    if corrections is not None:
        review["corrections"] = corrections
    return {"record": {"scientific_name": name}, "review": review}


@pytest.fixture()
def db(migrated_db_url):
    engine = create_engine(
        migrated_db_url, connect_args={"check_same_thread": False})
    yield engine
    engine.dispose()


def test_allowlist_is_imported_not_duplicated():
    assert apply_review.CORRECTABLE is research_review.CORRECTABLE
    assert not hasattr(apply_review, "SPECIES_FIELDS")


def test_uncertain_is_left_exactly_alone(db):
    with Session(db) as s:
        s.add(make_species("Dubius testus"))
        s.commit()
    with Session(db) as s:
        counts, refused = apply_reviews(
            [entry("Dubius testus", "uncertain")], s)
    assert counts["uncertain"] == 1
    assert counts["applied"] == 0
    assert refused == []
    with Session(db) as s:
        sp = s.exec(select(Species).where(
            Species.scientific_name == "Dubius testus")).one()
        assert sp.review_status == ReviewStatus.needs_review


def test_unknown_verdict_is_refused_not_guessed(db):
    with Session(db) as s:
        s.add(make_species("Typus errans"))
        s.commit()
    with Session(db) as s:
        counts, refused = apply_reviews(
            [entry("Typus errans", "confirmd")], s)  # the typo'd verdict
    assert counts["applied"] == 0
    assert len(refused) == 1 and "unknown verdict" in refused[0]
    with Session(db) as s:
        sp = s.exec(select(Species).where(
            Species.scientific_name == "Typus errans")).one()
        assert sp.review_status == ReviewStatus.needs_review


def test_confirmed_stamps_verified_with_the_whole_trail(db):
    with Session(db) as s:
        s.add(make_species("Confirmus testus"))
        s.commit()
    with Session(db) as s:
        counts, refused = apply_reviews([entry(
            "Confirmus testus", "confirmed",
            citation_source="NC State Extension Plant Toolbox",
            citation_url="https://plants.ces.ncsu.edu/plants/x",
            researched_by="web-research pipeline (unverified — needs human review)",
        )], s)
    assert counts["applied"] == 1 and refused == []
    with Session(db) as s:
        sp = s.exec(select(Species).where(
            Species.scientific_name == "Confirmus testus")).one()
        assert sp.review_status == ReviewStatus.verified
        assert "NC State" in sp.review_note
        assert "researched by web-research pipeline" in sp.review_note


def test_corrected_applies_allowlisted_fields_then_verifies(db):
    with Session(db) as s:
        s.add(make_species("Correctus testus"))
        s.commit()
    with Session(db) as s:
        counts, refused = apply_reviews([entry(
            "Correctus testus", "corrected",
            corrections={"temp_f_min": 55, "not_a_field": "junk"},
            citation_source="MoBot",
        )], s)
    assert counts["applied"] == 1 and refused == []
    with Session(db) as s:
        sp = s.exec(select(Species).where(
            Species.scientific_name == "Correctus testus")).one()
        assert sp.temp_f_min == 55
        assert sp.review_status == ReviewStatus.verified


def test_toxicity_true_to_false_never_goes_through(db):
    with Session(db) as s:
        s.add(make_species("Toxicus manens", toxic=True))
        s.commit()
    with Session(db) as s:
        counts, refused = apply_reviews([entry(
            "Toxicus manens", "corrected",
            corrections={"toxic_to_pets": False},
        )], s)
    assert counts["applied"] == 0
    assert len(refused) == 1 and "toxicity" in refused[0]
    with Session(db) as s:
        sp = s.exec(select(Species).where(
            Species.scientific_name == "Toxicus manens")).one()
        assert sp.toxic_to_pets is True                # still marked toxic
        assert sp.review_status == ReviewStatus.needs_review  # and not verified


def test_toxicity_false_to_true_is_allowed(db):
    """The dangerous direction is safe -> the safe direction is not blocked."""
    with Session(db) as s:
        s.add(make_species("Toxicus latens", toxic=False))
        s.commit()
    with Session(db) as s:
        counts, refused = apply_reviews([entry(
            "Toxicus latens", "corrected",
            corrections={"toxic_to_pets": True}, citation_source="ASPCA-free source",
        )], s)
    assert counts["applied"] == 1 and refused == []
    with Session(db) as s:
        sp = s.exec(select(Species).where(
            Species.scientific_name == "Toxicus latens")).one()
        assert sp.toxic_to_pets is True


def test_rejected_deletes_only_unreferenced_species(db):
    with Session(db) as s:
        s.add(make_species("Delendus liber"))
        grown = make_species("Delendus cultus")
        s.add(grown)
        s.flush()
        s.add(Plant(nickname="Growing", species_id=grown.id))
        s.commit()
    with Session(db) as s:
        counts, refused = apply_reviews([
            entry("Delendus liber", "rejected"),
            entry("Delendus cultus", "rejected"),
        ], s)
    assert counts["applied"] == 1
    assert len(refused) == 1 and "plants reference it" in refused[0]
    with Session(db) as s:
        assert s.exec(select(Species).where(
            Species.scientific_name == "Delendus liber")).first() is None
        assert s.exec(select(Species).where(
            Species.scientific_name == "Delendus cultus")).first() is not None


def test_ambiguous_name_is_refused_not_first_matched(db):
    with Session(db) as s:
        s.add(make_species("Ambiguus testus", common="One"))
        s.add(make_species("Ambiguus testus", common="Two"))
        s.commit()
    with Session(db) as s:
        counts, refused = apply_reviews(
            [entry("Ambiguus testus", "confirmed")], s)
    assert counts["applied"] == 0
    assert len(refused) == 1 and "ambiguous" in refused[0]
    with Session(db) as s:
        rows = s.exec(select(Species).where(
            Species.scientific_name == "Ambiguus testus")).all()
        assert all(
            sp.review_status == ReviewStatus.needs_review for sp in rows)


def test_dry_run_leaves_the_database_byte_identical(db, migrated_db_url, tmp_path):
    # A private copy of the migrated DB, so nothing shared is touched.
    src = Path(migrated_db_url.removeprefix("sqlite:///"))
    work = tmp_path / "dryrun.db"
    shutil.copy(src, work)
    engine = create_engine(f"sqlite:///{work.as_posix()}")
    with Session(engine) as s:
        s.add(make_species("Siccus probatus"))
        keep = make_species("Siccus alter")
        s.add(keep)
        s.commit()
    before = work.read_bytes()

    with Session(engine) as s:
        counts, refused = apply_reviews([
            entry("Siccus probatus", "confirmed", citation_source="NC State"),
            entry("Siccus alter", "rejected"),
        ], s, dry_run=True)
    engine.dispose()

    # The walk really happened — counters prove it — and nothing was written.
    assert counts["applied"] == 2
    assert refused == []
    assert work.read_bytes() == before
