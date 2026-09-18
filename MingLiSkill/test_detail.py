# -*- coding: utf-8 -*-
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from tools import HybridMingliToolkit
HTK = HybridMingliToolkit()
data = json.load(open(r'F:\牛逼模型\MingLi-Bench\data\data.json', encoding='utf-8'))
q = next(q for q in data['questions'] if q['id'] == 'ftb_0147')
bi = q['birth_info']
r = HTK.analyze_question(year=bi['year'], month=bi['month'], day=bi['day'],
                          hour=bi.get('hour', 12), gender=bi['gender'],
                          category='性格', question=q['question'],
                          options_json=json.dumps(q['options'], ensure_ascii=False))
d = json.loads(r)
da = d.get('detailed_analysis', {})
err = da.get('detailed_analysis_error', '')
out = []
if err:
    out.append('ERROR: %s' % err)
ss = da.get('十神详表', {})
if ss:
    out.append('十神详表:')
    for name, positions in ss.items():
        root_marks = ['%s(根=%s)' % (p['位置'], p['有根']) for p in positions]
        out.append('  %s × %d: %s' % (name, len(positions), ', '.join(root_marks)))
else:
    out.append('十神详表 empty')
    out.append('all detailed_analysis keys: %s' % list(da.keys()))
with open(r'E:\ming_li_skill\MingLiSkill\detail_verify2.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('done')
