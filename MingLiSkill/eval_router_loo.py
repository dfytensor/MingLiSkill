# -*- coding: utf-8 -*-
"""LOO evaluation of learned routers over the committed questions.
Strategies trained on the other questions, predicted on 1 — no self-contamination."""
import io, sys, json, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from retriever import Retriever, ROUNDS, BASE
from collections import Counter, defaultdict

r = Retriever()
key = {}
data = json.load(open(r'F:\牛逼模型\MingLi-Bench\data\data.json', encoding='utf-8'))
for q in data['questions']:
    key[q['id']] = q

records = []
for cf, af in ROUNDS:
    charts = {c['id']: c for c in json.load(open(os.path.join(BASE, cf), encoding='utf-8'))}
    ans = json.load(open(os.path.join(BASE, af), encoding='utf-8'))
    for qid, a in ans.items():
        rules = charts[qid]['chart_data'].get('rules_suggestion', {}).get('suggested_answer', '')
        records.append({'qid': qid, 'cat': key[qid]['category'], 'agent': a['answer'],
                        'rules': rules, 'real': key[qid]['answer']})
print('records: %d' % len(records))


def predict_router(rec, train):
    cat = rec['cat']
    stat = defaultdict(lambda: [0, 0, 0, 0])
    for t in train:
        s = stat[t['cat']]
        s[0] += (t['agent'] == t['real']); s[1] += 1
        s[2] += (t['rules'] == t['real']); s[3] += 1
    a_acc = stat[cat][0] / max(stat[cat][1], 1)
    r_acc = stat[cat][2] / max(stat[cat][3], 1)
    src = 'agent' if a_acc >= r_acc else 'rules'
    dis_ok_a = dis_ok_r = 0
    for t in train:
        if t['agent'] != t['rules']:
            dis_ok_a += (t['agent'] == t['real'])
            dis_ok_r += (t['rules'] == t['real'])
    dis_src = 'agent' if dis_ok_a >= dis_ok_r else 'rules'
    out = {}
    out['R_cat'] = rec['agent'] if src == 'agent' else rec['rules']
    out['R_best2'] = rec['agent'] if rec['agent'] == rec['rules'] else rec[dis_src]
    return out


strategies = ['R_cat', 'R_best2']
ok = {s: 0 for s in strategies}
b_agent = b_rules = 0
n = len(records)
for i, rec in enumerate(records):
    train = records[:i] + records[i + 1:]
    preds = predict_router(rec, train)
    for s in strategies:
        ok[s] += (preds[s] == rec['real'])
    b_agent += (rec['agent'] == rec['real'])
    b_rules += (rec['rules'] == rec['real'])

lines = ['LOO router evaluation on %d questions (train=others):' % n]
for s in strategies:
    lines.append('  %s: %d/%d = %.1f%%' % (s, ok[s], n, ok[s] / n * 100))
lines.append('baselines: agent %d/%d = %.1f%% | rules %d/%d = %.1f%%' % (
    b_agent, n, b_agent / n * 100, b_rules, n, b_rules / n * 100))
with open(r'E:\ming_li_skill\MingLiSkill\router_loo.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('done')
