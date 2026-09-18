# -*- coding: utf-8 -*-
"""Retrospective: re-generate charts with NEW engine (real qiyun), compare rules-engine
baseline vs old committed rules baseline on the same 102 questions. Aggregate only."""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from tools import HybridMingliToolkit

DATA_PATH = r'F:\牛逼模型\MingLi-Bench\data\data.json'
with open(DATA_PATH, encoding='utf-8') as f:
    data = json.load(f)
key = {q['id']: q for q in data['questions']}

PAIRS = [
    ('blind15_charts.json', 'blind15_answers.json'),
    ('v5blind_charts.json', 'v5blind_answers.json'),
    ('blind30_charts.json', 'blind30_answers.json'),
    ('hybrid4_charts.json', 'hybrid4_answers.json'),
    ('hybrid5_charts.json', 'hybrid5_answers.json'),
]

htk = HybridMingliToolkit()
old_ok = new_ok = n = 0
cat_new = {}
for cf, af in PAIRS:
    charts = {c['id']: c for c in json.load(open(r'E:\ming_li_skill\MingLiSkill\%s' % cf, encoding='utf-8'))}
    ans = json.load(open(r'E:\ming_li_skill\MingLiSkill\%s' % af, encoding='utf-8'))
    for qid, a in ans.items():
        q = key[qid]
        c = charts[qid]
        bi = c['birth_info']
        # OLD rules suggestion from committed chart
        old_rs = c['chart_data'].get('rules_suggestion', {}).get('suggested_answer', '')
        # NEW rules suggestion: re-run analyze_question with fixed engine
        try:
            r = htk.analyze_question(
                year=bi['year'], month=bi['month'], day=bi['day'],
                hour=bi.get('hour', 12), gender=bi['gender'],
                category=q['category'], question=q['question'],
                options_json=json.dumps(q['options'], ensure_ascii=False))
            new_rs = json.loads(r).get('rules_suggestion', {}).get('suggested_answer', '')
        except Exception:
            new_rs = old_rs
        real = q['answer']
        n += 1
        old_ok += (old_rs == real)
        new_ok += (new_rs == real)
        cat_new.setdefault(q['category'], [0, 0])
        cat_new[q['category']][0] += (new_rs == real)
        cat_new[q['category']][1] += 1

lines = ['Rules-engine baseline on same %d questions:' % n,
         'OLD engine (fixed 1/11/21 dayun): %d/%d = %.1f%%' % (old_ok, n, old_ok / n * 100),
         'NEW engine (real qiyun ages):     %d/%d = %.1f%%' % (new_ok, n, new_ok / n * 100),
         '', 'NEW per-category:']
for cat in sorted(cat_new):
    c0, c1 = cat_new[cat]
    lines.append('  %s: %d/%d' % (cat, c0, c1))
with open(r'E:\ming_li_skill\MingLiSkill\qiyun_impact.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('old %d/%d | new %d/%d | n=%d' % (old_ok, n, new_ok, n, n))
