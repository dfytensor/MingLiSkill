# -*- coding: utf-8 -*-
"""
ensemble_best.py — 多方法取长补短集成
分析每种方法在每个类别的表现，按类别选最优方法。
LOO 验证防止过拟合。
"""
import io, sys, json, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from collections import Counter, defaultdict

BASE = r'E:\ming_li_skill\MingLiSkill'
data = json.load(open(r'F:\牛逼模型\MingLi-Bench\data\data.json', encoding='utf-8'))
key = {q['id']: q for q in data['questions']}

# ===== Load all method outputs =====
methods = {}

# 1. Hybrid committed (LLM + router)
from hybrid_router_v2 import route_answer
from retriever import ROUNDS
for cf, af in ROUNDS:
    charts = {c['id']: c for c in json.load(open(os.path.join(BASE, cf), encoding='utf-8'))}
    ans = json.load(open(os.path.join(BASE, af), encoding='utf-8'))
    for qid, a in ans.items():
        rules = charts[qid]['chart_data'].get('rules_suggestion', {}).get('suggested_answer', '')
        final, _ = route_answer(key[qid]['category'], a['answer'], rules)
        methods.setdefault(qid, {})['hybrid'] = final
        methods[qid]['agent'] = a['answer']
        methods[qid]['rules'] = rules

# 2. KB engine
for line in open(os.path.join(BASE, 'kb_engine_result.txt'), encoding='utf-8'):
    m = re.match(r'(ftb_\d+)\s+\S+\s+kb=(\w)', line)
    if m:
        methods.setdefault(m.group(1), {})['kb'] = m.group(2)

# 3. Corpus engine
for line in open(os.path.join(BASE, 'corpus_engine_result.txt'), encoding='utf-8'):
    m = re.match(r'(ftb_\d+)\s+\S+\s+->\s+(\w)\s+\(real', line)
    if m:
        methods.setdefault(m.group(1), {})['corpus'] = m.group(2)

# 4. Methodology v2
for line in open(os.path.join(BASE, 'methodology_v2_result.txt'), encoding='utf-8'):
    m = re.match(r'(ftb_\d+)\s+\S+\s+(\w)->\s*\w+\s+(OK|X)', line)
    if m:
        methods.setdefault(m.group(1), {})['methodology_v2'] = m.group(2)

print('methods loaded: %d questions' % len(methods))
all_method_names = set()
for qid, m in methods.items():
    all_method_names.update(m.keys())
print('method names: %s' % sorted(all_method_names))

# ===== Per-category per-method accuracy =====
cat_method_acc = defaultdict(lambda: defaultdict(lambda: [0, 0]))
for qid, m in methods.items():
    cat = key[qid]['category']
    real = key[qid]['answer']
    for method_name, answer in m.items():
        cat_method_acc[cat][method_name][1] += 1
        if answer == real:
            cat_method_acc[cat][method_name][0] += 1

print('\n=== Per-category best method ===')
best_by_cat = {}
for cat in sorted(cat_method_acc):
    best_m, best_acc = None, 0
    for method_name, (ok, n) in sorted(cat_method_acc[cat].items()):
        acc = ok / n * 100
        marker = ' ★' if acc > best_acc else ''
        if acc > best_acc:
            best_acc = acc
            best_m = method_name
        print('  %s | %s: %d/%d (%.0f%%)%s' % (cat, method_name, ok, n, acc, marker))
    best_by_cat[cat] = best_m
    print('  → BEST: %s (%.0f%%)' % (best_m, best_acc))
    print()

# ===== LOO validation of category-method router =====
print('=== LOO Router (category → best method, trained on others) ===')
loo_correct = 0
n = 0
for test_qid in methods:
    train = {q: m for q, m in methods.items() if q != test_qid}
    cat = key[test_qid]['category']
    
    # Find best method for this category from training data
    cat_train = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    for qid, m in train.items():
        c = key[qid]['category']
        for mn, ans in m.items():
            cat_train[c][mn][1] += 1
            if ans == key[qid]['answer']:
                cat_train[c][mn][0] += 1
    
    best_m, best_acc = 'hybrid', 0  # default
    for mn, (ok, nn) in cat_train.get(cat, {}).items():
        acc = ok / max(nn, 1)
        if acc > best_acc:
            best_acc = acc
            best_m = mn
    
    # Predict
    pred = methods[test_qid].get(best_m)
    real = key[test_qid]['answer']
    n += 1
    loo_correct += (pred == real)

print('LOO category-router: %d/%d = %.1f%%' % (loo_correct, n, loo_correct / n * 100))

# ===== Agreement-based ensemble =====
print('\n=== Agreement-based ensemble ===')
# If 2+ methods agree → use that answer
# If all disagree → use hybrid
agree2 = agree3 = agree_all = 0
for qid, m in methods.items():
    real = key[qid]['answer']
    answers = list(m.values())
    cnt = Counter(answers)
    if cnt.most_common(1)[0][1] >= 2:
        agree2 += (cnt.most_common(1)[0][0] == real)
    if cnt.most_common(1)[0][1] >= 3:
        agree3 += (cnt.most_common(1)[0][0] == real)

print('When 2+ agree (%d questions): %.1f%% correct' % (sum(1 for m in methods.values() if Counter(m.values()).most_common(1)[0][1] >= 2), agree2 / max(sum(1 for m in methods.values() if Counter(m.values()).most_common(1)[0][1] >= 2), 1) * 100))
print('When 3+ agree (%d questions): %.1f%% correct' % (sum(1 for m in methods.values() if Counter(m.values()).most_common(1)[0][1] >= 3), agree3 / max(sum(1 for m in methods.values() if Counter(m.values()).most_common(1)[0][1] >= 3), 1) * 100))
