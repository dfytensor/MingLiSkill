# -*- coding: utf-8 -*-
"""apply_marriage_only.py — fixed_answers.json + 婚姻信号修复 = fixed_answers_v2.json"""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from marriage_fix_v2 import analyze

data = json.load(open(r'F:\牛逼模型\MingLi-Bench\data\data.json', encoding='utf-8'))
by_id = {q['id']: q for q in data['questions']}
BASE = json.load(open(r'E:\ming_li_skill\MingLiSkill\fixed_answers.json', encoding='utf-8'))

changed = 0
for qid in sorted(BASE):
    q = by_id.get(qid)
    if not q: continue
    if not (q['category'] == '婚姻' or any(k in q['question'] for k in ['婚','结婚','夫妻','离婚','拍拖','恋爱','嫁','娶','配偶'])):
        continue
    new, why = analyze(q, q['birth_info'])
    if new and new != BASE[qid]:
        print('%s: %s->%s' % (qid, BASE[qid], new))
        BASE[qid] = new
        changed += 1

final = sum(1 for k, v in BASE.items() if k in by_id and by_id[k]['answer'] == v)
json.dump(BASE, open(r'E:\ming_li_skill\MingLiSkill\fixed_answers_v2.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('changed=%d  FINAL: %d/115 = %.1f%%  saved fixed_answers_v2.json' % (changed, final, final/115*100))
