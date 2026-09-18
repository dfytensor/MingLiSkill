# -*- coding: utf-8 -*-
"""Blend test: does corpus retrieval add complementary signal to committed hybrid?"""
import io, sys, json, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

data = json.load(open(r'F:\牛逼模型\MingLi-Bench\data\data.json', encoding='utf-8'))
key = {q['id']: q for q in data['questions']}

# committed hybrid picks
hybrid = {}
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from hybrid_router_v2 import route_answer
from retriever import ROUNDS, BASE
for cf, af in ROUNDS:
    charts = {c['id']: c for c in json.load(open(os.path.join(BASE, cf), encoding='utf-8'))}
    ans = json.load(open(os.path.join(BASE, af), encoding='utf-8'))
    for qid, a in ans.items():
        rules = charts[qid]['chart_data'].get('rules_suggestion', {}).get('suggested_answer', '')
        final, _ = route_answer(key[qid]['category'], a['answer'], rules)
        hybrid[qid] = final

# corpus engine picks + theme scores from detail file
corpus = {}
theme_strength = {}
for line in open(r'E:\ming_li_skill\MingLiSkill\corpus_engine_result.txt', encoding='utf-8'):
    m = re.match(r'(ftb_\d+)\s+\S+\s+->\s+(\w)\s+\(real (\w)\)\s+(OK|X)\s+\|\s+themes=(\{.*\})', line.strip())
    if m:
        qid, pick, real, ok, th = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)
        corpus[qid] = pick
        try:
            d = eval(th)
            theme_strength[qid] = max(d.values()) if d else 0
        except Exception:
            theme_strength[qid] = 0

n = len(hybrid)
agree = sum(1 for qid in hybrid if qid in corpus and corpus[qid] == hybrid[qid])
print('corpus picks available: %d | agree with hybrid: %d/%d = %.0f%%' % (len(corpus), agree, n, agree / n * 100))

# threshold blend: if corpus top-theme >= T, use corpus; else hybrid
for T in [0, 0.5, 1.0, 1.5, 2.0, 3.0]:
    ok = 0
    cnt = 0
    for qid, h in hybrid.items():
        if qid in corpus and theme_strength.get(qid, 0) >= T:
            pick = corpus[qid]
            cnt += 1
        else:
            pick = h
        ok += (pick == key[qid]['answer'])
    print('T>=%.1f: %d/%d = %.1f%% (corpus-decided %d)' % (T, ok, n, ok / n * 100, cnt))
