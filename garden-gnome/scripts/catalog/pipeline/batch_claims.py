"""batch_claims.py path/to/bNN.json -- claims the loader will extract from one batch file (what the ingest total grows by)."""
import json, sys
sys.path.insert(0, '.')
from app.data.claims.tranche import claims_from_record
d = json.load(open(sys.argv[1]))
total = 0
for r in d['records']:
    claims, unsupported = claims_from_record(r)
    total += len(claims)
    if unsupported:
        print('  unsupported on', r['common_name'], unsupported)
print(len(d['records']), 'records', total, 'claims')
