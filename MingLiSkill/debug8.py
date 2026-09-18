# -*- coding: utf-8 -*-
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
qs = {c['id']: c for c in json.load(open(r'E:\ming_li_skill\MingLiSkill\hybrid8_charts.json', encoding='utf-8'))}
c = qs['ftb_0001']
ln = c['chart_data'].get('liunian') or {}
out = []
for yi in ln.get('年份流年对比', []):
    out.append(json.dumps(yi, ensure_ascii=False)[:300])
with open(r'E:\ming_li_skill\MingLiSkill\debug8.txt', 'w', encoding='utf-8') as f:
    f.write('\n\n'.join(out))
print('ok')
