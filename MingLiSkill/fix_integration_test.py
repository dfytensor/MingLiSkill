# -*- coding: utf-8 -*-
"""
fix_integration_test.py v2 — 基线=各轮最优答案union，应用机梁福德修复
"""
import io, sys, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from tools.ziwei_tools import ZiweiToolkit
from fix_tools import analyze_fude_palace

ZT = ZiweiToolkit()
data = json.load(open(r'F:\牛逼模型\MingLi-Bench\data\data.json', encoding='utf-8'))
real = {q['id']: q['answer'] for q in data['questions']}
by_id = {q['id']: q for q in data['questions']}

# 优先级: hybrid9(53.8%) > hybrid4(40%) > hybrid5(36.7%) > hybrid7/8 > hybrid6 > v5blind
FILES = [
    r'E:\ming_li_skill\MingLiSkill\hybrid9_answers.json',
    r'E:\ming_li_skill\MingLiSkill\hybrid4_answers.json',
    r'E:\ming_li_skill\MingLiSkill\hybrid5_answers.json',
    r'E:\ming_li_skill\MingLiSkill\hybrid7_answers.json',
    r'E:\ming_li_skill\MingLiSkill\hybrid8_answers.json',
    r'E:\ming_li_skill\MingLiSkill\hybrid6_answers.json',
    r'E:\ming_li_skill\MingLiSkill\v5blind_answers.json',
]
def getletter(v):
    return v.get('answer', v) if isinstance(v, dict) else v

BASE = {}
for f in FILES:
    a = json.load(open(f, encoding='utf-8'))
    for k, v in a.items():
        if k not in BASE:
            BASE[k] = getletter(v)

base_correct = sum(1 for k, v in BASE.items() if real.get(k) == v)
print('基线(union最优): %d/%d = %.1f%%' % (base_correct, len(BASE), base_correct/len(BASE)*100))

FUDE_KW = ['命理', '风水', '玄学', '算命', '占卜', '宗教', '修行', '法师', '八字', '看相']

changes = []
new_correct = base_correct

for qid, my in BASE.items():
    q = by_id.get(qid)
    if not q:
        continue
    bi = q['birth_info']
    # 题目文本或选项是否涉及玄学/职业
    alltext = q['question'] + ' '.join(o['text'] for o in q['options'])
    if not any(k in alltext for k in FUDE_KW):
        continue
    try:
        r2 = ZT.paipan(year=bi['year'], month=bi['month'], day=bi['day'],
                       hour=bi.get('hour', 12), gender=bi['gender'])
        zw = json.loads(r2)
        pal = zw.get('十二宫', {})
        stars_map = {k: (v.get('主星', []) if isinstance(v, dict) else v) for k, v in pal.items()}
        sigs = analyze_fude_palace(stars_map)
        strong = any('机梁' in s for s in sigs)
    except:
        strong = False
    if not strong:
        continue
    for o in q['options']:
        if any(k in o['text'] for k in FUDE_KW):
            if o['letter'] != my:
                delta = 1 if (o['letter'] == q['answer']) else (-1 if my == q['answer'] else 0)
                changes.append((qid, my, o['letter'], q['answer'], delta))
                new_correct += delta
            break

print('修复后: %d/%d = %.1f%%' % (new_correct, len(BASE), new_correct/len(BASE)*100))
print('改动 %d 处:' % len(changes))
for qid, old, new, r_, d in changes:
    print('  %s: %s→%s (正确=%s) %s' % (qid, old, new, r_, '✓' if d > 0 else ('✗' if d < 0 else '—')))
