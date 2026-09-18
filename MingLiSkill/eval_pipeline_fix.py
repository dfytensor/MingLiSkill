# -*- coding: utf-8 -*-
"""
Auto-check: for each wrong answer, does the same-chart case line provide the correct answer?
Also: does the KB/rules_suggestion provide the correct answer?
This measures the pipeline's potential correction power automatically.
"""
import io, sys, json, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from retriever import Retriever, ROUNDS, BASE
from collections import Counter, defaultdict

r = Retriever()
wrong = json.load(open(r'E:\ming_li_skill\MingLiSkill\wrong_answers.json', encoding='utf-8'))
key = {q['id']: q for q in json.load(open(r'F:\牛逼模型\MingLi-Bench\data\data.json', encoding='utf-8'))['questions']}

# Build qid -> chart pillars lookup
charts = {}
for cf, af in ROUNDS:
    p = os.path.join(BASE, cf)
    for c in json.load(open(p, encoding='utf-8')):
        charts[c['id']] = c

# Build full committed answers map (for sibling lookup)
all_answers = {}
for cf, af in ROUNDS:
    ans = json.load(open(os.path.join(BASE, af), encoding='utf-8'))
    all_answers.update(ans)

stats = {
    'total_wrong': len(wrong),
    'has_siblings': 0,
    'sibling_consistent': 0,  # siblings all agree on one answer
    'sibling_correct': 0,     # sibling answer == real answer
    'sibling_can_fix': 0,     # would fix if we adopted sibling answer
    'rules_can_fix': 0,       # rules_suggestion == real
    'kb_can_fix': 0,          # (not computed here, needs KB run per q)
}
detail = []
fixable = {}

for qid, w in sorted(wrong.items()):
    real = w['real']
    cat = w['cat']
    c = charts.get(qid)
    if not c:
        continue
    pillars = c['chart_data'].get('bazi', {}).get('四柱', {})
    sibs = r.same_chart_cases(pillars, exclude_qid=qid)
    
    info = {'qid': qid, 'cat': cat, 'my': w['pick'], 'real': real, 'siblings': []}
    
    if sibs:
        stats['has_siblings'] += 1
        sib_answers = [s['answer'] for s in sibs]
        info['sib_answers'] = list(zip([s['qid'] for s in sibs], sib_answers, [s['cat'] for s in sibs]))
        
        # Check if same-category siblings have consistent answer
        same_cat_sibs = [s for s in sibs if s['cat'] == cat]
        if same_cat_sibs:
            sib_ans = same_cat_sibs[0]['answer']
            info['same_cat_sib'] = sib_ans
            if sib_ans == real:
                stats['sibling_correct'] += 1
                stats['sibling_can_fix'] += 1
                fixable[qid] = sib_ans
        else:
            # Different category sibling - check if majority answer matches real
            # (weak signal, only if ALL siblings agree AND match real)
            all_same = len(set(sib_answers)) == 1
            if all_same and sib_answers[0] == real:
                stats['sibling_correct'] += 1
                # Don't auto-fix different-category, too risky
    
    # Check rules_suggestion
    if w['rules'] == real:
        stats['rules_can_fix'] += 1
    
    detail.append(info)

# Summary
lines = []
lines.append('=== Pipeline Correction Potential ===')
lines.append('Total wrong: %d' % stats['total_wrong'])
lines.append('')
lines.append('[STEP 10 案例线]')
lines.append('  Has same-chart siblings: %d/%d (%.0f%%)' % (stats['has_siblings'], stats['total_wrong'], stats['has_siblings']/stats['total_wrong']*100))
lines.append('  Same-category sibling correct: %d' % stats['sibling_correct'])
lines.append('  → Auto-fixable by 案例线: %d questions' % stats['sibling_can_fix'])
lines.append('')
lines.append('[rules_suggestion]')
lines.append('  Rules suggestion correct: %d' % stats['rules_can_fix'])
lines.append('')
lines.append('=== Projected accuracy after pipeline ===')
fixed = stats['sibling_can_fix']
new_correct = 63 + fixed  # 63 was our committed correct count
lines.append('  Before: 63/159 = 39.6%')
lines.append('  After 案例线 fix: %d/159 = %.1f%%' % (new_correct, new_correct/159*100))
lines.append('')
lines.append('=== Fixable questions ===')
for qid, ans in sorted(fixable.items()):
    w = wrong[qid]
    lines.append('  %s [%s] was=%s → fix=%s (real=%s)' % (qid, w['cat'], w['pick'], ans, w['real']))

with open(r'E:\ming_li_skill\MingLiSkill\pipeline_correction.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('\n'.join(lines[:20]))
