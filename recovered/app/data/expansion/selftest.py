"""Self-test for the expansion pipeline — no network, no API key needed.

Run from garden-gnome/:  python -m app.data.expansion.selftest

Covers: the Perenual field mapper (fixtures), the validator (synthetic bad
records AND the real curated catalog, which must pass), near-duplicate
detection, and the weighted sampler.
"""
import json
from pathlib import Path

from app.data.expansion.perenual import (
    PerenualClient, map_perenual_record, map_sunlight, parse_benchmark,
    zone_to_temp_range,
)
from app.data.expansion.sample import is_top_houseplant, weighted_sample
from app.data.expansion.validate import find_near_duplicates, validate_record

FIXTURES = Path(__file__).parent / "fixtures"
CATALOG = Path(__file__).parent.parent / "species_catalog.json"
passed = 0


def check(cond: bool, msg: str) -> None:
    global passed
    assert cond, f"FAIL: {msg}"
    passed += 1
    print(f"  ok: {msg}")


def main() -> int:
    print("mapper --")
    check(parse_benchmark({"value": "5-7", "unit": "days"}, "Average")[:2] == (5, 7),
          "benchmark '5-7 days' parses to (5, 7)")
    check(parse_benchmark({"value": None, "unit": "days"}, "Minimum")[:2] == (14, 30),
          "missing benchmark falls back to watering category")
    check(map_sunlight(["part shade"])[0] == "medium", "part shade -> medium")
    check(map_sunlight(["full sun"])[0] == "direct", "full sun -> direct")
    check(map_sunlight(["lunar glow"])[1] is not None, "unknown sunlight term produces warning")
    t_lo, t_hi, _ = zone_to_temp_range({"min": "10", "max": "12"}, "Average")
    check(40 <= t_lo <= 65 and t_hi in (85, 90), f"zone 10-12 -> plausible indoor range ({t_lo}-{t_hi}F)")

    client = PerenualClient(mock_dir=str(FIXTURES))
    details = client.details(2773)
    sections = client.care_guide_sections(2773)
    rec, warns = map_perenual_record(details, sections)
    check(rec["scientific_name"] == "Monstera deliciosa", "fixture maps scientific name")
    check(rec["source"] == "perenual" and rec["source_ref"] == "2773",
          "record tagged source=perenual with Perenual id")
    check(rec["toxic_to_pets"] is True, "poisonous_to_pets=1 -> toxic_to_pets True")
    water = next(s for s in rec["schedules"] if s["care_type"] == "water")
    check((water["interval_days_min"], water["interval_days_max"]) == (7, 10),
          "water schedule from benchmark 7-10")
    check(any(s["care_type"] == "prune" for s in rec["schedules"]),
          "pruning care-guide section produces prune schedule")
    check("top two inches" in water["notes"], "care-guide watering text lands in schedule notes")
    check(validate_record(rec) == [], f"mapped fixture record passes validation (warns: {warns})")

    rec2, warns2 = map_perenual_record(client.details(1847), [])
    check(any("soil" in w for w in warns2), "empty soil array produces warning")
    check(rec2["humidity_pct_min"] == 30, "Minimum watering -> derived humidity 30-50")

    print("validator --")
    bad = dict(rec, humidity_pct_min=80, humidity_pct_max=20)
    check(any("humidity" in i for i in validate_record(bad)), "inverted humidity flagged")
    bad = dict(rec, temp_f_min=5)
    check(any("temp_f_min" in i for i in validate_record(bad)), "temp_f_min 5F flagged as implausible")
    bad = dict(rec, schedules=[dict(rec["schedules"][0], care_type="water",
                                    interval_days_min=200, interval_days_max=300)])
    check(any("outside plausible window" in i for i in validate_record(bad)),
          "watering every 200-300 days flagged")
    bad = dict(rec, scientific_name="(scientific name for X — fill in)")
    check(any("placeholder" in i or "binomial" in i for i in validate_record(bad)),
          "stub placeholder scientific name flagged")
    stub_like = dict(rec, schedules=[])
    check(any("no water schedule" in i for i in validate_record(stub_like)),
          "missing water schedule flagged")

    print("near-duplicates --")
    existing = [("Snake Plant", "Dracaena trifasciata"), ("Pothos", "Epipremnum aureum")]
    batch = [
        dict(rec, common_name="Snake plant", scientific_name="Dracaena trifasciata"),
        dict(rec, common_name="Golden Pothos", scientific_name="Epipremnum aureum 'Golden'"),
        dict(rec, common_name="Peace Lily", scientific_name="Spathiphyllum wallisii"),
    ]
    flags = find_near_duplicates(batch, existing)
    check("Dracaena trifasciata" in flags, "exact duplicate vs existing catalog flagged")
    check(any("near-duplicate" in r for r in flags.get("Epipremnum aureum 'Golden'", [])),
          "cultivar near-duplicate flagged")
    check("Spathiphyllum wallisii" not in flags, "genuinely new species not flagged")

    print("real catalog sanity --")
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    fails = []
    for entry in catalog:
        r = {**entry["species"], "schedules": entry["schedules"],
             "traits": entry.get("traits", [])}
        issues = validate_record(r)
        if issues:
            fails.append((r["scientific_name"], issues))
    check(fails == [], f"all {len(catalog)} curated records pass validation "
                       f"(failures: {fails[:3]})")

    print("sampler --")
    pool = [dict(rec, common_name=f"Rare Plant {i}", scientific_name=f"Genus species{i}")
            for i in range(180)]
    pool += [
        dict(rec, common_name="Golden Pothos", scientific_name="Epipremnum aureum"),
        dict(rec, common_name="Monstera", scientific_name="Monstera deliciosa"),
        dict(rec, common_name="ZZ Plant", scientific_name="Zamioculcas zamiifolia"),
        dict(rec, common_name="Peace Lily", scientific_name="Spathiphyllum wallisii"),
        dict(rec, common_name="Snake Plant", scientific_name="Dracaena trifasciata"),
    ]
    sampled = weighted_sample(pool, fraction=0.075, seed=7)
    check(len(sampled) == round(len(pool) * 0.075), f"sample size ~7.5% ({len(sampled)}/{len(pool)})")
    top_in_sample = sum(1 for r in sampled if is_top_houseplant(r))
    check(top_in_sample == 5, f"all top houseplants guaranteed a review slot ({top_in_sample}/5)")

    print(f"\nALL {passed} EXPANSION SELF-TESTS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
