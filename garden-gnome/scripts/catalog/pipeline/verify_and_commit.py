"""verify_and_commit.py bNN path/to/bNN.json "<subject>" -- the orchestrator's one-call landing check.

Runs the loader count, land_check, verify_quotes and the tranche invariants; commits (via commit_batch.py) only if all
pass. Prints a handful of lines. Run from garden-gnome/."""
import json, os, re, subprocess, sys
sp = os.path.dirname(os.path.abspath(__file__))
b, path, subject = sys.argv[1], sys.argv[2], sys.argv[3]
def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, shell=isinstance(cmd, str))
out = run(['.venv/bin/python', f'{sp}/batch_claims.py', path]).stdout.strip()
print('claims  :', out.splitlines()[-1])
lc = run(['.venv/bin/python', 'scripts/catalog/land_check.py', f'{sp}/{b}_landed_records.json'])
lc_tail = (lc.stdout + lc.stderr).strip().splitlines()[-1:] or ['']
tox = [l.strip() for l in (lc.stdout).splitlines() if 'toxic_to_pets=True' in l or 'toxic_to_pets=False' in l or l.strip().startswith('quote:')]
print('landchk :', lc_tail[0], '| exit', lc.returncode)
for t in tox: print('   ', t[:150])
vq = run(['.venv/bin/python', 'scripts/catalog/verify_quotes.py', path])
vq_line = [l for l in vq.stdout.splitlines() if ' hit, ' in l]
miss = [l for l in vq.stdout.splitlines() if l.startswith('MISS')]
print('quotes  :', vq_line[-1] if vq_line else vq.stdout[-200:])
for m in miss: print('   ', m[:150])
inv = run(['.venv/bin/python', '-m', 'pytest', 'tests/test_tranche_invariants.py', '-p', 'no:cacheprovider', '-W', 'ignore', '-o', 'addopts=', '-q'])
inv_line = [l for l in inv.stdout.splitlines() if 'passed' in l or 'failed' in l]
print('invariants:', inv_line[-1] if inv_line else inv.stdout[-200:])
ok = lc.returncode == 0 and 'none' in lc_tail[0] and not miss and inv.returncode == 0
if not ok:
    print('NOT COMMITTED')
    sys.exit(1)
cm = run(['.venv/bin/python', f'{sp}/commit_batch.py', b, path, subject])
print(cm.stdout.strip() or cm.stderr[-500:])
