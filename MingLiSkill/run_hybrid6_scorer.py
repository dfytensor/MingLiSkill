# -*- coding: utf-8 -*-
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
import tools
from marriage_scorer import rank_years
qs = {c['id']: c for c in json.load(open(r'E:\ming_li_skill\MingLiSkill\hybrid6_charts.json', encoding='utf-8'))}
out = []
for qid in ['ftb_0034', 'ftb_0076']:
    c = qs[qid]
    b = c['chart_data']['bazi']
    chart = {'日主': b['日主'], 'gender': c['birth_info']['gender'], '四柱': b['四柱']}
    ln = c['chart_data'].get('liunian', {})
    ranked = rank_years(chart, ln)
    out.append('%s (%s): %s' % (qid, b['日主'], [(r['year'], r['score']) for r in ranked]))
with open(r'E:\ming_li_skill\MingLiSkill\hybrid6_scorer.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('ok')
