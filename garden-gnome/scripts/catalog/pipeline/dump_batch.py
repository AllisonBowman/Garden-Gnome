"""dump_batch.py bNN -- write bNN_dump.txt (records + citations) and bNN_audit.txt (audit findings)."""
import json, os, sys
S = os.path.dirname(os.path.abspath(__file__))
b = sys.argv[1]
res = json.load(open(f'{S}/{b}_records.json'))
with open(f'{S}/{b}_dump.txt', 'w') as f:
    for r in res['records']:
        f.write('===== %s | %s | acc %s\n' % (r['scientific_name_given'], r['common_name'], r['scientific_name_accepted']))
        for k, v in r.items():
            if k not in ('citations', 'unknowns') and v is not None:
                f.write('  %s: %r\n' % (k, v))
        f.write('  --- citations ---\n')
        for i, c in enumerate(r['citations']):
            f.write('  [%d] %s\n      SRC: %s\n      URL: %s\n      Q: %r\n' % (i, c['claim'], c['source'], c['url'], c['quote']))
        f.write('  --- unknowns (non-audit) ---\n')
        for u in r['unknowns']:
            if ' on audit' not in u:
                f.write('   - %s\n' % u)
        f.write('\n')
with open(f'{S}/{b}_audit.txt', 'w') as f:
    for r in res['records']:
        for u in r['unknowns']:
            if ' on audit' in u:
                f.write('\n===== %s (%s) =====\n--- %s\n' % (r['common_name'], r['scientific_name_given'], u))
    f.write('\n===== AUDIT SUMMARY =====\n%s\n' % json.dumps(res.get('audit_summary'), indent=1, ensure_ascii=False))
for fn in (f'{b}_dump.txt', f'{b}_audit.txt'):
    print(fn, os.path.getsize(f'{S}/{fn}'))
