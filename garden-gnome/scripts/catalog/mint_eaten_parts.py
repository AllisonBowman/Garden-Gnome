#!/usr/bin/env python
"""Mint `eaten_parts` for every verified record that says the plant is eaten.

ADR 0011 makes eating a cited description: the parts a source names as eaten,
from a fixed vocabulary (leaves, fruit, seeds, roots, flowers, stems). The
tranche already quotes those parts in the passages behind `is_edible`, so this
script reads each such passage and proposes the parts it names as eaten. It
adds nothing a passage does not say and fetches no page.

How a passage is read. It is split into clauses, on sentence marks and on the
turns a source uses to change subject ("but", "however", "while"). A clause
that speaks of eating and does not speak of harm contributes the parts it
names. A clause that speaks of harm contributes only a part it excepts
("all parts are toxic except the ripe fruit"). Everything else contributes
nothing. A passage that names no part leaves the record without the field,
which the app reads as "no source names a part", never as "nothing is eaten".

The result is an audit file, one entry per record read, so that what was
proposed, from which words, is on the record before anything is written.
Verifiers read the audit (see docs/2026-11-01-eaten-parts-audit.md); only an
entry they passed is written, and `--write` takes their verdicts file.

Usage (from garden-gnome/):
  python scripts/catalog/mint_eaten_parts.py                 # audit only
  python scripts/catalog/mint_eaten_parts.py --write VERDICTS.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve()
VERIFIED = HERE.parents[2] / "app" / "data" / "verified"
AUDIT = HERE.parent / "pipeline" / "eaten-parts-mint.json"

VOCABULARY = ("leaves", "fruit", "seeds", "roots", "flowers", "stems")

#: The words of a passage that name each part. Tubers, bulbs, corms and
#: rhizomes are roots; nuts, grain, beans and peas are seeds; pods and berries
#: are fruit. "Buds" count only as flower buds.
#: A crop named by its own word names its eaten part: "bananas are eaten"
#: says the fruit is, "lettuce is eaten" the leaves. Only words with one
#: reading are here; "broccoli" (stems and flowers) and "sprouts" are not.
PART_RES = {
    "leaves": re.compile(
        r"\b(?:leaf|leaves|leafy|greens|foliage|needles?|fiddleheads?"
        r"|lettuce|cabbages?|kale|spinach|chard|collards?)\b", re.I),
    "fruit": re.compile(
        r"\b(?:fruits?|berr(?:y|ies)|pods?|drupes?|hips?|bananas?|grapes?|melons?"
        r"|maypops?|apples?|pears?|plums?|cherr(?:y|ies)|peach(?:es)?|figs?|lemons?"
        r"|limes?|oranges?|tomato(?:es)?|peppers?|cucumbers?|persimmons?"
        r"|mulberr(?:y|ies)|squash(?:es)?|gourds?)\b", re.I),
    "seeds": re.compile(
        r"\b(?:seeds?|nuts?|nutmeats?|grains?|kernels?|beans?|peas?|acorns?|corn)\b", re.I),
    "roots": re.compile(
        r"\b(?:roots?|tubers?|bulbs?|corms?|rhizomes?|taproots?|carrots?|beets?"
        r"|radish(?:es)?|turnips?|potato(?:es)?|yams?|onions?|garlic|ginger)\b", re.I),
    "flowers": re.compile(
        r"\b(?:flowers?|petals?|blossoms?|florets?|flower\s+buds?|cauliflower)\b", re.I),
    "stems": re.compile(
        r"\b(?:stems?|stalks?|shoots?|spears?|petioles?|canes?|asparagus|celery"
        r"|rhubarb|leeks?)\b", re.I),
}

#: A clause is about eating when it holds one of these.
EATING_RE = re.compile(
    r"\b(?:edible|eaten|eat|eating|eats|consum\w*|cooked|cooking|raw|flavou?r\w*"
    r"|garnish\w*|teas?|salads?|snacks?|cuisines?|jams?|jell\w*|pies?|syrups?"
    r"|steamed|boiled|roasted|fried|baked|pickled|dried|infusions?|flour"
    r"|used (?:as|for|in)|food|foods|vegetables?|culinary|seasonings?|spices?"
    r"|harvested|edibility|dishes|soups?|stews?|wines?|juices?|sweetener|herb"
    r"|nutritious|grown for|preserves?|cider|delicious|tasty|sweet|bitter|tart"
    r"|flavou?r|condiment)\b",
    re.I)

#: A clause is about harm or refusal when it holds one of these; its parts are
#: not eaten unless the clause excepts them.
HARM_RE = re.compile(
    r"\b(?:not edible|inedible|non-?edible|not (?:be )?eaten|poison\w*|toxi\w*"
    r"|harmful|should not|do not|don't|never|avoid\w*|unsafe|dangerous|irritant"
    r"|caution|warning|allerg\w*|sickness|illness|fatal|deadly)\b",
    re.I)

#: Within a harm clause, what is excepted is eaten: "all parts are poisonous
#: except the ripe fruit".
EXCEPT_RE = re.compile(r"\bexcept(?:ing| for)?\b(.{0,60})", re.I)

CLAUSE_SPLIT_RE = re.compile(
    r"[.;:!?]|\n|\s+(?:but|however|whereas|while|although|though)\s+|\s--\s|\s-\s",
    re.I)


#: Words that name a part without saying it is eaten: a comparison ("tastes
#: like cucumber"), a part taken off before eating ("stems removed"), a time
#: ("until they flower"), another dish ("fruit salad"). Blanked before the
#: parts are read, so they cannot be read as a part of this plant.
NOT_A_PART_RE = re.compile(
    r"(?:tastes?|smells?|flavou?r(?:ed)?|looks?)\s+(?:like|similar to|of)\s+[^,.;]+"
    r"|\blike\s+(?:a|an|the)?\s*\w+(?:\s+or\s+\w+)?"
    r"|\(\s*[^)]*(?:removed|discarded|peeled)[^)]*\)"
    r"|\buntil\s+(?:they|it)\s+(?:flower|bolt|seed)\w*"
    r"|\bfruit\s+salads?\b|\bsalads?\b",
    re.I)


def clauses(text: str) -> list[str]:
    text = NOT_A_PART_RE.sub(" ", text or "")
    return [c.strip() for c in CLAUSE_SPLIT_RE.split(text) if c and c.strip()]


def parts_in(text: str) -> list[str]:
    """The vocabulary parts named in `text`, in order of first appearance."""
    found: list[tuple[int, str]] = []
    for part, pattern in PART_RES.items():
        m = pattern.search(text)
        if m:
            found.append((m.start(), part))
    return [p for _, p in sorted(found)]


def read_passage(quote: str) -> dict:
    """What a passage says is eaten, with the clauses that said it."""
    eating_clauses: list[str] = []
    harm_clauses: list[str] = []
    ordered: list[tuple[int, str]] = []
    offset = 0
    blanked = NOT_A_PART_RE.sub(" ", quote or "")
    for clause in clauses(quote):
        at = blanked.find(clause, offset)
        offset = at + len(clause) if at >= 0 else offset
        if HARM_RE.search(clause):
            harm_clauses.append(clause)
            m = EXCEPT_RE.search(clause)
            if m:
                for part in parts_in(m.group(1)):
                    ordered.append((at + m.start(), part))
            continue
        if EATING_RE.search(clause):
            eating_clauses.append(clause)
            for part in parts_in(clause):
                ordered.append((at, part))
    # NC State's Edibility field is sometimes a bare list of the parts eaten
    # ("Seeds, leaves"), with no verb for the cue to find. A short passage
    # that names parts and nothing else, under a claim that the plant is
    # eaten, is that list.
    if not ordered and not harm_clauses and len((quote or "").split()) <= 6:
        for part in parts_in(quote or ""):
            ordered.append((0, part))
        if ordered:
            eating_clauses.append(quote.strip())
    parts: list[str] = []
    for _, part in sorted(ordered):
        if part not in parts:
            parts.append(part)
    return {"parts": parts, "eating_clauses": eating_clauses, "harm_clauses": harm_clauses}


def edibility_citations(record: dict) -> list[dict]:
    return [c for c in record.get("citations") or []
            if re.search(r"\bis_edible\b", c.get("claim") or "")
            and (c.get("quote") or "").strip() and (c.get("url") or "").strip()]


def name_of(record: dict) -> str:
    return record.get("scientific_name_accepted") or record.get("scientific_name_given") or "?"


def audit_records() -> list[dict]:
    """One entry per record recorded as eaten, in tranche order."""
    entries: list[dict] = []
    for path in sorted(VERIFIED.glob("b*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for record in data["records"]:
            if record.get("is_edible") is not True:
                continue
            entry = {"batch": path.name, "scientific_name": name_of(record),
                     "common_name": record.get("common_name"),
                     "already": record.get("eaten_parts"), "citations": []}
            best = None
            for c in edibility_citations(record):
                read = read_passage(c["quote"])
                entry["citations"].append({
                    "source": c.get("source", ""), "url": c["url"], "quote": c["quote"],
                    **read})
                if read["parts"] and (best is None or len(read["parts"]) > len(best["parts"])):
                    best = {"url": c["url"], "source": c.get("source", ""),
                            "quote": c["quote"], "parts": read["parts"]}
            entry["proposed"] = best
            entry["status"] = ("no edibility citation" if not entry["citations"]
                               else "no part named" if best is None else "proposed")
            entries.append(entry)
    return entries


def _claim_text(parts: list[str]) -> str:
    return (f"eaten_parts {', '.join(parts)} (the parts this passage names as eaten; "
            f"minted {date.today().isoformat()} by scripts/catalog/mint_eaten_parts.py "
            f"from the citation behind is_edible, and verified; see "
            f"docs/2026-11-01-eaten-parts-audit.md)")


def write_verified(entries: list[dict], verdicts: dict[str, dict]) -> dict:
    """Write `eaten_parts` and its citation onto every record whose verdict
    passed, keeping each batch file's formatting. Returns counts."""
    counts = {"written": 0, "refused": 0, "unverified": 0, "unchanged": 0}
    by_batch: dict[str, list[dict]] = {}
    for e in entries:
        if e["status"] != "proposed":
            continue
        by_batch.setdefault(e["batch"], []).append(e)
    for batch, todo in by_batch.items():
        path = VERIFIED / batch
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        changed = False
        for record in data["records"]:
            entry = next((e for e in todo if name_of(record) == e["scientific_name"]), None)
            if entry is None:
                continue
            verdict = verdicts.get(entry["scientific_name"])
            if verdict is None:
                counts["unverified"] += 1
                continue
            parts = verdict.get("parts") or []
            if not verdict.get("pass") or not parts:
                counts["refused"] += 1
                continue
            if record.get("eaten_parts") == parts:
                counts["unchanged"] += 1
                continue
            record["eaten_parts"] = parts
            cites = record.setdefault("citations", [])
            cites[:] = [c for c in cites if not (c.get("claim") or "").startswith("eaten_parts ")]
            cites.append({"claim": _claim_text(parts), "source": entry["proposed"]["source"],
                          "url": entry["proposed"]["url"], "quote": entry["proposed"]["quote"]})
            counts["written"] += 1
            changed = True
        if changed:
            path.write_text(_dump_like(raw, data), encoding="utf-8")
    return counts


