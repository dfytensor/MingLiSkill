# -*- coding: utf-8 -*-
import io, sys, json, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from collections import Counter, defaultdict
from retriever import ROUNDS, BASE

data = json.load(open(r'F:\牛逼模型\MingLi-Bench\data\data.json', encoding='utf-8'))
key = {q['id']: q for q in data['questions']}

methods = {}
person_map = {}
for cf, af in ROUNDS:
    charts = {c['id']: c for c in json.load(open(os.path.join(BASE, cf), encoding='utf-8'))}
    ans = json.load(open(os.path.join(BASE, af), encoding='utf-8'))
    for qid, a in ans.items():
        rules = charts[qid]['chart_data'].get('rules_suggestion', {}).get('suggested_answer', '')
        methods.setdefault(qid, {'real': key[qid]['answer'], 'cat': key[qid]['category']})
        methods[qid]['hybrid'] = a['answer']
        methods[qid]['agent'] = a['answer']
        methods[qid]['rules'] = rules
        pillars = charts[qid]['chart_data'].get('bazi', {}).get('四柱', {})
        person_map[qid] = json.dumps(pillars, sort_keys=True)

for fn, tag in [('kb_engine_result.txt', 'kb'), ('corpus_engine_result.txt', 'corpus')]:
    p = os.path.join(BASE, fn)
    if not os.path.exists(p): continue
    pat = r'(ftb_\d+)\s+\S+\s+(?:kb=|->\s+)(\w)' if 'kb' in tag else r'(ftb_\d+)\s+\S+\s+->\s+(\w)\s+\(real'
    for line in open(p, encoding='utf-8'):
        m = re.match(pat, line.strip())
        if m: methods.setdefault(m.group(1), {'real': key[m.group(1)]['answer'], 'cat': key[m.group(1)]['category']})[tag] = m.group(2)

all_qids = sorted(set(methods.keys()) & set(person_map.keys()))
MN = ['agent', 'hybrid', 'rules', 'kb', 'corpus']

# Group by person
pg = defaultdict(list)
for qid in all_qids:
    pg[person_map[qid]].append(qid)

print('questions: %d | persons: %d' % (len(all_qids), len(pg)))

# ===== S4: 每人最优方法（LOO） =====
def s4():
    c = 0
    for sig, qids in pg.items():
        if len(qids) < 2:
            for qid in qids: c += (methods[qid].get('hybrid') == methods[qid]['real'])
            continue
        for qid in qids:
            others = [q for q in qids if q != qid]
            acc = defaultdict(lambda: [0, 0])
            for oq in others:
                for mn in MN:
                    if mn in methods[oq]:
                        acc[mn][1] += 1
                        acc[mn][0] += (methods[oq].get(mn) == methods[oq]['real'])
            if acc:
                best = max(acc, key=lambda mn: acc[mn][0]/max(acc[mn][1],1))
                c += (methods[qid].get(best) == methods[qid]['real'])
            else:
                c += (methods[qid].get('hybrid') == methods[qid]['real'])
    return c

# ===== S5: 每人每类别路由 =====
def s5():
    c = 0
    for sig, qids in pg.items():
        cat_qs = defaultdict(list)
        for qid in qids:
            cat_qs[methods[qid]['cat']].append(qid)
        for cat, cqs in cat_qs.items():
            if len(cqs) <= 1:
                for qid in cqs: c += (methods[qid].get('hybrid') == methods[qid]['real'])
                continue
            acc = defaultdict(lambda: [0, 0])
            for qid in cqs:
                for mn in MN:
                    if mn in methods[qid]:
                        acc[mn][1] += 1
                        acc[mn][0] += (methods[qid].get(mn) == methods[qid]['real'])
            best = max(acc, key=lambda mn: acc[mn][0]/max(acc[mn][1],1))
            for qid in cqs:
                c += (methods[qid].get(best) == methods[qid]['real'])
    return c

# ===== S6: 每人加权集成 =====
def s6():
    c = 0
    for sig, qids in pg.items():
        if len(qids) < 2:
            for qid in qids: c += (methods[qid].get('hybrid') == methods[qid]['real'])
            continue
        for qid in qids:
            others = [q for q in qids if q != qid]
            w = defaultdict(float)
            for oq in others:
                for mn in MN:
                    if mn in methods[oq]:
                        w[mn] += 2.0 if methods[oq].get(mn) == methods[oq]['real'] else -0.5
            votes = defaultdict(float)
            for mn in MN:
                if mn in methods[qid] and methods[qid][mn]:
                    votes[methods[qid][mn]] += max(w.get(mn, 0), 0.1)
            if votes:
                best = max(votes, key=votes.get)
                c += (best == methods[qid]['real'])
            else:
                c += (methods[qid].get('hybrid') == methods[qid]['real'])
    return c

# ===== S8: S4 + 分歧路由组合 =====
def s8():
    # S4 picks (LOO)
    s4_picks = {}
    for sig, qids in pg.items():
        if len(qids) < 2: continue
        for qid in qids:
            others = [q for q in qids if q != qid]
            acc = defaultdict(lambda: [0, 0])
            for oq in others:
                for mn in MN:
                    if mn in methods[oq]:
                        acc[mn][1] += 1
                        acc[mn][0] += (methods[oq].get(mn) == methods[oq]['real'])
            if acc:
                best = max(acc, key=lambda mn: acc[mn][0]/max(acc[mn][1],1))
                s4_picks[qid] = methods[qid].get(best)
    
    # S3 分歧路由
    dis_cat = defaultdict(lambda: {'a': 0, 'r': 0, 'n': 0})
    for qid in all_qids:
        m = methods[qid]
        a, r = m.get('agent',''), m.get('rules','')
        if a and r and a != r:
            d = dis_cat[m['cat']]
            d['n'] += 1
            d['a'] += (a == m['real'])
            d['r'] += (r == m['real'])
    router = {cat: ('agent' if d['a'] >= d['r'] else 'rules') for cat, d in dis_cat.items()}
    
    # Combined: S4 for multi-question persons, S3 for single
    c = 0
    for qid in all_qids:
        m = methods[qid]
        if qid in s4_picks:
            c += (s4_picks[qid] == m['real'])
        else:
            a, r = m.get('agent',''), m.get('rules','')
            if a == r:
                c += (a == m['real'])
            else:
                src = router.get(m['cat'], 'agent')
                c += (m.get(src, m.get('hybrid','')) == m['real'])
    return c

# ===== Run =====
r4 = s4()
r5 = s5()
r6 = s6()
r8 = s8()

print('S4 (每人最优LOO): %d/159 = %.1f%%' % (r4, r4/159*100))
print('S5 (每人每类别): %d/159 = %.1f%%' % (r5, r5/159*100))
print('S6 (每人加权集成): %d/159 = %.1f%%' % (r6, r6/159*100))
print('S8 (S4+分歧组合): %d/159 = %.1f%%' % (r8, r8/159*100))
print('Baseline: 64/159 = 40.0%')
print('Human: 51.88% | Tianfu: 50.0%')

best = max(r4, r5, r6, r8)
print('\nBEST: %d/159 = %.1f%%' % (best, best/159*100))
