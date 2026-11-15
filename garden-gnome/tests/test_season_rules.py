"""Every guidance line has a named, linked citation, or is worded as
general advice (PLAN.md section 7 and P0-12)."""
from app.services.season import rules


def test_every_cited_line_names_a_publisher_and_a_web_address():
    r = rules.rules()
    for key, line in r["lines"].items():
        src = r["sources"][line["source"]]
        assert src["name"].strip(), key
        if line["kind"] == "cited":
            assert src["url"].startswith("https://"), key
            assert line["source"] != "general", key
        else:
            assert line["kind"] == "general", key
            assert line["source"] == "general", key
            assert line["text"].startswith("General advice"), key


def test_no_citation_says_several():
    r = rules.rules()
    for src in r["sources"].values():
        assert "several" not in " ".join(str(v) for v in src.values()).lower()


def test_engineering_defaults_are_named_in_the_rules_file():
    d = rules.rules()["engineering_defaults"]
    assert d["fall_hardening_day_length_hours"] == 13.5
    assert d["fall_hardening_days_before_median_freeze"] == 42


def test_owner_facing_text_has_no_em_dash_and_no_lawn_feeding_skip():
    for key, line in rules.rules()["lines"].items():
        assert "—" not in line["text"] + line.get("low_impact_note", ""), key
    feed = rules.line("hardening_no_feed")
    assert "lawn" not in feed["text"].lower()
