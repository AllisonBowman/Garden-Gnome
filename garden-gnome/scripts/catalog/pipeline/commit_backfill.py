"""commit_backfill.py LABEL SUBJECT BODY_FILE FILE [FILE ...] -- verify and commit one size-backfill landing.

Run from garden-gnome/ with the project venv. FILE is each app/data/verified/b*.json the landing touched, plus any
pipeline result/summary files to commit with it. A backfill only ADDS fields to records already in the corpus, so
its claim delta is measured per touched batch file against that file's committed (HEAD) version -- never from the
whole working tree, which may hold other landings' uncommitted changes. The count test's LAST assertion is bumped
by that delta, the docs header's claim total follows it, and only the named files are staged.

Refuses to commit when verify_quotes reports a MISS on any citation whose claim names one of the six backfill
fields, or when the tranche invariants fail. A MISS on an older citation in a touched file is printed, not fatal:
it predates the landing.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from app.data.claims.tranche import claims_from_record  # noqa: E402

STEMS = ('is_edible', 'attracts_pollinators', 'climbs', 'mature_height_in', 'mature_spread_in')
TEST = 'tests/test_claim_ingest.py'
DOCS = '../docs/2026-09-02-catalog-truth-collection-run.md'


def claims(records):
    return sum(len(claims_from_record(r)[0]) for r in records)


def run(cmd, env=None):
    return subprocess.run(cmd, capture_output=True, text=True, env=env)


def main() -> int:
    label, subject, body_file, *files = sys.argv[1:]
    batches = [f for f in files if f.startswith('app/data/verified/')]
    delta = 0
    for f in batches:
        now = claims(json.loads(Path(f).read_text())['records'])
        head = run(['git', 'show', f'HEAD:./{f}'])
        before = claims(json.loads(head.stdout)['records']) if head.returncode == 0 else 0
        print(f'  {f}: {before} -> {now} ({now - before:+d})')
        delta += now - before

    fatal = []
    for f in batches:
        out = run(['.venv/bin/python', 'scripts/catalog/verify_quotes.py', f], env={**os.environ, 'VQ_CACHE_ONLY': '1'}).stdout
        summary = [ln for ln in out.splitlines() if ' hit, ' in ln]
        misses = [ln for ln in out.splitlines() if ln.startswith('MISS')]
        new = [m for m in misses if any(s in m for s in STEMS)]
        # A new-field citation the checker could not reach was not tested at all: that is not a pass.
        # Run warm_cache.py (outside the sandbox) first; a page that still will not load must be re-cited or dropped.
        untested = [ln for ln in out.splitlines()
                    if ln.startswith(('SKIP', 'INCONCLUSIVE')) and any(s in ln for s in STEMS)]
        print(f'  quotes {Path(f).name}: {summary[-1] if summary else out[-160:]}')
        for m in misses:
            print(('    NEW-FIELD MISS ' if m in new else '    pre-existing MISS ') + m[:170])
        for u in untested:
            print('    NEW-FIELD UNTESTED ' + u[:170])
        fatal += new + untested
    inv = run(['.venv/bin/python', '-m', 'pytest', 'tests/test_tranche_invariants.py', '-p', 'no:cacheprovider',
               '-W', 'ignore', '-o', 'addopts=', '-q'])
    inv_line = [ln for ln in inv.stdout.splitlines() if 'passed' in ln or 'failed' in ln]
    print('  invariants:', inv_line[-1] if inv_line else inv.stdout[-200:])
    if fatal or inv.returncode != 0:
        print('NOT COMMITTED')
        return 1

    s = Path(TEST).read_text()
    old = int(re.findall(r'assert report\.claims_written == (\d+)', s)[-1])
    assert s.count(f'assert report.claims_written == {old}') == 1, old
    new_total = old + delta
    s = s.replace(f'assert report.claims_written == {old}',
                  f'# + {delta} (size backfill {label}).\n    assert report.claims_written == {new_total}')
    Path(TEST).write_text(s)

    doc = Path(DOCS).read_text()
    m = re.search(r'(- \*\*\d+ batches, )([\d,]+)( claims, )', doc)
    assert m, 'docs header not found'
    doc = doc[:m.start(2)] + f'{new_total:,}' + doc[m.end(2):]
    Path(DOCS).write_text(doc)

    body = Path(body_file).read_text().rstrip() + '\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n'
    subprocess.run(['git', 'add', *files, TEST, DOCS], check=True)
    subprocess.run(['git', 'commit', '-q', '-m', f'{subject}\n\n{body}'], check=True)
    print(f'{label}: {delta:+d} claims -> {new_total}')
    print(run(['git', 'log', '--oneline', '-1']).stdout.strip())
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
