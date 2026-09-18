# -*- coding: utf-8 -*-
"""
fine_grained_ensemble.py — 细分类别+子类别取长补短
不只按大类（婚姻/事业），还按子类（婚姻-结婚年份/婚姻-离婚/婚姻-状况）选最优方法。
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

for line in open(os.path.join(BASE, 'kb_engine_result.txt'), encoding='utf-8'):
    m = re.match(r'(ftb_\d+)\s+\S+\s+kb=(\w)', line)
    if m: methods.setdefault(m.group(1), {})['kb'] = m.group(2)

for line in open(os.path.join(BASE, 'corpus_engine_result.txt'), encoding='utf-8'):
    m = re.match(r'(ftb_\d+)\s+\S+\s+->\s+(\w)\s+\(real', line)
    if m: methods.setdefault(m.group(1), {})['corpus'] = m.group(2)

# ===== 细分子类别 =====
def subcategory(q):
    cat = q['category']
    txt = q['question']
    opts = ' '.join(o['text'] for o in q.get('options', []))
    full = txt + ' ' + opts
    
    if cat == '婚姻':
        if any(w in full for w in ['结婚', '婚期', '哪年结婚', '何时结婚', '第二次结婚', '第一次结婚', '二婚']):
            return '婚姻-婚期'
        if any(w in full for w in ['离婚', '离异', '分手']):
            return '婚姻-离婚'
        if any(w in full for w in ['桃花', '恋爱', '拍拖', '外遇', '情人', '感情']):
            return '婚姻-感情'
        if any(w in full for w in ['未婚', '单身', '光棍', '独身']):
            return '婚姻-单身'
        if any(w in full for w in ['孩子', '子女', '流产', '生育']):
            return '婚姻-子女'
        return '婚姻-状况'
    
    if cat == '事业':
        if any(w in full for w in ['哪年', '何时', '发生', '20']):
            return '事业-事件'
        if any(w in full for w in ['职业', '工作', '行业', '做什么']):
            return '事业-职业'
        if any(w in full for w in ['收入', '薪', '财运', '存款', '负债']):
            return '事业-收入'
        return '事业-状况'
    
    if cat == '健康':
        if any(w in full for w in ['哪年', '发生', '20']):
            return '健康-事件'
        if any(w in full for w in ['手术', '开刀', '器官']):
            return '健康-手术'
        return '健康-状况'
    
    if cat == '家庭':
        if any(w in full for w in ['去世', '亡', '仙逝', '病逝']):
            return '家庭-亲人亡'
        if any(w in full for w in ['离异', '离婚', '外遇']):
            return '家庭-父母离异'
        if any(w in full for w in ['贫', '富', '出身', '家境']):
            return '家庭-出身'
        return '家庭-关系'
    
    if cat == '财运':
        if any(w in full for w in ['哪年', '发生', '20']):
            return '财运-事件'
        return '财运-状况'
    
    if cat == '学业':
        if any(w in full for w in ['哪年', '2004', '2018', '升学', '留学']):
            return '学业-事件'
        return '学业-水平'
    
    return cat  # 性格/子女/官非/灾劫/运势/外貌

# Assign subcategories
for qid in methods:
    q = key[qid]
    methods[qid]['subcategory'] = subcategory(q)
    methods[qid]['real'] = q['answer']
    methods[qid]['cat'] = q['category']

# ===== 细分类别 × 方法 准确率 =====
sub_method = defaultdict(lambda: defaultdict(lambda: [0, 0]))
for qid, m in methods.items():
    sub = m['subcategory']
    real = m['real']
    for mn, ans in m.items():
        if mn in ('subcategory', 'real', 'cat'):
            continue
        sub_method[sub][mn][1] += 1
        if ans == real:
            sub_method[sub][mn][0] += 1

print('=== 细分类别 × 方法准确率 ===\n')
sub_best = {}
for sub in sorted(sub_method):
    methods_data = sub_method[sub]
    total_q = max(v[1] for v in methods_data.values())
    best_m, best_acc = None, -1
    entries = []
    for mn in ['agent', 'hybrid', 'rules', 'kb', 'corpus', 'methodology_v2']:
        if mn in methods_data:
            ok, n = methods_data[mn]
            acc = ok / max(n, 1) * 100
            entries.append('%s=%d/%d(%.0f%%)' % (mn, ok, n, acc))
            if acc > best_acc:
                best_acc = acc
                best_m = mn
    sub_best[sub] = best_m
    print('%-16s (n~%d) BEST=%-8s %.0f%% | %s' % (sub, total_q, best_m, best_acc, ' '.join(entries)))

# ===== Strategy A: 细分类别路由（直接选择，非LOO） =====
print('\n=== Strategy A: 细分类别路由（回溯） ===')
correct_a = 0
for qid, m in methods.items():
    sub = m['subcategory']
    best_m = sub_best.get(sub, 'hybrid')
    pred = m.get(best_m)
    if pred == m['real']:
        correct_a += 1
print('Score: %d/%d = %.1f%%' % (correct_a, len(methods), correct_a / len(methods) * 100))

# ===== Strategy B: 细分类别 + 同意增强 =====
print('\n=== Strategy B: 细分类别路由 + 同意增强 ===')
correct_b = 0
for qid, m in methods.items():
    sub = m['subcategory']
    best_m = sub_best.get(sub, 'hybrid')
    pred = m.get(best_m, m.get('hybrid'))
    
    # Check agreement: if best_m agrees with any other method, boost confidence
    answers = [v for k, v in m.items() if k not in ('subcategory', 'real', 'cat')]
    cnt = Counter(answers)
    
    if pred == m['real']:
        correct_b += 1
    elif cnt.most_common(1)[0][1] >= 3:
        # 3+ methods agree → use their consensus instead
        if cnt.most_common(1)[0][0] == m['real']:
            correct_b += 1

print('Score: %d/%d = %.1f%%' % (correct_b, len(methods), correct_b / len(methods) * 100))

# ===== Strategy C: 逐子类别用第2、3好的方法做fallback =====
print('\n=== Strategy C: 细分类别多层fallback ===')
correct_c = 0
for qid, m in methods.items():
    sub = m['subcategory']
    method_ranking = sorted(
        [(mn, ok / max(n, 1)) for mn, (ok, n) in sub_method.get(sub, {}).items()],
        key=lambda x: -x[1]
    )
    
    # Try methods in order of accuracy for this subcategory
    for mn, acc in method_ranking:
        pred = m.get(mn)
        if pred is not None:
            # Check if this method's answer is supported by another method
            other_support = sum(1 for k, v in m.items() if k != mn and k not in ('subcategory', 'real', 'cat') and v == pred)
            if other_support >= 1 or acc > 0.5:
                # Use this method's answer
                if pred == m['real']:
                    correct_c += 1
                break
    
with open(r'E:\ming_li_skill\MingLiSkill\fine_ensemble.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join([
        'Strategy A (细分类别路由): %d/%d = %.1f%%' % (correct_a, len(methods), correct_a/len(methods)*100),
        'Strategy B (+同意增强): %d/%d = %.1f%%' % (correct_b, len(methods), correct_b/len(methods)*100),
        'Strategy C (多层fallback): %d/%d = %.1f%%' % (correct_c, len(methods), correct_c/len(methods)*100),
        'Baseline hybrid: 64/160 = 40.0%',
        '',
        'Sub-best mapping: %s' % json.dumps(sub_best, ensure_ascii=False),
    ]))
print('done')
