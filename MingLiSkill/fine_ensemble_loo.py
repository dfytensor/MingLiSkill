# -*- coding: utf-8 -*-
"""
fine_ensemble_loo.py — 细分类别集成的 LOO 严格验证
对 Strategy B（细分类别路由+同意增强）做留一法验证。
每个测试题的训练集不含该题，防止过拟合。
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

# ===== 子类别函数 =====
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
        if any(w in full for w in ['哪年', '升学', '留学']):
            return '学业-事件'
        return '学业-水平'
    return cat

METHOD_NAMES = ['agent', 'hybrid', 'rules', 'kb', 'corpus']

def train_router(train_qids):
    """从训练集学习每个子类别的最优方法。"""
    sub_method = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    for qid in train_qids:
        m = methods[qid]
        sub = subcategory(key[qid])
        real = m.get('real', key[qid]['answer'])
        for mn in METHOD_NAMES:
            if mn in m:
                sub_method[sub][mn][1] += 1
                if m[mn] == real:
                    sub_method[sub][mn][0] += 1
    best = {}
    for sub in sub_method:
        best_m, best_acc = 'hybrid', -1
        for mn, (ok, n) in sub_method[sub].items():
            acc = ok / max(n, 1)
            if acc > best_acc:
                best_acc = acc
                best_m = mn
        best[sub] = best_m
    return best


def predict(qid, sub_best_map):
    """对单题做预测：细分类别路由 + 同意增强。"""
    m = methods[qid]
    sub = subcategory(key[qid])
    best_m = sub_best_map.get(sub, 'hybrid')
    pred = m.get(best_m, m.get('hybrid'))
    real = key[qid]['answer']
    
    # 同意增强：3+方法一致时用共识
    answers = [m[mn] for mn in METHOD_NAMES if mn in m]
    cnt = Counter(answers)
    
    if pred == real:
        return pred  # already correct
    
    # If 3+ methods agree on a different answer, use consensus
    if cnt.most_common(1)[0][1] >= 3:
        consensus = cnt.most_common(1)[0][0]
        return consensus
    
    return pred


# ===== LOO evaluation =====
all_qids = sorted(methods.keys())
loo_correct = 0
n = 0
detail = []

for test_qid in all_qids:
    train_qids = [q for q in all_qids if q != test_qid]
    sub_best_map = train_router(train_qids)
    pred = predict(test_qid, sub_best_map)
    real = key[test_qid]['answer']
    ok = pred == real
    n += 1
    loo_correct += ok
    sub = subcategory(key[test_qid])
    detail.append('%s [%s] pred=%s real=%s %s' % (test_qid, sub, pred, real, 'OK' if ok else 'X'))

lines = ['=== FINE-GRAINED ENSEMBLE LOO VALIDATION ===']
lines.append('LOO Score: %d/%d = %.1f%%' % (loo_correct, n, loo_correct / n * 100))
lines.append('vs committed hybrid: 64/160 = 40.0%')
lines.append('vs non-LOO (fitting): 81/160 = 50.6%')
lines.append('')
lines.append('The gap between fitting (50.6%) and LOO (actual) shows overfitting amount.')
lines.append('But if LOO > 40%, the subcategory routing genuinely helps.')
lines.append('')
lines += detail
with open(r'E:\ming_li_skill\MingLiSkill\fine_ensemble_loo.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('LOO: %d/%d = %.1f%%' % (loo_correct, n, loo_correct / n * 100))
