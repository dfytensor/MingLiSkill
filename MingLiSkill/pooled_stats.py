# -*- coding: utf-8 -*-
import io, sys, json
out = []
DATA_PATH = r'F:\牛逼模型\MingLi-Bench\data\data.json'
ROUNDS = [
    ('blind15_answers.json', 'blind15_charts.json'),
    ('v5blind_answers.json', 'v5blind_charts.json'),
    ('blind30_answers.json', 'blind30_charts.json'),
]
with open(DATA_PATH, encoding='utf-8') as f:
    data = json.load(f)
key = {q['id']: q for q in data['questions']}
cat_me, cat_rules, cat_n = {}, {}, {}
wrongs_me, wrongs_rules = [], []
for ans_file, chart_file in ROUNDS:
    with open(r'E:\ming_li_skill\MingLiSkill\%s' % ans_file, encoding='utf-8') as f:
        mine = json.load(f)
    with open(r'E:\ming_li_skill\MingLiSkill\%s' % chart_file, encoding='utf-8') as f:
        charts = {c['id']: c for c in json.load(f)}
    for qid, a in mine.items():
        real = key[qid]['answer']
        cat = key[qid].get('category', '?')
        m_ok = a['answer'] == real
        rs = charts[qid]['chart_data'].get('rules_suggestion', {}).get('suggested_answer', '')
        r_ok = rs == real
        cat_n[cat] = cat_n.get(cat, 0) + 1
        cat_me[cat] = cat_me.get(cat, 0) + m_ok
        cat_rules[cat] = cat_rules.get(cat, 0) + r_ok
        if not m_ok:
            wrongs_me.append((qid, cat, a['answer'], real, rs))
        if not r_ok:
            wrongs_rules.append((qid, cat, rs, real))
out.append('=== Pooled category stats (57 Q) ===')
for c in sorted(cat_n):
    out.append('%s: agent %d/%d (%.0f%%) | rules %d/%d (%.0f%%)' % (
        c, cat_me.get(c, 0), cat_n[c], cat_me.get(c, 0)/cat_n[c]*100,
        cat_rules.get(c, 0), cat_n[c], cat_rules.get(c, 0)/cat_n[c]*100))
out.append('')
out.append('=== Agent wrong (qid, cat, mine, real, rules_said) ===')
for w in wrongs_me:
    mark = ' <-- rules got it right' if w[4] == w[3] else ''
    out.append('%s [%s] mine=%s real=%s rules=%s%s' % w + mark if False else '%s [%s] mine=%s real=%s rules=%s%s' % (w[0], w[1], w[2], w[3], w[4], ' <-- rules right' if w[4]==w[3] else ''))
with open(r'E:\ming_li_skill\MingLiSkill\pooled_analysis.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('done')
