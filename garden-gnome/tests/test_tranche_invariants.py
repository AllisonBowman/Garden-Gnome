"""Shape invariants over every verified tranche file, not just the one being landed.

`claims_from_record` pairs values to citations and `recompute` writes the
resolved value straight onto the Species row with a bare `setattr` -- there is
no enum coercion or validation anywhere between a tranche file and the
column. So a researcher writing a sentence into `soil_drainage`, or the
literal string "null" into `scientific_name_accepted`, lands silently and
corrupts the controlled vocabulary the UI filters on. Both have happened
(b36 and b23 respectively) and were caught only by a hand-run script at
landing time. This test makes those checks permanent, across the whole
corpus, so a batch that drifts fails here instead of in production.

Everything asserted here is something the pipeline cannot tolerate. Batch
conventions that the loader does not depend on (citation-label phrasing,
name_note coverage) are deliberately left to the loader tests and to review.
"""
import glob
import json
from collections import defaultdict
from pathlib import Path

import pytest

from app.data.claims.sync import binomial_key
from app.models.models import (
    EatenPart,
    FertilizeStrength, HumidityNeed, OutdoorSunExposure, SoilBase,
    SoilDrainage, WaterRegime)

VERIFIED = Path(__file__).resolve().parents[1] / "app" / "data" / "verified"

# The exact shape every tranche record carries -- the research schema, not the
# full Species table. A key outside this set is scaffolding that leaked.
TRANCHE_FIELDS = frozenset({
    "common_name", "scientific_name_given", "scientific_name_accepted",
    "name_note", "is_houseplant", "toxic_to_pets", "toxicity_detail",
    "chill_damage_f", "cool_rest_note",
    "day_f_min", "day_f_max", "night_f_min", "night_f_max",
    "humidity_need", "humidity_pct_min", "humidity_pct_max",
    "light_fc_min", "light_fc_good", "direct_sun_hours_max",
    "outdoor_sun_exposure",
    "soil_base", "soil_drainage", "soil_ph_min", "soil_ph_max",
    "water_regime", "water_dry_down_target", "water_check_depth_cm",
    "water_growing_days_est", "water_dormant_days_est", "water_estimate_basis",
    "fertilize_interval_days", "fertilize_active_months", "fertilize_strength",
    "is_edible", "attracts_pollinators", "climbs", "eaten_parts",
    "mature_height_in_min", "mature_height_in_max",
    "mature_spread_in_min", "mature_spread_in_max",
    "unknowns", "citations",
})

ENUM_FIELDS = {
    "soil_base": {e.value for e in SoilBase},
    "soil_drainage": {e.value for e in SoilDrainage},
    "water_regime": {e.value for e in WaterRegime},
    "humidity_need": {e.value for e in HumidityNeed},
    "fertilize_strength": {e.value for e in FertilizeStrength},
}

# `outdoor_sun_exposure` is declared list[str] on the model, so the enum is
# not enforced at the column -- which is exactly why it has to be here.
SUN_EXPOSURE = {e.value for e in OutdoorSunExposure}
# The same for `eaten_parts` (0023): a list of EatenPart tokens, only on a
# record that says the plant is eaten, with a citation that names the field.
EATEN_PARTS = {e.value for e in EatenPart}


def _batches():
    for path in sorted(glob.glob(str(VERIFIED / "b*.json"))):
        yield Path(path).name, json.loads(Path(path).read_text())["records"]


def _records():
    for batch, records in _batches():
        for record in records:
            yield batch, record


def _label(batch, record):
    return f"{batch}: {record.get('common_name') or record.get('scientific_name_given')}"


@pytest.mark.parametrize("batch,record", list(_records()), ids=lambda x: x if isinstance(x, str) else "")
def test_enum_columns_hold_a_token_not_prose(batch, record):
    for field, allowed in ENUM_FIELDS.items():
        value = record.get(field)
        assert value is None or value in allowed, (
            f"{_label(batch, record)}: {field}={value!r} is not one of "
            f"{sorted(allowed)} -- recompute would write this straight into "
            f"the column")


