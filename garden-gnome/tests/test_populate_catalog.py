"""Merging the free catalog passes.

merge_one / merge_reports / coverage are pure, so the precedence rules are
testable without a database. The rule that matters most: a duplicate row is
never "improved" — removing it beats filling it in.
"""
from app.data.expansion import populate_catalog as pc


def entry(name, verdict="uncertain", corrections=None, notes="", record=None):
    return {
        "record": record or {"scientific_name": name},
        "review": {
            "verdict": verdict,
            "citation_source": "src",
            "citation_url": f"https://example/{name.replace(' ', '_')}",
            "corrections": corrections or {},
            "notes": notes,
            "researched_by": "test",
        },
    }


def test_rejection_wins_over_any_enrichment():
    """A duplicate should be removed, not enriched — filling its care data is
    effort spent on a row that shouldn't exist."""
    merged = pc.merge_one(
        {"scientific_name": "Scindapsus aureus"},
        [
            {"verdict": "corrected", "corrections": {"humidity_pct_min": 50}, "notes": "genus"},
            {"verdict": "rejected", "corrections": {}, "notes": "duplicate of Epipremnum aureum"},
        ],
    )
    assert merged["verdict"] == "rejected"
    assert merged["corrections"] == {}


def test_complementary_corrections_are_unioned():
    """The two sources answer different questions, so they compose."""
    merged = pc.merge_one(
        {"scientific_name": "Anthurium veitchii"},
        [
            {"verdict": "corrected", "corrections": {"humidity_pct_min": 50, "light_need": "low"}},
            {"verdict": "corrected", "corrections": {"scientific_name": "Anthurium veitchii"}},
        ],
    )
    assert merged["verdict"] == "corrected"
    assert merged["corrections"]["humidity_pct_min"] == 50
    assert merged["corrections"]["scientific_name"] == "Anthurium veitchii"


def test_taxonomy_wins_on_names_genus_keeps_care():
    later_taxonomy = [
        {"verdict": "corrected", "corrections": {"scientific_name": "Wrong name", "soil_type": "peat"}},
        {"verdict": "corrected", "corrections": {"scientific_name": "Right name", "soil_type": "loam"}},
    ]
    merged = pc.merge_one({"scientific_name": "x"}, later_taxonomy)
    assert merged["corrections"]["scientific_name"] == "Right name"  # last wins on names
    assert merged["corrections"]["soil_type"] == "peat"              # first keeps care


def test_no_corrections_stays_uncertain():
    merged = pc.merge_one({"scientific_name": "x"}, [
        {"verdict": "uncertain", "corrections": {}},
        {"verdict": "uncertain", "corrections": {}},
    ])
    assert merged["verdict"] == "uncertain"


def test_empty_input_is_handled():
    merged = pc.merge_one({"scientific_name": "x"}, [])
    assert merged["verdict"] == "uncertain"
    assert merged["corrections"] == {}


def test_merge_reports_keys_by_species_and_preserves_order():
    genus = [entry("Anthurium veitchii", "corrected", {"soil_type": "peat"}),
             entry("Ficus lyrata", "uncertain")]
    wiki = [entry("Anthurium veitchii", "corrected", {"scientific_name": "Anthurium veitchii"})]
    merged = pc.merge_reports(genus, wiki)
    assert [m["record"]["scientific_name"] for m in merged] == ["Anthurium veitchii", "Ficus lyrata"]
    first = merged[0]["review"]["corrections"]
    assert first["soil_type"] == "peat" and "scientific_name" in first


def test_merge_reports_ignores_entries_without_a_name():
    merged = pc.merge_reports([{"record": {}, "review": {"verdict": "uncertain"}}])
    assert merged == []


# --- coverage ---------------------------------------------------------------

CARE = ["light_need", "soil_type"]


def test_coverage_counts_duplicates_separately():
    entries = [{
        "record": {"scientific_name": "a"},
        "review": {"verdict": "rejected", "corrections": {}},
    }]
    assert pc.coverage(entries, CARE)["duplicates"] == 1


