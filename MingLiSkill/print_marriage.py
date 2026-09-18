# -*- coding: utf-8 -*-
"""Print FULL data for all marriage questions for careful LLM analysis."""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from tools.ziwei_tools import ZiweiToolkit
from tools import HybridMingliToolkit

ZT = ZiweiToolkit()
HTK = HybridMingliToolkit()

data = json.load(open(r'F:\牛逼模型\MingLi-Bench\data\data.json', encoding='utf-8'))
by_id = {q['id']: q for q in data['questions']}

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
    for k, v in json.load(open(f, encoding='utf-8')).items():
        BASE.setdefault(k, getletter(v))

# Use fixed answers (fix A/B already applied)
try:
    BASE = json.load(open(r'E:\ming_li_skill\MingLiSkill\fixed_answers.json', encoding='utf-8'))
except:
    pass

# Marriage questions = category 婚姻 OR question text about marriage
marriage_qs = []
for q in data['questions']:
    qid = q['id']
    if qid not in BASE:
        continue
    text = q['question'] + ' '.join(o['text'] for o in q['options'])
    is_mar = q['category'] == '婚姻' or any(k in q['question'] for k in ['婚姻','结婚','夫妻','离婚','丈夫','妻子','嫁','娶'])
    if is_mar:
        marriage_qs.append(q)

print('marriage questions found: %d' % len(marriage_qs))

out = []
for q in marriage_qs:
    bi = q['birth_info']
    my = BASE.get(q['id'], '?')
    real = q['answer']
    status = 'OK' if my == real else 'X'
    
    out.append('\n' + '='*70)
    out.append('[%s] my=%s real=%s %s' % (q['id'], my, real, status))
    out.append('Q: %s' % q['question'])
    for o in q['options']:
        mk = ''
        if o['letter'] == real: mk += ' ◀REAL'
        if o['letter'] == my: mk += ' ◀MY'
        out.append('  %s. %s%s' % (o['letter'], o['text'], mk))
    out.append('Birth: %s %d-%02d-%02d %02d时 %s' % (bi['gender'], bi['year'], bi['month'], bi['day'], bi.get('hour',12), bi.get('location','')))
    
    # Bazi
    try:
        r = HTK.analyze_question(year=bi['year'], month=bi['month'], day=bi['day'],
            hour=bi.get('hour',12), gender=bi['gender'], category='婚姻',
            question=q['question'], options_json=json.dumps(q['options'], ensure_ascii=False))
        ch = json.loads(r)
        b = ch.get('bazi', {})
        out.append('BAZI: 日主=%s(%s) %s | 四柱=%s' % (b.get('日主'), b.get('日主五行'), b.get('日主强弱'), b.get('四柱')))
        out.append('  十神: %s' % json.dumps(b.get('十神',{}), ensure_ascii=False))
        wx = b.get('五行力量', {})
        tot = sum(wx.values()) or 1
        out.append('  五行%: %s' % ' '.join('%s=%.0f%%' % (k, v/tot*100) for k, v in wx.items()))
        out.append('  喜用=%s 忌=%s' % (b.get('喜用神'), b.get('忌神')))
        da = ch.get('detailed_analysis', {})
        gs = da.get('性别十神', {})
        if gs:
            out.append('  性别十神: %s' % json.dumps(gs, ensure_ascii=False)[:250])
    except Exception as e:
        out.append('  bazi ERR %s' % e)
    
    # Ziwei palaces
    try:
        r2 = ZT.paipan(year=bi['year'], month=bi['month'], day=bi['day'],
                       hour=bi.get('hour',12), gender=bi['gender'])
        zw = json.loads(r2)
        pal = zw.get('十二宫', {})
        for pn in ['命宫','夫妻','夫妻宫','子女','子女宫','福德','福德宫']:
            p = pal.get(pn)
            if p:
                st = p.get('主星', []) if isinstance(p, dict) else p
                out.append('  紫微%s: %s' % (pn, st))
    except Exception as e:
        out.append('  ziwei ERR %s' % e)

with open(r'E:\ming_li_skill\MingLiSkill\marriage_deep.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('written marriage_deep.txt (%d lines)' % len(out))
