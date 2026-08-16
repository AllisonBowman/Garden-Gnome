"""Turning the verified tranche into Claims.

The tranche is 40 hand-researched species carrying 293 citations. Loading it as
bare column writes would throw the citations away and leave the catalog exactly
as unaccountable as before, so every value enters as a Claim attached to the
citation that supports it (ADR 0001).

A value the citations do not actually support is reported, never invented. That
case is the whole reason this runs as code instead of a bulk insert.
"""
from app.data.claims.tranche import claims_from_record


CLEMSON_URL = "https://hgic.clemson.edu/factsheet/indoor-plants"
NCSU_URL = "https://plants.ces.ncsu.edu/plants/dracaena-trifasciata/"

RECORD = {
    "common_name": "Snake Plant",
    "scientific_name_given": "Sansevieria trifasciata",
    "scientific_name_accepted": "Dracaena trifasciata",
    "humidity_need": "low",
    "water_regime": "dry_thoroughly_between",
    "water_dormant_days_est": 45,
    "light_fc_min": 100,
    "citations": [
        {
            "claim": "light_fc_min 100 and light_fc_good 200",
            "source": "Clemson HGIC 1450, Indoor Plants",
            "url": CLEMSON_URL,
            "quote": "Low (minimum 100 ft-c)",
        },
        {
            "claim": "water_regime dry_thoroughly_between; water_dormant_days_est 45",
            "source": "NC State Extension Gardener Plant Toolbox",
            "url": NCSU_URL,
            "quote": "Water thoroughly, then allow to dry",
        },
        {
            "claim": "humidity_need low",
            "source": "NC State Extension Gardener Plant Toolbox",
            "url": NCSU_URL,
            "quote": "Tolerates low humidity",
        },
    ],
}


def test_each_value_becomes_a_claim_carrying_the_citation_that_supports_it():
    claims, unsupported = claims_from_record(RECORD)
    by_field = {c.field: c for c in claims}

    assert by_field["humidity_need"].value == "low"
    assert by_field["humidity_need"].citation_url == NCSU_URL
    assert by_field["humidity_need"].authority_name == (
        "NC State Extension Gardener Plant Toolbox")

    # One citation can support more than one field, and does here.
    assert by_field["water_regime"].citation_url == NCSU_URL
    assert by_field["water_dormant_days_est"].value == 45
    assert by_field["light_fc_min"].citation_url == CLEMSON_URL

    assert unsupported == []


def test_a_value_no_citation_supports_is_reported_not_invented():
    orphan = dict(RECORD, soil_ph_min=6.0)

    claims, unsupported = claims_from_record(orphan)

    assert "soil_ph_min" in unsupported
    assert "soil_ph_min" not in {c.field for c in claims}


def test_one_citation_covering_a_range_supports_both_ends():
    # "day_f 70-85" is how the tranche cites a pair of columns once.
    record = {
        "scientific_name_accepted": "Epipremnum aureum",
        "day_f_min": 70, "day_f_max": 85,
        "citations": [{"claim": "day_f 70-85 and night_f 60-70",
                       "source": "Clemson HGIC 1568", "url": CLEMSON_URL,
                       "quote": "70 to 85 degrees"}],
    }

    claims, unsupported = claims_from_record(record)

    assert {c.field for c in claims} == {"day_f_min", "day_f_max"}
    assert unsupported == []


def test_a_prose_restatement_rides_on_its_structured_companion():
    # `toxicity_detail` is the readable form of what the `toxic_to_pets`
    # citation says, from the same source. It is one fact recorded twice, so
    # it inherits that citation rather than counting as unsupported.
    record = {
        "scientific_name_accepted": "Dracaena trifasciata",
        "toxic_to_pets": True,
        "toxicity_detail": "NC State rates poison severity Low; saponins.",
        "citations": [{"claim": "toxic_to_pets true", "source": "NC State",
                       "url": NCSU_URL, "quote": "Poison severity: Low"}],
    }

    claims, unsupported = claims_from_record(record)
    by_field = {c.field: c for c in claims}

    assert by_field["toxicity_detail"].citation_url == NCSU_URL
    assert unsupported == []


def test_the_researchers_own_reasoning_is_not_a_claim_about_the_plant():
    # `water_estimate_basis` records the assumptions behind an estimate --
    # pot, medium, light. No source said it; it is annotation, and filing it
    # as evidence would attribute our own reasoning to an authority.
    record = {
        "scientific_name_accepted": "Dracaena trifasciata",
        "water_estimate_basis": "Assumes a well-drained mix in low winter light.",
        "citations": [],
    }

    claims, unsupported = claims_from_record(record)

    assert claims == []
    assert unsupported == []


def test_the_accepted_name_is_the_subject_not_the_one_we_were_given():
    # Everything joins on the binomial, so a claim filed under a synonym would
    # never be found again.
    claims, _ = claims_from_record(RECORD)

    assert {c.subject for c in claims} == {"Dracaena trifasciata"}
