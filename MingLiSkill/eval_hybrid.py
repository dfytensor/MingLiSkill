# -*- coding: utf-8 -*-
"""Retrospective evaluation of hybrid_router_v2 on the 57 pooled blind questions."""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from hybrid_router_v2 import evaluate

DATA_PATH = r'F:\牛逼模型\MingLi-Bench\data\data.json'
with open(DATA_PATH, encoding='utf-8') as f:
    data = json.load(f)
key = {q['id']: q for q in data['questions']}

ROUNDS = [
    ('R1', 'blind15_charts.json', 'blind15_answers.json'),
    ('R2', 'v5blind_charts.json', 'v5blind_answers.json'),
    ('R3', 'blind30_charts.json', 'blind30_answers.json'),
]

lines = []
tot_c = tot_n = 0
all_detail = []
for label, chart_file, ans_file in ROUNDS:
    c, n, cats, detail = evaluate(r'E:\ming_li_skill\MingLiSkill\%s' % chart_file,
                                  r'E:\ming_li_skill\MingLiSkill\%s' % ans_file, key)
    tot_c += c
    tot_n += n
    all_detail += [(label,) + d for d in detail]
    lines.append('%s hybrid: %d/%d = %.1f%%' % (label, c, n, c / n * 100))

lines.append('')
lines.append('POOLED hybrid: %d/%d = %.1f%%  (agent alone 23/57=40.4%%, rules alone 23/57=40.4%%, oracle 36/57=63.2%%)' % (tot_c, tot_n, tot_c / tot_n * 100))

# per-category
agg = {}
for label, qid, cat, mine, rs, final, real, res, source in all_detail:
    agg.setdefault(cat, {'t': 0, 'c': 0, 'rules': 0})
    agg[cat]['t'] += 1
    agg[cat]['c'] += (res == 'OK')
    agg[cat]['rules'] += (source == 'rules')
lines.append('')
lines.append('Category breakdown:')
for cat in sorted(agg):
    s = agg[cat]
    lines.append('  %s: %d/%d (%.0f%%) [rules-delegated %d/%d]' % (cat, s['c'], s['t'], s['c']/s['t']*100, s['rules'], s['t']))

lines.append('')
lines.append('Wrong cases (hybrid):')
for label, qid, cat, mine, rs, final, real, res, source in all_detail:
    if res != 'OK':
        lines.append('  %s %s [%s] mine=%s rules=%s -> chose %s(%s), real=%s' % (label, qid, cat, mine, rs, final, source, real))

with open(r'E:\ming_li_skill\MingLiSkill\hybrid_eval.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('done, pooled %d/%d = %.1f%%' % (tot_c, tot_n, tot_c/tot_n*100))
