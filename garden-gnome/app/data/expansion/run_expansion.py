"""Catalog expansion orchestrator.

Tiered sourcing per target species:
  1. Perenual API (Premium) — mapped into our schema, tagged source=perenual
  2. /species/generate LLM draft fallback — tagged source=llm_generated
Then a mandatory validation pass on every record; clean records import with
review_status=approved, flagged ones go to output/review_queue.json instead
of the database. Finally a weighted 5-10% sample lands in
output/review_sample.json for manual cross-checking (see apply_review.py).

Usage (from garden-gnome/):
  python -m app.data.expansion.run_expansion --targets app/data/expansion/target_species.txt
  python -m app.data.expansion.run_expansion --mock-dir app/data/expansion/fixtures --dry-run
Options: --limit N, --dry-run, --skip-llm, --sample-fraction 0.075
"""
import argparse
import json
import sys
from pathlib import Path

from sqlmodel import Session, select

from app.db.database import engine, init_db, migrate_db
from app.models.models import CareSchedule, Species, SpeciesTrait
from app.data.expansion.perenual import PerenualClient, map_perenual_record, _norm
from app.data.expansion.validate import find_near_duplicates, validate_record
from app.data.expansion.sample import to_review_entry, weighted_sample

OUT_DIR = Path(__file__).parent / "output"


def load_targets(path: Path) -> list[dict]:
    """Target file: one species per line. Either a bare name, or
    'perenual_id<TAB>common_name<TAB>scientific_name' (from fetch_targets.py).
    Lines starting with # are comments."""
    targets = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) >= 3 and parts[0].isdigit():
            targets.append({"perenual_id": int(parts[0]), "common": parts[1], "scientific": parts[2]})
        else:
            targets.append({"perenual_id": None, "common": line, "scientific": ""})
    return targets


def pick_match(target: dict, results: list[dict]) -> dict | None:
    """Choose the best Perenual search hit for a target name."""
    want = _norm(target["scientific"] or target["common"])
    for row in results:
        sci = row.get("scientific_name")
        sci_list = sci if isinstance(sci, list) else [sci or ""]
        if _norm(row.get("common_name", "")) == want or any(_norm(s) == want for s in sci_list):
            return row
    return results[0] if results else None


def llm_fallback(name: str) -> tuple[dict | None, str | None]:
    """Draft a record via the existing LLM generation service."""
    from app.services.catalog import BACKEND, generate_species_profile
    if BACKEND == "stub":
        return None, "LLM backend not configured (ADVISOR_BACKEND=stub)"
    try:
        draft = generate_species_profile(name)
    except RuntimeError as exc:
        return None, str(exc)
    draft.update({
        "source": "llm_generated",
        "source_ref": "",
        "review_status": "approved",  # validation may downgrade
        "review_note": "",
    })
    draft.setdefault("schedules", [])
    draft.setdefault("traits", [])
    return draft, None


