# -*- coding: utf-8 -*-
"""Dump all 40 2021 questions with full data for reverse-mining."""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from tools.ziwei_tools import ZiweiToolkit
from tools import HybridMingliToolkit

ZT = ZiweiToolkit()
HTK = HybridMingliToolkit()
qs = json.load(open(r'E:\ming_li_skill\MingLiSkill\new_bench\bench2021_questions.json', encoding='utf-8'))

out = []
for q21 in qs:
    bi = q21['birth']
    gender = '男' if q21['gender'] == 'male' else '女'
    out.append('\n' + '='*70)
    out.append('[%s] real=%s' % (q21['question_id'], q21['answer']))
    out.append('Q: %s' % q21['question'])
    for txt in q21['options']:
        out.append('  %s' % txt)
    out.append('Birth: %s %d-%02d-%02d %02d时' % (gender, bi['year'], bi['month'], bi['day'], bi.get('hour',12)))
    try:
        r = HTK.analyze_question(year=bi['year'], month=bi['month'], day=bi['day'],
            hour=bi.get('hour',12), gender=gender, category='',
            question=q21['question'], options_json=json.dumps(q21['options'], ensure_ascii=False))
        b = json.loads(r).get('bazi', {})
        pillars = b.get('四柱', {})
        wx = b.get('五行力量', {})
        tot = sum(wx.values()) or 1
        ss = b.get('十神', {})
        out.append('BAZI: 日主=%s(%s) %s' % (b.get('日主'), b.get('日主五行'), b.get('日主强弱')))
        out.append('  四柱: %s' % pillars)
        out.append('  五行%: %s' % ' '.join('%s=%.0f' % (k, v/tot*100) for k, v in wx.items()))
        tg = sorted(set(v for k, v in ss.items() if '天干' in k))
        out.append('  透干: %s' % tg)
        ss_count = {}
        for v in ss.values():
            ss_count[v] = ss_count.get(v, 0) + 1
        out.append('  十神计数: %s' % json.dumps(ss_count, ensure_ascii=False))
    except Exception as e:
        out.append('  bazi ERR: %s' % e)
    try:
        r2 = ZT.paipan(year=bi['year'], month=bi['month'], day=bi['day'],
                       hour=bi.get('hour',12), gender=gender)
        zw = json.loads(r2).get('十二宫', {})
        for pn in ['命宫','夫妻','财帛','官禄','福德','疾厄','子女','迁移','田宅','父母','兄弟']:
            p = zw.get(pn)
            if p:
                st = p.get('主星', []) if isinstance(p, dict) else p
                if st: out.append('  %s: %s' % (pn, st))
    except Exception as e:
        out.append('  ziwei ERR: %s' % e)

open(r'E:\ming_li_skill\MingLiSkill\b21_all.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('written %d questions' % len(qs))
