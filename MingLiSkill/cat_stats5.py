# -*- coding: utf-8 -*-
import io, sys, json
from collections import Counter
data = json.load(open(r'F:\牛逼模型\MingLi-Bench\data\data.json', encoding='utf-8'))
by_id = {q['id']: q for q in data['questions']}
BASE = json.load(open(r'E:\ming_li_skill\MingLiSkill\fixed_answers_v5.json', encoding='utf-8'))
wc = Counter(); tc = Counter()
wrong_ids = {}
for qid, v in BASE.items():
    q = by_id.get(qid)
    if not q: continue
    tc[q['category']] += 1
    if v != q['answer']:
        wc[q['category']] += 1
        wrong_ids.setdefault(q['category'], []).append(qid)
lines = []
for cat in sorted(tc, key=lambda c: -wc.get(c, 0)):
    lines.append('%s: %d wrong / %d total (%.0f%%) ids=%s' % (cat, wc.get(cat,0), tc[cat], wc.get(cat,0)*100/tc[cat], ','.join(wrong_ids.get(cat, [])[:20])))
open(r'E:\ming_li_skill\MingLiSkill\cat_stats.txt', 'w', encoding='utf-8').write('\n'.join(lines))
print('written')
