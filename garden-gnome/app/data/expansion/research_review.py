"""Research needs_review species against horticultural sources on the web.

Of ~1940 catalog species, ~1688 are `needs_review` — imported from Perenual
with known gaps ("no soil data — defaulted") that no human has checked. Doing
those lookups by hand is the bottleneck; this does the looking-up.

**The machine proposes, a human disposes.** This writes a review file in
exactly the shape `apply_review.py` already consumes, with the `review` block
pre-filled and a citation URL for each claim. A human skims and corrects it,
then runs apply_review.py — which is the only thing that touches the database.
Nothing here writes to the catalog, and no verdict here marks a species
verified on its own.

Sources: the model is pointed at the same authorities the manual workflow uses
(NC State Extension Plant Toolbox, Missouri Botanical Garden Plant Finder, RHS,
university extension services), because those are what a reviewer would cite.

Usage (from garden-gnome/):

    # try ten records first and read the output before spending more
    python -m app.data.expansion.research_review --limit 10

    # offline, no API key, no cost — exercises parsing and file shape
    python -m app.data.expansion.research_review --mock-dir fixtures/research

    # the whole backlog, once you trust it
    python -m app.data.expansion.research_review --all

Then review output/researched_review.json by hand and apply:

    python -m app.data.expansion.apply_review output/researched_review.json

Costs real money per record (web search plus model tokens), so --limit
defaults to a small number: running the full backlog has to be deliberate.
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

from sqlmodel import Session, select

from app.db.database import engine
from app.models.models import Species

OUT_DIR = Path(__file__).parent / "output"
CHECKPOINT = OUT_DIR / "researched_records.jsonl"
REVIEW_FILE = OUT_DIR / "researched_review.json"

DEFAULT_MODEL = "claude-opus-4-8"
DEFAULT_LIMIT = 10
MAX_SEARCHES_PER_RECORD = 4
# Server-tool turns can stop with pause_turn and need re-sending to continue.
MAX_RESUMES = 3

# Fields apply_review.py will write back. Corrections outside this set are
# ignored there, so don't invite them.
CORRECTABLE = [
    "common_name", "scientific_name", "light_need", "humidity_pct_min",
    "humidity_pct_max", "temp_f_min", "temp_f_max", "soil_type",
    "toxic_to_pets", "care_notes",
]

SYSTEM_INSTRUCTION = (
    "You are a horticultural fact-checker verifying entries in a houseplant "
    "care database. For each record you are given, search authoritative "
    "sources and decide whether the care data is correct.\n\n"
    "Prefer, in order: NC State Extension Plant Toolbox "
    "(plants.ces.ncsu.edu), Missouri Botanical Garden Plant Finder "
    "(missouribotanicalgarden.org), the RHS (rhs.org.uk), and university "
    "extension services. Treat retail plant-shop pages and content farms as "
    "unreliable and do not cite them.\n\n"
    "Rules that matter more than being helpful:\n"
    "- Cite a specific page you actually consulted, not a search page or a "
    "site's front page. If you could not find the species on a trustworthy "
    "source, the verdict is 'uncertain'. Never invent a citation.\n"
    "- 'uncertain' is a perfectly good answer and is expected to be common. A "
    "human reads every verdict; a wrong 'confirmed' wastes their trust, while "
    "an honest 'uncertain' costs them one lookup.\n"
    "- Only propose a correction when the source explicitly contradicts the "
    "record. Do not rewrite wording you merely dislike.\n"
    "- Toxicity claims must come from a source that states it. This field "
    "affects whether someone lets a pet near the plant, so leave it alone "
    "rather than guess.\n"
    "- Judge care values for an INDOOR container plant, not landscape use.\n\n"
    "Respond with a single JSON object and nothing else:\n"
    '{"verdict": "confirmed" | "corrected" | "rejected" | "uncertain", '
    '"citation_source": "<publication name>", "citation_url": "<exact page URL>", '
    '"corrections": {"<field>": <value>}, "notes": "<one or two sentences>"}\n\n'
    "verdict meanings: confirmed = record matches the source; corrected = "
    "source disagrees, corrections hold the fixed values; rejected = this is "
    "not a real/distinct species or is unsuitable as a houseplant entry; "
    "uncertain = you could not verify it. Correctable fields: "
    + ", ".join(CORRECTABLE) + "."
)


def build_prompt(sp: Species) -> str:
    record = {f: getattr(sp, f, None) for f in CORRECTABLE}
    return (
        "Verify this houseplant care record:\n\n"
        + json.dumps(record, indent=2, ensure_ascii=False)
        + f"\n\nExisting reviewer note: {sp.review_note or '(none)'}"
    )


def extract_json(text: str) -> dict | None:
    """Pull the JSON object out of a model reply.

    Same defensive approach as catalog.py's _extract_json: the reply may carry
    prose or fences around the object even when asked for bare JSON."""
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    candidate = fenced.group(1) if fenced else None
    if candidate is None:
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end <= start:
            return None
        candidate = text[start:end + 1]
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def sanitize(review: dict) -> dict:
    """Normalize a model verdict into apply_review.py's contract.

    Anything that would let an unverified claim through gets downgraded to
    'uncertain', which apply_review skips."""
    verdict = str(review.get("verdict", "")).strip().lower()
    if verdict not in {"confirmed", "corrected", "rejected", "uncertain"}:
        verdict = "uncertain"

    url = str(review.get("citation_url", "")).strip()
    source = str(review.get("citation_source", "")).strip()
    # A verdict without a real citation is an opinion, not a review.
    if verdict in {"confirmed", "corrected"} and not url.startswith("http"):
        verdict = "uncertain"

    corrections = review.get("corrections")
    corrections = corrections if isinstance(corrections, dict) else {}
    corrections = {k: v for k, v in corrections.items() if k in CORRECTABLE and v is not None}
    if verdict == "corrected" and not corrections:
        verdict = "uncertain"  # claims a fix but supplies none

    return {
        "verdict": verdict,
        "citation_source": source,
        "citation_url": url,
        "corrections": corrections,
        "notes": str(review.get("notes", "")).strip(),
        # Marks the entry as machine-drafted so a reviewer knows what they're
        # reading, and so it is never mistaken for a human sign-off.
        "researched_by": "web-research pipeline (unverified — needs human review)",
    }


def research_one(client, model: str, sp: Species) -> dict:
    """One record, one verdict. Returns a sanitized review block."""
    import anthropic

    messages = [{"role": "user", "content": build_prompt(sp)}]
    text = ""
    for _ in range(MAX_RESUMES):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=4096,
                system=SYSTEM_INSTRUCTION,
                tools=[{
                    "type": "web_search_20260209",
                    "name": "web_search",
                    "max_uses": MAX_SEARCHES_PER_RECORD,
                }],
                messages=messages,
            )
        except anthropic.APIError as exc:
            return sanitize({"notes": f"API error: {exc}"})

        if response.stop_reason == "refusal":
            return sanitize({"notes": "declined by safety classifiers"})

        text = "".join(b.text for b in response.content if b.type == "text").strip()
        # A server-tool turn can pause mid-search; re-send to continue.
        if response.stop_reason != "pause_turn":
            break
        messages.append({"role": "assistant", "content": response.content})

    parsed = extract_json(text)
    if parsed is None:
        return sanitize({"notes": "could not parse a verdict from the reply"})
    return sanitize(parsed)


def load_checkpoint() -> dict[str, dict]:
    """Resume support: scientific_name -> entry already researched."""
    done: dict[str, dict] = {}
    if CHECKPOINT.exists():
        for line in CHECKPOINT.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                done[entry["record"]["scientific_name"]] = entry
            except (json.JSONDecodeError, KeyError):
                continue
    return done


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=DEFAULT_LIMIT,
                    help=f"research at most N records (default {DEFAULT_LIMIT})")
    ap.add_argument("--all", action="store_true",
                    help="research the entire needs_review backlog (costs real money)")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--mock-dir", default=None,
                    help="read canned replies from a fixture dir instead of the API")
    ap.add_argument("--status", default="needs_review",
                    help="which review_status to work through")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    done = load_checkpoint()

    with Session(engine) as session:
        pending = session.exec(
            select(Species).where(Species.review_status == args.status)
        ).all()
        # Detach the fields we need; the session closes before the slow part.
        targets = [sp for sp in pending if sp.scientific_name not in done]
        records = [{f: getattr(sp, f, None) for f in CORRECTABLE} | {
            "review_status": sp.review_status, "review_note": sp.review_note or "",
        } for sp in targets]
        species_objs = list(targets)

    total_pending = len(species_objs)
    if not args.all:
        species_objs = species_objs[:max(0, args.limit)]
        records = records[:max(0, args.limit)]

    print(f"  {args.status}: {total_pending} unresearched, {len(done)} already checkpointed")
    print(f"  researching {len(species_objs)} this run (model: {args.model})")
    if not species_objs:
        print("  nothing to do")

    client = None
    mock_dir = Path(args.mock_dir) if args.mock_dir else None
    if species_objs and mock_dir is None:
        if not os.getenv("ANTHROPIC_API_KEY"):
            print("  ! ANTHROPIC_API_KEY is not set — use --mock-dir to run offline")
            return 2
        import anthropic
        client = anthropic.Anthropic()

    with CHECKPOINT.open("a", encoding="utf-8") as ckpt:
        for sp, record in zip(species_objs, records):
            if mock_dir is not None:
                fixture = mock_dir / f"{sp.scientific_name.replace(' ', '_')}.json"
                raw = json.loads(fixture.read_text(encoding="utf-8")) if fixture.exists() else {}
                review = sanitize(raw)
            else:
                review = research_one(client, args.model, sp)

            entry = {"record": record, "review": review}
            done[sp.scientific_name] = entry
            ckpt.write(json.dumps(entry, ensure_ascii=False) + "\n")
            ckpt.flush()
            print(f"  {review['verdict']:<10} {sp.scientific_name}")

    entries = list(done.values())
    REVIEW_FILE.write_text(
        json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    tally: dict[str, int] = {}
    for e in entries:
        v = e["review"]["verdict"]
        tally[v] = tally.get(v, 0) + 1
    print(f"\n  wrote {REVIEW_FILE} ({len(entries)} entries)")
    print(f"  verdicts: {tally}")
    print("\n  Next: read the file, correct what the research got wrong, then")
    print(f"  python -m app.data.expansion.apply_review {REVIEW_FILE}")
    print("  Nothing has been written to the catalog by this script.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
