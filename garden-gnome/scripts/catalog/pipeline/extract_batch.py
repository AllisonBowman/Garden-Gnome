"""extract_batch.py bNN TASKID -- write bNN_records.json from a completed workflow task output."""
import json, os, sys
S = os.path.dirname(os.path.abspath(__file__))
b, task = sys.argv[1], sys.argv[2]
src = task if os.path.exists(task) else f'{S}/../tasks/{task}.output'  # a task-output file path, or a task id in the old scratchpad layout
out = json.load(open(src))
res = out['result']
json.dump(res, open(f'{S}/{b}_records.json', 'w'), indent=1, ensure_ascii=False)
print('records', len(res['records']), '| unverified', res['unverified'], '| failed', res['agents_failed'],
      '| agents', out.get('agentCount'), '| tokens', out.get('totalTokens'))
