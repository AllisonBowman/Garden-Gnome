"""commit_batch.py bNN path/to/bNN.json "<subject>" -- bump the count test + docs header for ONE batch and commit only its files.
Run from garden-gnome/. The batch's claim count comes from the loader over that file alone, so concurrent uncommitted
landings in the tree do not leak into each other's numbers."""
import glob, json, re, subprocess, sys
sys.path.insert(0, '.')
from app.data.claims.tranche import claims_from_record
batch, path, subject = sys.argv[1], sys.argv[2], sys.argv[3]
d = json.load(open(path))
delta = sum(len(claims_from_record(r)[0]) for r in d['records'])
TEST, DOCS = 'tests/test_claim_ingest.py', '../docs/2026-09-02-catalog-truth-collection-run.md'
s = open(TEST).read()
# The corpus total is whatever the LAST assertion in this file says: the running-sum
# comment only tracks batch landings, while backfills add claims outside that chain.
old = int(re.findall(r'assert report\.claims_written == (\d+)', s)[-1])
assert s.count(f'assert report.claims_written == {old}') == 1, old
new = old + delta
s = s.replace(f'assert report.claims_written == {old}',
              f'# + {delta} ({batch}).\n    assert report.claims_written == {new}')
open(TEST, 'w').write(s)
# species/batches counted over COMMITTED files + this one, so other uncommitted landings don't inflate the header
tracked = subprocess.run(['git', 'ls-files', 'app/data/verified'], capture_output=True, text=True).stdout.split()
files = sorted(set(tracked) | {path})
species = sum(len(json.load(open(f))['records']) for f in files)
doc = open(DOCS).read()
m = re.search(r'- \*\*(\d+) batches, ([\d,]+) claims, (\d+) species, 8 authorities\*\* \(b47–b(\d+) landed', doc)
assert m, 'docs header not found'
last = max(int(m.group(4)), int(batch[1:]))
hdr = f'- **{len(files)} batches, {new:,} claims, {species} species, 8 authorities** (b47–b{last} landed'
doc = doc[:m.start()] + hdr + doc[m.end():]
open(DOCS, 'w').write(doc)
msg = f"""{subject}, {new:,} claims over {species} species

{d['normalizations'][0]}

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
"""
subprocess.run(['git', 'add', path, TEST, DOCS], check=True)
# Commit ONLY these paths: another team may have its own changes staged in this tree at the same moment.
subprocess.run(['git', 'commit', '-q', '-m', msg, '--', path, TEST, DOCS], check=True)
print(f'{batch}: +{delta} -> {new} claims, {species} species, {len(files)} batches')
print(subprocess.run(['git', 'log', '--oneline', '-1'], capture_output=True, text=True).stdout.strip())
