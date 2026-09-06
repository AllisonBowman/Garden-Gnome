"""List every binomial the verified tranche already covers, or check candidates.

    python scripts/catalog/covered.py                      # print all covered names (given + accepted)
    python scripts/catalog/covered.py "Dypsis lutescens" "Rhapis excelsa" ...   # check candidates

Run from garden-gnome/ with the project venv. Exit 1 on any DUP.

Matching is exact on the normalized binomial (whitespace collapsed, '×' -> 'x',
case-folded, cultivar/varietal tail stripped for the genus+species key), against
scientific_name_given AND scientific_name_accepted. This is what a substring
grep across the whole JSON cannot do: it ignores incidental mentions inside
citation quotes (the Nandina / Cat Palm false positives) and it catches a
species filed under a reclassified name (Areca Palm: given Dypsis lutescens,
accepted Chrysalidocarpus lutescens; Alocasia 'Polly').
"""
import glob
import json
import re
import sys
from pathlib import Path

# garden-gnome/app/data/verified, located from this file so the script runs from any cwd.
VERIFIED = Path(__file__).resolve().parents[2] / "app" / "data" / "verified"


def norm(name: str) -> str:
    n = re.sub(r"\s+", " ", (name or "").replace("×", "x")).strip().lower()
    return n


def key(name: str) -> str:
    # genus + species only: "alocasia x amazonica 'polly'" -> "alocasia x amazonica"
    n = norm(name)
    n = re.sub(r"\s+'.*$", "", n)                 # cultivar tail
    n = re.sub(r"\s+(var|subsp|ssp|f)\.\s+\S+$", "", n)  # infraspecific tail
    return n


def covered() -> dict[str, list[tuple[str, str]]]:
    out: dict[str, list[tuple[str, str]]] = {}
    for path in sorted(glob.glob(str(VERIFIED / "b*.json"))):
        batch = Path(path).name
        for r in json.loads(Path(path).read_text())["records"]:
            for field in ("scientific_name_given", "scientific_name_accepted"):
                if r.get(field):
                    out.setdefault(key(r[field]), []).append((batch, r.get("common_name") or "?"))
    return out


if __name__ == "__main__":
    cov = covered()
    if len(sys.argv) == 1:
        for k in sorted(cov):
            print(k)
        print(f"\n{len(cov)} distinct binomials")
    else:
        clean = True
        for cand in sys.argv[1:]:
            k = key(cand)
            hits = cov.get(k)
            # also flag a genus-level near miss so a synonym under another
            # species epithet at least gets looked at
            genus = k.split()[0]
            same_genus = sorted({b for kk, v in cov.items() if kk.split()[0] == genus for b, _ in v})
            if hits:
                clean = False
                print(f"DUP   {cand} -> {sorted(set(hits))}")
            else:
                note = f"  (genus already present in {same_genus})" if same_genus else ""
                print(f"clean {cand}{note}")
        sys.exit(0 if clean else 1)
