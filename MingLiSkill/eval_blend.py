# -*- coding: utf-8 -*-
"""Retrospective blend test (clearly labeled: NOT prospective)."""
import io, sys, json, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from collections import Counter

data = json.load(open(r'F:\牛逼模型\MingLi-Bench\data\data.json', encoding='utf-8'))
key = {q['id']: q for q in data['questions']}

# committed hybrid answers (agent or rules per router) per round
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from hybrid_router_v2 import route_answer
from retriever import ROUNDS, BASE

records = {}
for cf, af in ROUNDS:
    charts = {c['id']: c for c in json.load(open(os.path.join(BASE, cf), encoding='utf-8'))}
    ans = json.load(open(os.path.join(BASE, af), encoding='utf-8'))
    for qid, a in ans.items():
        rules = charts[qid]['chart_data'].get('rules_suggestion', {}).get('suggested_answer', '')
        final, _ = route_answer(key[qid]['category'], a['answer'], rules)
        records[qid] = {'hybrid': final, 'agent': a['answer'], 'rules': rules,
                        'real': key[qid]['answer'], 'cat': key[qid]['category']}

# KB engine picks from kb_engine_result.txt detail lines
kb_pick = {}
for line in open(r'E:\ming_li_skill\MingLiSkill\kb_engine_result.txt', encoding='utf-8'):
    m = re.match(r'(ftb_\d+)\s+\S+\s+kb=(\w)', line)
    if m:
        kb_pick[m.group(1)] = m.group(2)
import re

b2 = b3 = n = 0
for qid, rec in records.items():
    n += 1
    kb = kb_pick.get(qid)
    votes2 = Counter([rec['hybrid'], rec['rules']])
    b2 += (votes2.most_common(1)[0][0] == rec['real'])
    if kb:
        votes3 = Counter([rec['hybrid'], rec['rules'], kb])
        b3 += (votes3.most_common(1)[0][0] == rec['real'])
    else:
        b3 += (votes2.most_common(1)[0][0] == rec['real'])

lines = ['RETROSPECTIVE ONLY (answers already seen — NOT prospective validation):',
         'hybrid committed: 64/160 = 40.0%',
         'blend2 (hybrid+rules majority): %d/%d = %.1f%%' % (b2, n, b2 / n * 100),
         'blend3 (hybrid+rules+KB majority): %d/%d = %.1f%%' % (b3, n, b3 / n * 100)]
with open(r'E:\ming_li_skill\MingLiSkill\blend_result.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('\n'.join(lines))
