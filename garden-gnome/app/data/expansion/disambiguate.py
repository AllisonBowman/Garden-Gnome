"""Give cultivar rows a name that tells them apart.

The Perenual import brought in cultivars, but it kept the *species-level*
common name and put the cultivar only in the scientific name:

    id  76  Tomatoes  Solanum lycopersicum                        curated
    id 642  Tomato    Lycopersicon esculentum 'Sungold'           perenual
    id 951  Tomato    Lycopersicon esculentum 'Big Beef'          perenual
    id 952  Tomato    Lycopersicon esculentum 'Chef's Choice ...  perenual

Five rows reading "Tomato" in a picker are five rows a person cannot choose
between. It is not a small problem: 290 common names are shared across 1,007
of the 1,940 rows, with 35 rows called "Butterfly Bush" and 15 called
"Rosemary".

It also quietly breaks identification, which is the part that matters most.
Matching "rosemary" against fifteen rows all named exactly "Rosemary" produces
a fifteen-way tie at score 1.0, and the winner is then decided by whatever the
sort happens to do — so the curated, reviewed row with real care data has no
particular advantage over an unreviewed cultivar import.

Promoting the cultivar into the display name fixes both at once. "Rosemary
'Tuscan Blue'" is choosable in a list, and it no longer ties with a plain
"rosemary" query, so the curated row wins on its own merits without the
matcher needing to know anything about review status.

Nothing is deleted and no row is merged: a cultivar is a real thing somebody
may actually be growing. This only changes what a row is called.

Pure helpers here; the CLI at the bottom is the only part that touches a
database, and it defaults to reporting rather than writing.
"""
from __future__ import annotations

import re

# The cultivar epithet is conventionally single-quoted at the end of the name:
#   Lycopersicon esculentum 'Big Beef'
# Greedy, anchored at the end, so an apostrophe inside the epithet survives —
# "Chef's Choice Orange" must not be truncated to "Chef".
_CULTIVAR = re.compile(r"'(.+)'\s*$")


def cultivar_of(scientific_name: str) -> str | None:
    """The quoted cultivar epithet, or None when the name carries no cultivar."""
    m = _CULTIVAR.search((scientific_name or "").strip())
    if not m:
        return None
    epithet = m.group(1).strip()
    return epithet or None


def _already_names(common_name: str, epithet: str) -> bool:
    """True when the common name already identifies this cultivar, so renaming
    would only stutter ("Rosemary 'Tuscan Blue' 'Tuscan Blue'")."""
    return epithet.lower() in (common_name or "").lower()


def disambiguated_name(common_name: str, scientific_name: str) -> str | None:
    """The name this row should display, or None to leave it alone.

    Returns None for anything without a cultivar — a plain species keeps its
    plain name, so "Tree Tomato" (Cyphomandra betacea, a different plant that
    merely reads like a tomato) is never touched.
    """
    common = (common_name or "").strip()
    if not common:
        return None
    epithet = cultivar_of(scientific_name)
    if not epithet or _already_names(common, epithet):
        return None
    return f"{common} '{epithet}'"


def plan_renames(rows: list[tuple[int, str, str]]) -> list[tuple[int, str, str]]:
    """Work out the renames for `(id, common_name, scientific_name)` rows.

    Only rows whose common name is *shared* with another row are renamed. A
    cultivar that is already the only thing called what it is called reads
    better without the epithet bolted on, and leaving it alone keeps the diff
    to what actually needed fixing.

    Returns `(id, old_name, new_name)`, sorted by id.
    """
    counts: dict[str, int] = {}
    for _, common, _sci in rows:
        key = (common or "").strip().lower()
        counts[key] = counts.get(key, 0) + 1

    out: list[tuple[int, str, str]] = []
    for sid, common, sci in rows:
        if counts.get((common or "").strip().lower(), 0) < 2:
            continue
        new = disambiguated_name(common, sci)
        if new and new != common:
            out.append((sid, common, new))
    return sorted(out)


def _main() -> int:  # pragma: no cover - operational entry point
    import argparse
    import sqlite3

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", default="/data/garden_gnome.db")
    ap.add_argument("--apply", action="store_true",
                    help="write the renames; without this it only reports")
    ap.add_argument("--limit", type=int, default=20,
                    help="how many example renames to print")
    args = ap.parse_args()

    db = sqlite3.connect(args.db)
    cur = db.cursor()
    cur.execute("SELECT id, common_name, scientific_name FROM species")
    rows = cur.fetchall()
    renames = plan_renames(rows)

    print(f"{len(rows)} species; {len(renames)} would be renamed")
    for sid, old, new in renames[: args.limit]:
        print(f"  {sid:>5}  {old!r} -> {new!r}")
    if len(renames) > args.limit:
        print(f"  … and {len(renames) - args.limit} more")

    if not args.apply:
        print("\ndry run — nothing written. Re-run with --apply to commit.")
        return 0

    cur.executemany(
        "UPDATE species SET common_name = ? WHERE id = ?",
        [(new, sid) for sid, _old, new in renames],
    )
    db.commit()
    print(f"\napplied {len(renames)} renames")

    cur.execute(
        "SELECT COUNT(*) FROM (SELECT 1 FROM species GROUP BY lower(common_name) HAVING COUNT(*) > 1)"
    )
    print("common names still shared by more than one row:", cur.fetchone()[0])
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_main())
