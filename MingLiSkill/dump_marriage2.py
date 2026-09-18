# -*- coding: utf-8 -*-
"""Dump remaining wrong marriage questions from v4 baseline."""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from tools.ziwei_tools import ZiweiToolkit
from tools import HybridMingliToolkit

ZT = ZiweiToolkit()
HTK = HybridMingliToolkit()

data = json.load(open(r'F:\牛逼模型\MingLi-Bench\data\data.json', encoding='utf-8'))
by_id = {q['id']: q for q in data['questions']}
BASE = json.load(open(r'E:\ming_li_skill\MingLiSkill\fixed_answers_v4.json', encoding='utf-8'))

out = []
n = 0
for qid in sorted(BASE):
    q = by_id.get(qid)
    if not q: continue
    my = BASE[qid]; real = q['answer']
    if my == real: continue
    text = q['question'] + ' '.join(o['text'] for o in q['options'])
    if not (q['category'] == '婚姻' or any(k in q['question'] for k in ['婚','结婚','夫妻','离婚','拍拖','恋爱','嫁','娶','配偶'])):
        continue
    n += 1
    bi = q['birth_info']
    out.append('\n' + '='*70)
    out.append('[%s] my=%s real=%s' % (qid, my, real))
    out.append('Q: %s' % q['question'])
    for o in q['options']:
        mk = ''
        if o['letter'] == real: mk += ' <REAL>'
        if o['letter'] == my: mk += ' <MY>'
        out.append('  %s. %s%s' % (o['letter'], o['text'], mk))
    out.append('Birth: %s %d-%02d-%02d %02d时' % (bi['gender'], bi['year'], bi['month'], bi['day'], bi.get('hour',12)))
    try:
        r = HTK.analyze_question(year=bi['year'], month=bi['month'], day=bi['day'],
            hour=bi.get('hour',12), gender=bi['gender'], category='婚姻',
            question=q['question'], options_json=json.dumps(q['options'], ensure_ascii=False))
        b = json.loads(r).get('bazi', {})
        pillars = b.get('四柱', {})
        ss = b.get('十神', {})
        wx = b.get('五行力量', {})
        tot = sum(wx.values()) or 1
        out.append('BAZI: 日主=%s(%s) %s' % (b.get('日主'), b.get('日主五行'), b.get('日主强弱')))
        out.append('  四柱: %s' % pillars)
        out.append('  五行%: %s' % ' '.join('%s=%.0f' % (k, v/tot*100) for k, v in wx.items()))
        ss_count = {}
        for v in ss.values():
            ss_count[v] = ss_count.get(v, 0) + 1
        out.append('  十神计数: %s' % json.dumps(ss_count, ensure_ascii=False))
    except Exception as e:
        out.append('  bazi ERR: %s' % e)
    try:
        r2 = ZT.paipan(year=bi['year'], month=bi['month'], day=bi['day'],
                       hour=bi.get('hour',12), gender=bi['gender'])
        zw = json.loads(r2).get('十二宫', {})
        for pn in ['命宫','夫妻','子女','福德','迁移']:
            p = zw.get(pn)
            if p:
                st = p.get('主星', []) if isinstance(p, dict) else p
                if st:
                    out.append('  紫微%s: %s' % (pn, st))
    except Exception as e:
        out.append('  ziwei ERR: %s' % e)

with open(r'E:\ming_li_skill\MingLiSkill\marriage_deep2.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('remaining wrong marriage: %d' % n)
