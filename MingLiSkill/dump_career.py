# -*- coding: utf-8 -*-
"""Dump wrong questions for career/personality/academy/children."""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from tools.ziwei_tools import ZiweiToolkit
from tools import HybridMingliToolkit

ZT = ZiweiToolkit()
HTK = HybridMingliToolkit()
data = json.load(open(r'F:\牛逼模型\MingLi-Bench\data\data.json', encoding='utf-8'))
by_id = {q['id']: q for q in data['questions']}
BASE = json.load(open(r'E:\ming_li_skill\MingLiSkill\fixed_answers_v5.json', encoding='utf-8'))

TARGET = ['事业', '性格', '学业', '子女']
out = []
n = 0
for qid in sorted(BASE):
    q = by_id.get(qid)
    if not q or q['category'] not in TARGET: continue
    my = BASE[qid]; real = q['answer']
    if my == real: continue
    n += 1
    bi = q['birth_info']
    out.append('\n' + '='*70)
    out.append('[%s|%s] my=%s real=%s' % (qid, q['category'], my, real))
    out.append('Q: %s' % q['question'])
    for o in q['options']:
        mk = (' <REAL>' if o['letter'] == real else '') + (' <MY>' if o['letter'] == my else '')
        out.append('  %s. %s%s' % (o['letter'], o['text'], mk))
    out.append('Birth: %s %d-%02d-%02d %02d时' % (bi['gender'], bi['year'], bi['month'], bi['day'], bi.get('hour',12)))
    try:
        r = HTK.analyze_question(year=bi['year'], month=bi['month'], day=bi['day'],
            hour=bi.get('hour',12), gender=bi['gender'], category=q['category'],
            question=q['question'], options_json=json.dumps(q['options'], ensure_ascii=False))
        b = json.loads(r).get('bazi', {})
        pillars = b.get('四柱', {})
        wx = b.get('五行力量', {})
        tot = sum(wx.values()) or 1
        ss = b.get('十神', {})
        out.append('BAZI: 日主=%s(%s) %s' % (b.get('日主'), b.get('日主五行'), b.get('日主强弱')))
        out.append('  四柱: %s' % pillars)
        out.append('  五行%: %s' % ' '.join('%s=%.0f' % (k, v/tot*100) for k, v in wx.items()))
        tg = sorted(set(v for k, v in ss.items() if '天干' in k))
        out.append('  透干十神: %s' % tg)
    except Exception as e:
        out.append('  bazi ERR: %s' % e)
    try:
        r2 = ZT.paipan(year=bi['year'], month=bi['month'], day=bi['day'],
                       hour=bi.get('hour',12), gender=bi['gender'])
        zw = json.loads(r2).get('十二宫', {})
        for pn in ['命宫','官禄','财帛','福德','子女','父母','疾厄']:
            p = zw.get(pn)
            if p:
                st = p.get('主星', []) if isinstance(p, dict) else p
                if st: out.append('  紫微%s: %s' % (pn, st))
    except Exception as e:
        out.append('  ziwei ERR: %s' % e)

open(r'E:\ming_li_skill\MingLiSkill\career_deep.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('questions: %d' % n)
