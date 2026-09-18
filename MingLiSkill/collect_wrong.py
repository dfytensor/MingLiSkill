# -*- coding: utf-8 -*-
"""Collect all wrong answers across all rounds, run pipeline on each."""
import io, sys, json, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')

DATA = json.load(open(r'F:\牛逼模型\MingLi-Bench\data\data.json', encoding='utf-8'))
KEY = {q['id']: q for q in DATA['questions']}

from retriever import ROUNDS, BASE

# Collect: committed answer per qid (use hybrid router for consistency)
from hybrid_router_v2 import route_answer
committed = {}  # qid -> {pick, agent, rules, real, cat, round}
for cf, af in ROUNDS:
    charts = {c['id']: c for c in json.load(open(os.path.join(BASE, cf), encoding='utf-8'))}
    ans = json.load(open(os.path.join(BASE, af), encoding='utf-8'))
    for qid, a in ans.items():
        rules = charts[qid]['chart_data'].get('rules_suggestion', {}).get('suggested_answer', '')
        final, _ = route_answer(KEY[qid]['category'], a['answer'], rules)
        committed[qid] = {
            'pick': final, 'agent': a['answer'], 'rules': rules,
            'real': KEY[qid]['answer'], 'cat': KEY[qid]['category'],
        }

wrong = {qid: r for qid, r in committed.items() if r['pick'] != r['real']}
right = {qid: r for qid, r in committed.items() if r['pick'] == r['real']}

print('total: %d | correct: %d (%.1f%%) | wrong: %d' % (
    len(committed), len(right), len(right)/len(committed)*100, len(wrong)))

# categorize wrong answers
by_cat = {}
for qid, r in sorted(wrong.items()):
    by_cat.setdefault(r['cat'], []).append(qid)
for cat in sorted(by_cat):
    print('  %s: %d wrong (%s)' % (cat, len(by_cat[cat]), ','.join(by_cat[cat])))

# save wrong list for pipeline processing
with open(r'E:\ming_li_skill\MingLiSkill\wrong_answers.json', 'w', encoding='utf-8') as f:
    json.dump({qid: r for qid, r in sorted(wrong.items())}, f, ensure_ascii=False, indent=1)
print('saved wrong_answers.json')
