# -*- coding: utf-8 -*-
"""Compare agent blind answers vs rules_suggestion baseline vs real answers,
across all blind rounds. Post-scoring analysis."""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DATA_PATH = r'F:\牛逼模型\MingLi-Bench\data\data.json'

ROUNDS = [
    ('R1 v4(seed20260918,15Q)', 'blind15_answers.json', 'blind15_charts.json'),
    ('R2 v5(seed5150,12Q)', 'v5blind_answers.json', 'v5blind_charts.json'),
    ('R3 v5(seed7777,30Q)', 'blind30_answers.json', 'blind30_charts.json'),
]

with open(DATA_PATH, encoding='utf-8') as f:
    data = json.load(f)
key = {q['id']: q for q in data['questions']}

total_me = total_rules = total_n = 0
cat_me, cat_rules, cat_n = {}, {}, {}
agree_me_right = agree_rules_right = both_wrong = 0

print('%-28s %-14s %-14s' % ('Round', 'Agent盲测', '规则引擎基线'))
print('-' * 62)
for label, ans_file, chart_file in ROUNDS:
    with open(r'E:\ming_li_skill\MingLiSkill\%s' % ans_file, encoding='utf-8') as f:
        mine = json.load(f)
    with open(r'E:\ming_li_skill\MingLiSkill\%s' % chart_file, encoding='utf-8') as f:
        charts = {c['id']: c for c in json.load(f)}
    me_ok = rules_ok = n = 0
    for qid, a in mine.items():
        real = key[qid]['answer']
        m_ok = a['answer'] == real
        rs = charts[qid]['chart_data'].get('rules_suggestion', {}).get('suggested_answer', '')
        r_ok = rs == real
        n += 1
        me_ok += m_ok
        rules_ok += r_ok
        cat = key[qid].get('category', '?')
        cat_n[cat] = cat_n.get(cat, 0) + 1
        cat_me[cat] = cat_me.get(cat, 0) + m_ok
        cat_rules[cat] = cat_rules.get(cat, 0) + r_ok
        if m_ok: total_me += 1
        if r_ok: total_rules += 1
        total_n += 1
        if m_ok and r_ok: agree_me_right += 1
        elif m_ok: agree_me_right += 0  # me right, rules wrong
        elif r_ok: agree_rules_right += 0
        if m_ok and not r_ok: agree_me_right += 0
        # track
        if m_ok and not r_ok: pass
    print('%-28s %d/%d (%.1f%%)   %d/%d (%.1f%%)' % (
        label, me_ok, n, me_ok / n * 100, rules_ok, n, rules_ok / n * 100))

print('-' * 62)
print('POOLED:  Agent %d/%d = %.1f%%  |  规则引擎 %d/%d = %.1f%%' % (
    total_me, total_n, total_me / total_n * 100, total_rules, total_n, total_rules / total_n * 100))

print()
print('分类统计(合并57题): %s' % '  '.join('%s: 我%d/%d 规则%d/%d' % (
    c, cat_me.get(c, 0), cat_n[c], cat_rules.get(c, 0), cat_n[c]) for c in sorted(cat_n)))