def test_coverage_distinguishes_filled_partial_and_untouched():
    entries = [
        # every care field present after corrections -> filled
        {"record": {"scientific_name": "a", "light_need": "low", "soil_type": None},
         "review": {"verdict": "corrected", "corrections": {"soil_type": "peat"}}},
        # still missing one -> partial
        {"record": {"scientific_name": "b", "light_need": None, "soil_type": None},
         "review": {"verdict": "corrected", "corrections": {"soil_type": "peat"}}},
        # nothing proposed -> needs the paid pass
        {"record": {"scientific_name": "c", "light_need": None, "soil_type": None},
         "review": {"verdict": "uncertain", "corrections": {}}},
    ]
    stats = pc.coverage(entries, CARE)
    assert stats == {"total": 3, "duplicates": 0, "filled": 1,
                     "partial": 1, "still_needs_research": 1}


def test_coverage_treats_blank_strings_as_missing():
    entries = [{
        "record": {"scientific_name": "a", "light_need": "  ", "soil_type": "peat"},
        "review": {"verdict": "corrected", "corrections": {"soil_type": "peat"}},
    }]
    assert pc.coverage(entries, CARE)["partial"] == 1


# --- integration: the three passes compose ----------------------------------

def test_free_passes_compose_end_to_end():
    """genus_fill + wiki_enrich + merge over a catalog shaped like the real one.

    Guards the interfaces between the three modules — a change to any verdict
    shape shows up here rather than at runtime over 1,688 records."""
    from app.data.expansion import genus_fill as gf, wiki_enrich as we

    care = ["light_need", "humidity_pct_min", "soil_type", "toxic_to_pets"]

    def approved(name):
        return {"scientific_name": name, "light_need": "bright_indirect",
                "humidity_pct_min": 50, "humidity_pct_max": 70, "temp_f_min": 60,
                "temp_f_max": 85, "soil_type": "peat-based", "toxic_to_pets": True}

    def pending(name):
        return {"scientific_name": name, "light_need": None, "humidity_pct_min": None,
                "humidity_pct_max": None, "temp_f_min": None, "temp_f_max": None,
                "soil_type": None, "toxic_to_pets": None, "common_name": "",
                "care_notes": "", "review_status": "needs_review",
                "review_note": "no soil data — defaulted"}

    siblings = [approved("Anthurium andraeanum"), approved("Anthurium clarinervium")]
    has_sibling, orphan, synonym = (
        pending("Anthurium veitchii"), pending("Calathea orbifolia"),
        pending("Scindapsus aureus"),
    )

    def wiki_for(name):
        if name == "Scindapsus aureus":
            return {"title": "Epipremnum aureum", "extract": "pothos",
                    "url": "https://en.wikipedia.org/wiki/Epipremnum_aureum",
                    "redirected_from": name, "is_disambiguation": False}
        return {"title": name, "extract": "A species of flowering plant.",
                "url": "u", "redirected_from": None, "is_disambiguation": False}

    others = {"epipremnum aureum"}
    genus_report, wiki_report = [], []
    for rec, sibs in [(has_sibling, siblings), (orphan, []), (synonym, [])]:
        name = rec["scientific_name"]
        genus_report.append({"record": rec, "review": gf.derive_genus_fill(rec, sibs)})
        wiki_report.append({"record": rec, "review": we.derive_verdict(rec, wiki_for(name), others)})

    merged = pc.merge_reports(genus_report, wiki_report)
    by_name = {m["record"]["scientific_name"]: m["review"] for m in merged}

    # filled from its genus
    assert by_name["Anthurium veitchii"]["verdict"] == "corrected"
    assert by_name["Anthurium veitchii"]["corrections"]["soil_type"] == "peat-based"
    # no approved sibling and nothing taxonomic to say -> honest uncertain
    assert by_name["Calathea orbifolia"]["verdict"] == "uncertain"
    # duplicate wins over any enrichment
    assert by_name["Scindapsus aureus"]["verdict"] == "rejected"

    stats = pc.coverage(merged, care)
    assert stats["duplicates"] == 1
    assert stats["filled"] == 1
    assert stats["still_needs_research"] == 1
