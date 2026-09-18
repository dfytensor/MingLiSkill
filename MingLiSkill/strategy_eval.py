# -*- coding: utf-8 -*-
"""Offline strategy comparison on existing blind data (57 R1-R3 + 15 R4).
Strategies are evaluated post-hoc here; the winner gets validated prospectively in R5."""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from hybrid_router_v2 import AGENT_CATEGORIES, RULES_CATEGORIES

DATA_PATH = r'F:\牛逼模型\MingLi-Bench\data\data.json'
with open(DATA_PATH, encoding='utf-8') as f:
    data = json.load(f)
key = {q['id']: q for q in data['questions']}

# collect (qid, cat, agent, rules, real) for all rounds
rows = []
PAIRS = [
    ('blind15_charts.json', 'blind15_answers.json'),
    ('v5blind_charts.json', 'v5blind_answers.json'),
    ('blind30_charts.json', 'blind30_answers.json'),
    ('hybrid4_charts.json', 'hybrid4_answers.json'),
]
for chart_file, ans_file in PAIRS:
    with open(r'E:\ming_li_skill\MingLiSkill\%s' % chart_file, encoding='utf-8') as f:
        charts = {c['id']: c for c in json.load(f)}
    with open(r'E:\ming_li_skill\MingLiSkill\%s' % ans_file, encoding='utf-8') as f:
        mine = json.load(f)
    for qid, a in mine.items():
        rs = charts[qid]['chart_data'].get('rules_suggestion', {}).get('suggested_answer', '')
        rows.append((qid, key[qid].get('category', '?'), a['answer'], rs, key[qid]['answer']))

def score(strategy):
    c = n = 0
    cat = {}
    for qid, category, ag, rs, real in rows:
        if strategy == 'S1_current':
            pick = rs if category in RULES_CATEGORIES else ag
        elif strategy == 'S2_agree_then_rules':
            pick = ag if ag == rs else rs
        elif strategy == 'S3_agree_then_agent':
            pick = ag if ag == rs else ag
        elif strategy == 'S4_hybrid_disagree_rules':
            pick = rs if (category in RULES_CATEGORIES or ag != rs) else ag
        elif strategy == 'S5_hybrid_agent_categories_disagree_rules':
            # agent cats: agree->agent, disagree->rules; rules cats: rules
            pick = rs if (category in RULES_CATEGORIES or ag != rs) else ag
            pick = ag if (category in AGENT_CATEGORIES and ag == rs) else pick
        elif strategy == 'S6_always_agreement_only_scored':
            pick = ag if ag == rs else None
        elif strategy == 'S7_hybrid_disagree_agent':
            pick = ag if (category not in RULES_CATEGORIES) else rs
        n0 = 1
        if strategy == 'S6_always_agreement_only_scored' and pick is None:
            continue
        ok = pick == real
        n += 1
        c += ok
        cat.setdefault(category, [0, 0])
        cat[category][0] += ok
        cat[category][1] += 1
    return c, n, cat

out = []
for s in ['S1_current', 'S2_agree_then_rules', 'S3_agree_then_agent',
          'S4_hybrid_disagree_rules', 'S7_hybrid_disagree_agent']:
    c, n, cat = score(s)
    out.append('%s: %d/%d = %.1f%%' % (s, c, n, c / n * 100))

# agreement rate stats
agree = sum(1 for r in rows if r[2] == r[3])
out.append('')
out.append('agent==rules agreement: %d/%d = %.1f%%' % (agree, len(rows), agree / len(rows) * 100))
ag_ok = sum(1 for r in rows if r[2] == r[3] and r[2] == r[4])
out.append('when agree, correct: %d/%d = %.1f%%' % (ag_ok, agree, ag_ok / agree * 100))

# per-strategy per-category for S4
c, n, cat = score('S4_hybrid_disagree_rules')
out.append('')
out.append('S4 category: %s' % '  '.join('%s %d/%d' % (k, v[0], v[1]) for k, v in sorted(cat.items())))

with open(r'E:\ming_li_skill\MingLiSkill\strategy_eval.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('done')
