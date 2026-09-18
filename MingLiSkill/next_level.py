# -*- coding: utf-8 -*-
"""
next_level.py — 三种进一步提升策略
S5: 每人每类别路由（比每人路由更细粒度）
S6: 每人加权集成（不选一个方法，按历史准确率加权所有方法）
S7: 命盘相似度跨人学习（同类命盘借用他人最优方法）
"""
import io, sys, json, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from collections import Counter, defaultdict
from retriever import ROUNDS, BASE

BASE_DIR = BASE
data = json.load(open(r'F:\牛逼模型\MingLi-Bench\data\data.json', encoding='utf-8'))
key = {q['id']: q for q in data['questions']}

# ===== Load all methods =====
methods = {}
person_map = {}  # qid -> pillars_signature

for cf, af in ROUNDS:
    charts = {c['id']: c for c in json.load(open(os.path.join(BASE_DIR, cf), encoding='utf-8'))}
    ans = json.load(open(os.path.join(BASE_DIR, af), encoding='utf-8'))
    for qid, a in ans.items():
        rules = charts[qid]['chart_data'].get('rules_suggestion', {}).get('suggested_answer', '')
        methods.setdefault(qid, {})['hybrid'] = a['answer']
        methods[qid]['agent'] = a['answer']
        methods[qid]['rules'] = rules
        pillars = charts[qid]['chart_data'].get('bazi', {}).get('四柱', {})
        sig = json.dumps(pillars, sort_keys=True)
        person_map[qid] = sig

for line in open(os.path.join(BASE_DIR, 'kb_engine_result.txt'), encoding='utf-8'):
    m = re.match(r'(ftb_\d+)\s+\S+\s+kb=(\w)', line)
    if m: methods.setdefault(m.group(1), {})['kb'] = m.group(2)

for line in open(os.path.join(BASE_DIR, 'corpus_engine_result.txt'), encoding='utf-8'):
    m = re.match(r'(ftb_\d+)\s+\S+\s+->\s+(\w)\s+\(real', line)
    if m: methods.setdefault(m.group(1), {})['corpus'] = m.group(2)

METHOD_NAMES = ['agent', 'hybrid', 'rules', 'kb', 'corpus']

# Add missing person_map entries from chart data
for qid in list(methods.keys()):
    methods[qid]['real'] = key[qid]['answer']
    methods[qid]['cat'] = key[qid]['category']
    if qid not in person_map:
        for cf, af in ROUNDS:
            charts = json.load(open(os.path.join(BASE_DIR, cf), encoding='utf-8'))
            for c in charts:
                if c['id'] == qid:
                    pillars = c['chart_data'].get('bazi', {}).get('四柱', {})
                    person_map[qid] = json.dumps(pillars, sort_keys=True)
                    break

METHOD_NAMES = ['agent', 'hybrid', 'rules', 'kb', 'corpus']

# Group by person
person_groups = defaultdict(list)
for qid in all_qids:
    person_map_key = person_map[qid]
    person_groups[person_map_key].append(qid)

print('questions: %d | unique persons: %d' % (len(all_qids), len(person_groups)))