def _dump_like(raw: str, data: dict) -> str:
    """Serialise the way the file was written: indent and escaping detected
    from the original, trailing newline kept."""
    indent = 2
    m = re.search(r"\n( +)\"", raw)
    if m:
        indent = len(m.group(1))
    ascii_only = "\\u" in raw and not any(ord(ch) > 127 for ch in raw)
    out = json.dumps(data, indent=indent, ensure_ascii=ascii_only)
    return out + ("\n" if raw.endswith("\n") else "")


def roundtrip_identical() -> list[str]:
    """Batch files that `_dump_like` does not reproduce byte for byte. Empty
    means a write touches only the records it changes."""
    bad = []
    for path in sorted(VERIFIED.glob("b*.json")):
        raw = path.read_text(encoding="utf-8")
        if _dump_like(raw, json.loads(raw)) != raw:
            bad.append(path.name)
    return bad


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", metavar="VERDICTS",
                        help="JSON of {scientific_name: {pass, parts}} from the verifiers; "
                             "writes the passed entries into the batch files")
    args = parser.parse_args()
    entries = audit_records()
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(entries, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    statuses: dict[str, int] = {}
    for e in entries:
        statuses[e["status"]] = statuses.get(e["status"], 0) + 1
    parts_count: dict[str, int] = {}
    for e in entries:
        for p in (e["proposed"] or {}).get("parts", []):
            parts_count[p] = parts_count.get(p, 0) + 1
    print(f"records recorded as eaten: {len(entries)}")
    print(f"status: {statuses}")
    print(f"parts proposed: {parts_count}")
    print(f"audit written: {AUDIT}")
    bad = roundtrip_identical()
    print(f"batch files that do not round-trip byte for byte: {len(bad)} {bad[:5]}")
    if args.write:
        if bad:
            sys.exit("refusing to write: a batch file would be reformatted")
        verdicts = json.loads(Path(args.write).read_text(encoding="utf-8"))
        print("written:", write_verified(entries, verdicts))


if __name__ == "__main__":
    main()
