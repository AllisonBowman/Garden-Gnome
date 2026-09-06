"""The offline expansion tools and the rows the claim sync mints.

A claims-minted Species (ADR 0005) carries no legacy care values at all: no
light label, no humidity band, no soil string, and a null toxicity flag. The
expansion tools were written for the Perenual era, when every row had all of
those, so each one needs a guard that recognises such a row and leaves it
alone -- validate must not bury it in "missing" issues, admit_queue must not
sample it for a citation pass its evidence already had, and genus_fill must
not count it as a sibling that says nothing.
"""
from app.data.expansion import admit_queue, genus_fill
from app.data.expansion.validate import validate_record
from app.models.models import ReviewStatus, Species, SpeciesSource


def minted_record(**over):
    rec = {
        "common_name": "Pawpaw", "scientific_name": "Asimina triloba",
        "source": SpeciesSource.claims, "review_status": "approved",
        "light_need": None, "humidity_pct_min": None, "humidity_pct_max": None,
        "temp_f_min": None, "temp_f_max": None, "soil_type": None,
        "toxic_to_pets": None, "care_notes": "", "schedules": [],
    }
    rec.update(over)
    return rec


def minted_row(name="Asimina triloba", common="Pawpaw"):
    return Species(common_name=common, scientific_name=name,
                   source=SpeciesSource.claims, source_ref="b63-native-trees.json",
                   review_status=ReviewStatus.approved, toxic_to_pets=None,
                   care_notes="")


def legacy_row(name="Asimina parviflora", common="Dwarf Pawpaw",
               source=SpeciesSource.curated):
    return Species(common_name=common, scientific_name=name, source=source,
                   light_need="medium", humidity_pct_min=40,
                   humidity_pct_max=60, temp_f_min=60, temp_f_max=80,
                   soil_type="mix", toxic_to_pets=False,
                   review_status=ReviewStatus.approved)


def test_validate_does_not_judge_a_claims_minted_row_by_its_legacy_shape():
    assert validate_record(minted_record()) == []
    # The same shape from any other pipeline is still every problem it looks like.
    assert validate_record(minted_record(source="perenual")) != []


def test_admit_queue_never_samples_a_claims_minted_row_for_the_citation_pass():
    candidates = admit_queue.review_candidates([
        legacy_row("Epipremnum aureum", "Pothos", source=SpeciesSource.perenual),
        minted_row(),
    ])

    assert [r["scientific_name"] for r in candidates] == ["Epipremnum aureum"]


def test_genus_fill_never_counts_a_claims_minted_row_as_a_sibling():
    records = genus_fill.catalog_records([legacy_row(), minted_row()])

    assert [r["scientific_name"] for r in records] == ["Asimina parviflora"]
    # The projection is the one derive_genus_fill reads.
    assert set(records[0]) == set(
        genus_fill.CORRECTABLE + ["review_status", "review_note"])