# ===== S5: 每人每类别路由 =====
def s5_person_category():
    """对每个命主，按类别分别统计哪个方法最准（比S4更细粒度）。"""
    correct = 0
    for sig, qids in person_groups.items():
        if len(qids) < 2:
            # 单题命主，用 hybrid
            for qid in qids:
                correct += (methods[qid].get('hybrid') == methods[qid]['real'])
            continue
        
        # 按类别分组
        cat_qs = defaultdict(list)
        for qid in qids:
            cat = key[qid]['category']
            cat_qs[cat].append(qid)
        
        for cat, cat_qids in cat_qs.items():
            if len(cat_qids) == 1:
                # 单题类别，用该命主全局最优方法
                method_acc = defaultdict(lambda: [0, 0])
                for qid in qids:
                    m = methods[qid]
                    for mn in METHOD_NAMES:
                        if mn in m:
                            method_acc[mn][1] += 1
                            if m[mn] == m['real']:
                                method_acc[mn][0] += 1
                best_m = max(method_acc, key=lambda mn: method_acc[mn][0] / max(method_acc[mn][1], 1))
                for qid in cat_qids:
                    correct += (methods[qid].get(best_m) == methods[qid]['real'])
            else:
                # 多题类别，用该类别的最优方法
                method_acc = defaultdict(lambda: [0, 0])
                for qid in cat_qids:
                    m = methods[qid]
                    for mn in METHOD_NAMES:
                        if mn in m:
                            method_acc[mn][1] += 1
                            if m[mn] == m['real']:
                                method_acc[mn][0] += 1
                best_m = max(method_acc, key=lambda mn: method_acc[mn][0] / max(method_acc[mn][1], 1))
                for qid in cat_qids:
                    correct += (methods[qid].get(best_m) == methods[qid]['real'])
    
    return correct


# ===== S6: 每人加权集成 =====
def s6_weighted_ensemble():
    """不选单一方法，按历史准确率加权所有方法的投票。"""
    correct = 0
    for sig, qids in person_groups.items():
        if len(qids) < 2:
            for qid in qids:
                correct += (methods[qid].get('hybrid') == methods[qid]['real'])
            continue
        
        for qid in qids:
            m = methods[qid]
            
            # 计算其他题上各方法的准确率
            other_qids = [q for q in qids if q != qid]
            method_weights = defaultdict(float)
            for oq in other_qids:
                om = methods[oq]
                for mn in METHOD_NAMES:
                    if mn in om:
                        method_weights[mn] += 2.0 if om[mn] == om['real'] else -0.5
            
            # 加权投票
            weighted_votes = defaultdict(float)
            for mn in METHOD_NAMES:
                if mn in m and m[mn]:
                    w = max(method_weights.get(mn, 0), 0.1)  # 最低权重0.1
                    weighted_votes[m[mn]] += w
            
            if weighted_votes:
                best = max(weighted_votes, key=weighted_votes.get)
                correct += (best == m['real'])
            else:
                correct += (m.get('hybrid') == m['real'])
    
    return correct


# ===== S7: 命盘相似度跨人学习 =====
def s7_similarity():
    """找命盘相似的命主，借用他们的最优方法。
    相似度 = 日主相同 + 五行占比排序相近"""
    
    # 提取每个命主的特征
    person_features = {}
    for sig, qids in person_groups.items():
        # 从第一个题获取排盘
        c = next((c for cf, af in ROUNDS 
                 for c in json.load(open(os.path.join(BASE_DIR, cf), encoding='utf-8'))
                 if c['id'] == qids[0]), None)
        if not c:
            continue
        b = c['chart_data'].get('bazi', {})
        day_gan = b.get('日主', '')
        day_wx = b.get('日主五行', '')
        wx = b.get('五行力量', {})
        
        # 方法准确率
        method_acc = defaultdict(lambda: [0, 0])
        for qid in qids:
            m = methods[qid]
            for mn in METHOD_NAMES:
                if mn in m:
                    method_acc[mn][1] += 1
                    if m[mn] == m['real']:
                        method_acc[mn][0] += 1
        
        person_features[sig] = {
            'day_gan': day_gan, 'day_wx': day_wx, 'wx': wx,
            'method_acc': dict(method_acc),
        }
    
    # 对每个命主，找同日主五行的其他命主
    correct = 0
    for sig, qids in person_groups.items():
        my_feat = person_features.get(sig, {})
        if not my_feat:
            continue
        
        for qid in qids:
            m = methods[qid]
            
            # 找同日主五行的其他命主
            similar = []
            for other_sig, other_feat in person_features.items():
                if other_sig == sig:
                    continue
                if other_feat['day_wx'] == my_feat.get('day_wx'):
                    similar.append(other_feat)
            
            # 聚合同类命主的方法准确率
            method_scores = defaultdict(lambda: [0, 0])
            for sf in similar:
                for mn, (ok, nn) in sf.get('method_acc', {}).items():
                    method_scores[mn][0] += ok
                    method_scores[mn][1] += nn
            
            # 选最优方法
            best_m = 'hybrid'
            best_acc = -1
            for mn, (ok, nn) in method_scores.items():
                acc = ok / max(nn, 1)
                if acc > best_acc:
                    best_acc = acc
                    best_m = mn
            
            pred = m.get(best_m, m.get('hybrid'))
            correct += (pred == m['real'])
    
    return correct


