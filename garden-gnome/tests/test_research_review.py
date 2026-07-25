"""Web-research review pipeline: parsing and the safety downgrades.

The pipeline drafts review verdicts for ~1688 unreviewed species. It never
writes to the catalog — apply_review.py does, from a file a human has read.
These tests cover the layer between: what the model said, and what is allowed
to reach that file.
"""
import json

from app.data.expansion import research_review as rr


# --- extracting a verdict from a model reply -------------------------------

def test_extract_json_handles_bare_object():
    assert rr.extract_json('{"verdict": "confirmed"}') == {"verdict": "confirmed"}


def test_extract_json_handles_fences_and_prose():
    """Models add fences and preamble even when told not to."""
    reply = 'Here is my assessment:\n```json\n{"verdict": "uncertain"}\n```\nHope that helps!'
    assert rr.extract_json(reply) == {"verdict": "uncertain"}


def test_extract_json_returns_none_on_garbage():
    assert rr.extract_json("I could not find this plant.") is None
    assert rr.extract_json("{not valid json}") is None


# --- the safety downgrades -------------------------------------------------

def test_confirmed_without_citation_is_downgraded():
    """A verdict with no source is an opinion. apply_review.py would stamp it
    review_status=verified, so it must not survive as 'confirmed'."""
    out = rr.sanitize({"verdict": "confirmed", "citation_source": "Some Blog"})
    assert out["verdict"] == "uncertain"


def test_confirmed_with_real_citation_survives():
    out = rr.sanitize({
        "verdict": "confirmed",
        "citation_source": "NC State Extension Plant Toolbox",
        "citation_url": "https://plants.ces.ncsu.edu/plants/monstera-deliciosa/",
    })
    assert out["verdict"] == "confirmed"


def test_corrected_without_corrections_is_downgraded():
    """Claiming the record is wrong while supplying no fix is not actionable."""
    out = rr.sanitize({
        "verdict": "corrected",
        "citation_url": "https://plants.ces.ncsu.edu/plants/x/",
        "corrections": {},
    })
    assert out["verdict"] == "uncertain"


def test_unknown_correction_fields_are_stripped():
    """apply_review.py ignores fields outside SPECIES_FIELDS; drop them here so
    a reviewer isn't shown edits that will silently do nothing."""
    out = rr.sanitize({
        "verdict": "corrected",
        "citation_url": "https://plants.ces.ncsu.edu/plants/x/",
        "corrections": {"light_need": "low", "watering_gallons": 3, "id": 99},
    })
    assert out["corrections"] == {"light_need": "low"}


def test_unrecognized_verdict_becomes_uncertain():
    for bad in ("probably fine", "", None, "APPROVED!!"):
        assert rr.sanitize({"verdict": bad})["verdict"] == "uncertain"


def test_rejected_needs_no_citation():
    """'this isn't a real distinct species' is a judgement about the record,
    not a claim about care data — and it only ever deletes a row a human
    approved for deletion."""
    assert rr.sanitize({"verdict": "rejected"})["verdict"] == "rejected"


def test_every_entry_is_marked_machine_drafted():
    """A reviewer must never mistake this for a human sign-off."""
    out = rr.sanitize({"verdict": "confirmed", "citation_url": "https://x.test/a"})
    assert "unverified" in out["researched_by"].lower()


def test_output_matches_apply_review_contract():
    """apply_review.py reads exactly these keys off the review block."""
    out = rr.sanitize({"verdict": "confirmed", "citation_url": "https://x.test/a"})
    for key in ("verdict", "citation_source", "citation_url", "corrections", "notes"):
        assert key in out
    # It calls .strip() on the three string fields, so none may be None.
    for key in ("citation_source", "citation_url", "notes"):
        assert isinstance(out[key], str)


def test_review_file_shape_is_json_serializable():
    entry = {"record": {"scientific_name": "Monstera deliciosa"},
             "review": rr.sanitize({"verdict": "uncertain"})}
    assert json.loads(json.dumps(entry))["review"]["verdict"] == "uncertain"