@pytest.mark.parametrize("batch,record", list(_records()), ids=lambda x: x if isinstance(x, str) else "")
def test_eaten_parts_is_a_list_of_known_tokens_on_a_plant_recorded_as_eaten(batch, record):
    value = record.get("eaten_parts")
    if value is None:
        return
    assert isinstance(value, list) and value, _label(batch, record)
    assert set(value) <= EATEN_PARTS, f"{_label(batch, record)}: eaten_parts={value!r}"
    assert len(set(value)) == len(value), f"{_label(batch, record)}: a part twice"
    assert record.get("is_edible") is True, (
        f"{_label(batch, record)}: eaten_parts on a record not recorded as eaten")
    name = record.get("scientific_name_accepted") or record.get("scientific_name_given") or ""
    assert len(name.split()) >= 2, (
        f"{_label(batch, record)}: eaten_parts on a bare genus record, which no species can take")
    citations = record.get("citations") or []
    minted = [c for c in citations if (c.get("claim") or "").startswith("eaten_parts ")]
    assert minted, f"{_label(batch, record)}: no citation names eaten_parts"
    behind = [(c.get("url"), c.get("quote")) for c in citations
              if "is_edible" in (c.get("claim") or "")]
    for c in minted:
        assert (c.get("url"), c.get("quote")) in behind, (
            f"{_label(batch, record)}: the eaten_parts citation does not rest on the "
            f"url and quote of the citation behind is_edible")


@pytest.mark.parametrize("batch,record", list(_records()), ids=lambda x: x if isinstance(x, str) else "")
def test_sun_exposure_is_a_list_of_known_tokens(batch, record):
    value = record.get("outdoor_sun_exposure")
    if value is None:
        return
    assert isinstance(value, list), _label(batch, record)
    assert set(value) <= SUN_EXPOSURE, (
        f"{_label(batch, record)}: outdoor_sun_exposure={value!r}")


@pytest.mark.parametrize("batch,record", list(_records()), ids=lambda x: x if isinstance(x, str) else "")
def test_no_key_outside_the_research_schema(batch, record):
    extra = set(record) - TRANCHE_FIELDS
    assert not extra, f"{_label(batch, record)}: stray keys {sorted(extra)}"


@pytest.mark.parametrize("batch,record", list(_records()), ids=lambda x: x if isinstance(x, str) else "")
def test_null_is_json_null_not_the_word(batch, record):
    # A missing value encoded as the string "null" is not missing to the
    # loader -- it is a populated string, and would be filed as evidence.
    for field, value in record.items():
        if isinstance(value, str):
            assert value.strip().lower() != "null", (
                f"{_label(batch, record)}: {field} holds the string 'null'")


@pytest.mark.parametrize("batch,record", list(_records()), ids=lambda x: x if isinstance(x, str) else "")
def test_the_record_can_be_named_and_typed(batch, record):
    assert record.get("common_name"), f"{batch}: a record has no common_name"
    assert record.get("scientific_name_given"), _label(batch, record)
    toxic = record.get("toxic_to_pets")
    assert toxic is None or isinstance(toxic, bool), (
        f"{_label(batch, record)}: toxic_to_pets={toxic!r} is not a bool")


@pytest.mark.parametrize("batch,record", list(_records()), ids=lambda x: x if isinstance(x, str) else "")
def test_every_citation_is_a_real_pointer(batch, record):
    for c in record.get("citations") or []:
        for key in ("claim", "source", "url", "quote"):
            assert (c.get(key) or "").strip(), (
                f"{_label(batch, record)}: citation missing {key}: {c}")


def _binomial(name):
    # "Abelia × grandiflora", "Abelia ×grandiflora" and "Abelia x grandiflora"
    # are one name. Imported, not re-typed: a private copy of this rule is
    # exactly how the corpus check and the sync came to disagree about a
    # hybrid's spacing.
    return binomial_key(name)


@pytest.mark.parametrize("spelling", [
    "Nepeta × faassenii", "Nepeta ×faassenii", "Nepeta x faassenii"])
def test_the_duplicate_check_sees_one_name_however_a_source_spelled_it(spelling):
    """The guard below is only as good as this key. Before the hybrid marker was
    normalised, "Genus ×epithet" and "Genus × epithet" keyed apart, so one plant
    researched twice under the two spellings passed the check unnoticed."""
    assert _binomial(spelling) == "nepeta x faassenii"
    # and a different taxon is still a different name
    assert _binomial("Nepeta faassenii") != _binomial("Nepeta × faassenii")


def test_no_species_is_researched_twice():
    """One species, one record. `ingest_tranche` only notices a duplicate when
    the citations are byte-identical, so a species researched again under a
    synonym (or with fresh citations) would land as a second, conflicting set
    of claims about the same subject."""
    seen = defaultdict(set)
    for batch, record in _records():
        for key in ("scientific_name_given", "scientific_name_accepted"):
            name = _binomial(record.get(key))
            if name:
                seen[name].add(batch)
    duplicated = {name: sorted(b) for name, b in seen.items() if len(b) > 1}
    assert not duplicated, f"species present in more than one batch: {duplicated}"