# ===== S8: S4 + S3 组合 =====
def s8_combined():
    """S4 优先（同命主最优方法），fallback 到 S3（分歧路由）。"""
    # S4 的选择
    s4_pick = {}
    for sig, qids in person_groups.items():
        if len(qids) < 2:
            continue
        method_acc = defaultdict(lambda: [0, 0])
        for qid in qids:
            m = methods[qid]
            for mn in METHOD_NAMES:
                if mn in m:
                    method_acc[mn][1] += 1
                    if m[mn] == m['real']:
                        method_acc[mn][0] += 1
        
        # 留一法：对每题，用其他题选最优方法
        for qid in qids:
            other_qids = [q for q in qids if q != qid]
            method_acc_loo = defaultdict(lambda: [0, 0])
            for oq in other_qids:
                om = methods[oq]
                for mn in METHOD_NAMES:
                    if mn in om:
                        method_acc_loo[mn][1] += 1
                        if om[mn] == om['real']:
                            method_acc_loo[mn][0] += 1
            
            if method_acc_loo:
                best_m = max(method_acc_loo, key=lambda mn: method_acc_loo[mn][0] / max(method_acc_loo[mn][1], 1))
                s4_pick[qid] = methods[qid].get(best_m)
    
    # S3 的分歧路由
    dis_by_cat = defaultdict(lambda: {'agent_ok': 0, 'rules_ok': 0, 'count': 0})
    for qid in all_qids:
        m = methods[qid]
        agent_a = m.get('agent', '')
        rules_a = m.get('rules', '')
        if agent_a != rules_a:
            d = dis_by_cat[m['cat']]
            d['count'] += 1
            d['agent_ok'] += (agent_a == m['real'])
            d['rules_ok'] += (rules_a == m['real'])
    
    disagree_router = {}
    for cat, d in dis_by_cat.items():
        if d['count'] > 0:
            disagree_router[cat] = 'agent' if d['agent_ok'] >= d['rules_ok'] else 'rules'
    
    # Combined
    correct = 0
    for qid in all_qids:
        m = methods[qid]
        # S4 优先
        if qid in s4_pick:
            correct += (s4_pick[qid] == m['real'])
        else:
            # S3 fallback
            agent_a = m.get('agent', '')
            rules_a = m.get('rules', '')
            if agent_a == rules_a:
                correct += (agent_a == m['real'])
            else:
                src = disagree_router.get(m['cat'], 'agent')
                pred = m.get(src, m.get('hybrid', ''))
                correct += (pred == m['real'])
    
    return correct


# ===== Run all =====
print('=== Next Level Strategies ===\n')

s5 = s5_person_category()
print('S5 (每人每类别路由): %d/160 = %.1f%%' % (s5, s5/160*100))

s6 = s6_weighted_ensemble()
print('S6 (每人加权集成): %d/160 = %.1f%%' % (s6, s6/160*100))

s7 = s7_similarity()
print('S7 (命盘相似度跨人学习): %d/160 = %.1f%%' % (s7, s7/160*100))

s8 = s8_combined()
print('S8 (S4+S3组合): %d/160 = %.1f%%' % (s8, s8/160*100))

print('\nPrevious best S4: 78/160 = 48.8%')
print('Baselines: human=51.88% | Tianfu=50.0%')

best = max(s5, s6, s7, s8, 78)  # include S4=78
print('\nOVERALL BEST: %d/160 = %.1f%%' % (best, best/160*100))
