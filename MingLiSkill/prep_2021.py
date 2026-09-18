# -*- coding: utf-8 -*-
"""Run full pipeline on 40 new 2021 questions. Answers committed BEFORE scoring."""
import io, sys, json, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from tools import HybridMingliToolkit
from extra_tools import auto_yongshen
from tools.shensha import natal_shensha, year_shensha

HTK = HybridMingliToolkit()

questions = json.load(open(r'E:\ming_li_skill\MingLiSkill\new_bench\bench2021_questions.json', encoding='utf-8'))

# Group by person
persons = {}
for qq in questions:
    pid = qq['person_id']
    if pid not in persons:
        persons[pid] = {'birth': qq['birth'], 'gender': qq['gender'], 'questions': []}
    persons[pid]['questions'].append(qq)

print('persons: %d, total questions: %d' % (len(persons), len(questions)))

# Generate charts for each person
results = []
for pid, pdata in sorted(persons.items()):
    b = pdata['birth']
    gender = pdata['gender']
    g = '男' if gender == 'male' else '女'
    try:
        r = HTK.analyze_question(
            year=b['year'], month=b['month'], day=b['day'],
            hour=b.get('hour', 12), gender=g,
            category='综合', question='综合分析',
            options_json='[]')
        chart = json.loads(r)
    except Exception as e:
        print('chart error for %s: %s' % (pid, e))
        continue
    
    bazi = chart.get('bazi', {})
    ziwei = chart.get('ziwei', {})
    pillars = bazi.get('四柱', {})
    
    # 神煞
    yz = pillars.get('年柱', '')[-1:]
    dz = pillars.get('日柱', '')[-1:]
    dg = bazi.get('日主', '')
    natal = natal_shensha(yz, dz, dg)
    
    # 用神
    ys = auto_yongshen('综合', bazi)
    
    # Same-chart cases from 160
    from retriever import Retriever
    ret = Retriever()
    sibs = ret.same_chart_cases(pillars)
    
    print('\n=== %s (%s %d-%02d-%02d) ===' % (pid[:20], g, b['year'], b['month'], b['day']))
    print('四柱: %s' % json.dumps(pillars, ensure_ascii=False))
    print('日主: %s(%s) %s | 喜:%s 忌:%s' % (bazi.get('日主'), bazi.get('日主五行'), bazi.get('日主强弱'), bazi.get('喜用神'), bazi.get('忌神')))
    print('五行: %s' % json.dumps(bazi.get('五行力量', {}), ensure_ascii=False))
    print('神煞: %s' % json.dumps(natal['positions'], ensure_ascii=False))
    if sibs:
        print('案例线: %s' % '; '.join('%s[%s]=%s' % (s['qid'], s['cat'], s['answer']) for s in sibs[:4]))
    
    # For each question, output the question and options for manual reasoning
    for qq in pdata['questions']:
        print('\n  %s: %s' % (qq['question_id'], qq['question'][:60]))
        for o in qq['options']:
            if isinstance(o, dict):
                print('    %s. %s' % (o.get('letter', '?'), str(o.get('text', ''))[:60]))
            elif isinstance(o, str):
                print('    %s' % o[:60])

# Save questions WITHOUT answers for blind answering
blind = []
for qq in questions:
    blind.append({
        'question_id': qq['question_id'],
        'person_id': qq['person_id'],
        'question': qq['question'],
        'options': qq['options'],
    })
with open(r'E:\ming_li_skill\MingLiSkill\new_bench\bench2021_blind.json', 'w', encoding='utf-8') as f:
    json.dump(blind, f, ensure_ascii=False, indent=1)
print('\nsaved bench2021_blind.json (%d questions, no answers)' % len(blind))