def import_record(rec: dict, session: Session) -> int:
    species_fields = {k: v for k, v in rec.items() if k not in ("schedules", "traits")}
    species = Species(**species_fields)
    session.add(species)
    session.flush()
    for s in rec.get("schedules", []):
        session.add(CareSchedule(species_id=species.id, **s))
    for t in rec.get("traits", []):
        session.add(SpeciesTrait(species_id=species.id, **t))
    return species.id


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--targets", default=str(Path(__file__).parent / "target_species.txt"))
    ap.add_argument("--limit", type=int, default=0, help="process at most N targets")
    ap.add_argument("--dry-run", action="store_true", help="no database writes")
    ap.add_argument("--mock-dir", default=None, help="read Perenual fixtures from dir")
    ap.add_argument("--skip-llm", action="store_true", help="skip the LLM fallback tier")
    ap.add_argument("--sample-fraction", type=float, default=0.075)
    args = ap.parse_args()

    targets_path = Path(args.targets)
    if not targets_path.exists():
        print(f"Target list not found: {targets_path}\n"
              "Generate one with: python -m app.data.expansion.fetch_targets --from-perenual",
              file=sys.stderr)
        return 2

    targets = load_targets(targets_path)
    if args.limit:
        targets = targets[: args.limit]

    client = PerenualClient(mock_dir=args.mock_dir)
    init_db()
    migrate_db()

    # Resume support: every mapped record is checkpointed to a JSONL file the
    # moment it's built, so a crash (rate-limit wall, network, Ctrl-C) never
    # loses progress — rerunning picks up where the last run stopped.
    OUT_DIR.mkdir(exist_ok=True)
    checkpoint = OUT_DIR / "mapped_records.jsonl"
    mapped: list[dict] = []
    done_refs: set[str] = set()
    done_sci: set[str] = set()
    resumed_warnings: dict[str, list[str]] = {}
    if checkpoint.exists():
        for line in checkpoint.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                # Mapper warnings ride along in the checkpoint so a resumed
                # record still routes to review
                warns = rec.pop("_warnings", [])
                if warns:
                    resumed_warnings[rec.get("scientific_name", "")] = warns
                mapped.append(rec)
                done_refs.add(rec.get("source_ref", ""))
                done_sci.add(_norm(rec.get("scientific_name", "")))
        if mapped:
            print(f"  resuming: {len(mapped)} records from previous checkpoint")

    with Session(engine) as session:
        existing = session.exec(select(Species.common_name, Species.scientific_name)).all()
        existing_sci = {_norm(s) for _, s in existing}

        warnings_by_sci: dict[str, list[str]] = dict(resumed_warnings)
        misses: list[str] = []
        llm_failures: list[dict] = []
        fetch_failures: list[dict] = []
        skipped_existing = 0

        # Circuit breaker: Perenual's care-guide endpoint has an undocumented
        # cap far below the main 10k/day quota. Once it starts failing it
        # fails for hours, and each attempt burns ~6 min of retry backoff —
        # so after a few consecutive failures, stop asking for the rest of
        # the run. Records fall back to details-based notes; the guide text
        # can be backfilled later in quota-friendly drips.
        guide_fail_streak = 0
        guides_disabled = False

        with checkpoint.open("a", encoding="utf-8") as ckpt:
            for i, target in enumerate(targets, 1):
                label = target["scientific"] or target["common"]
                if _norm(target["scientific"]) in existing_sci:
                    skipped_existing += 1
                    continue
                if (target["perenual_id"] and str(target["perenual_id"]) in done_refs) \
                        or _norm(target["scientific"]) in done_sci:
                    continue  # already mapped in a previous (crashed) run

                # A single bad target/endpoint must not kill a multi-hour run
                try:
                    # ── Tier 1: Perenual ─────────────────────────────────
                    details = None
                    if target["perenual_id"]:
                        details = client.details(target["perenual_id"])
                    else:
                        hit = pick_match(target, client.search(target["common"]))
                        if hit:
                            details = client.details(hit["id"])
                    if details:
                        sci = details.get("scientific_name")
                        sci = sci[0] if isinstance(sci, list) and sci else (sci or "")
                        sections = []
                        if not guides_disabled:
                            try:
                                sections = client.care_guide_sections(
                                    details["id"], expect_scientific=sci)
                                guide_fail_streak = 0
                            except Exception:
                                guide_fail_streak += 1
                                if guide_fail_streak >= 5:
                                    guides_disabled = True
                                    print("  !! care-guide endpoint failing repeatedly "
                                          "— circuit breaker OPEN, continuing on "
                                          "species details only")
                        rec, warns = map_perenual_record(details, sections)
                        if _norm(rec["scientific_name"]) in existing_sci \
                                or _norm(rec["scientific_name"]) in done_sci:
                            skipped_existing += 1
                            continue
                        mapped.append(rec)
                        done_sci.add(_norm(rec["scientific_name"]))
                        ckpt.write(json.dumps(
                            {**rec, "_warnings": warns}, ensure_ascii=False) + "\n")
                        ckpt.flush()
                        if warns:
                            warnings_by_sci[rec["scientific_name"]] = warns
                    else:
                        # ── Tier 2: LLM draft ───────────────────────────
                        misses.append(label)
                        if not args.skip_llm:
                            draft, err = llm_fallback(label)
                            if draft:
                                mapped.append(draft)
                                ckpt.write(json.dumps(draft, ensure_ascii=False) + "\n")
                                ckpt.flush()
                            else:
                                llm_failures.append({"name": label, "error": err})
                except Exception as exc:  # noqa: BLE001 — log and move on
                    fetch_failures.append({"name": label, "error": str(exc)})

                if i % 50 == 0:
                    print(f"  ...{i}/{len(targets)} targets processed "
                          f"({len(mapped)} mapped, {len(misses)} misses, "
                          f"{len(fetch_failures)} fetch failures)")

        # ── Tier 3: validation on every record, regardless of source ─────
        dup_flags = find_near_duplicates(mapped, list(existing))
        clean, flagged = [], []
        for rec in mapped:
            issues = validate_record(rec)
            issues += dup_flags.get(rec.get("scientific_name", ""), [])
            issues += warnings_by_sci.get(rec.get("scientific_name", ""), [])
            if issues:
                rec["review_status"] = "needs_review"
                flagged.append({"record": rec, "issues": issues})
            else:
                clean.append(rec)

        # ── Import clean records ──────────────────────────────────────────
        imported_ids: list[int] = []
        if not args.dry_run:
            for rec in clean:
                if _norm(rec["scientific_name"]) in existing_sci:
                    continue  # stale checkpoint entry already imported earlier
                imported_ids.append(import_record(rec, session))
            session.commit()

    # ── Outputs ───────────────────────────────────────────────────────────
    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / "review_queue.json").write_text(
        json.dumps(flagged, indent=2, ensure_ascii=False), encoding="utf-8")
    sample = [to_review_entry(r) for r in weighted_sample(clean, args.sample_fraction)]
    (OUT_DIR / "review_sample.json").write_text(
        json.dumps(sample, indent=2, ensure_ascii=False), encoding="utf-8")
    report = {
        "targets": len(targets),
        "skipped_already_in_catalog": skipped_existing,
        "mapped_from_perenual": sum(1 for r in mapped if r["source"] == "perenual"),
        "llm_generated": sum(1 for r in mapped if r["source"] == "llm_generated"),
        "perenual_misses": misses,
        "llm_failures": llm_failures,
        "fetch_failures": fetch_failures,
        "imported": len(imported_ids) if not args.dry_run else 0,
        "clean_but_not_imported_dry_run": len(clean) if args.dry_run else 0,
        "flagged_for_review": len(flagged),
        "manual_review_sample": len(sample),
    }
    (OUT_DIR / "expansion_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps({k: v for k, v in report.items()
                      if k not in ("perenual_misses", "llm_failures", "fetch_failures")},
                     indent=2))
    if fetch_failures:
        print(f"NOTE: {len(fetch_failures)} targets failed to fetch (see "
              "expansion_report.json) — rerun the same command to retry just those.")
    print(f"\nOutputs in {OUT_DIR}:")
    print("  review_queue.json   -- flagged records + issues (NOT imported)")
    print("  review_sample.json  -- weighted sample for manual citation pass")
    print("  expansion_report.json -- full run report")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
