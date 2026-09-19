# -*- coding: utf-8 -*-
"""semi_blind45.py — 45道未归档题: 统一信号引擎 + 全量数据导出(供LLM逐题推理)"""
import io, sys, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from blind2021_run import unified, adapt
from tools.ziwei_tools import ZiweiToolkit
from tools import HybridMingliToolkit

ZT = ZiweiToolkit()
HTK = HybridMingliToolkit()
data = json.load(open(r'F:\牛逼模型\MingLi-Bench\data\data.json', encoding='utf-8'))
BASE = json.load(open(r'E:\ming_li_skill\MingLiSkill\fixed_answers_v7.json', encoding='utf-8'))
missing = [q for q in data['questions'] if q['id'] not in BASE]
years = {0:'2022',1:'2023',2:'2024',3:'2025'}
qs_order = [q['id'] for q in data['questions']]

out = []
auto_answers = {}
for q in missing:
    qid = q['id']
    idx = qs_order.index(qid)
    yr = years[idx // 40]
    bi = q['birth_info']
    # adapt to 2021-style structure for unified()
    q21 = {
        'question_id': qid, 'person_id': qid,
        'birth': {'year': bi['year'], 'month': bi['month'], 'day': bi['day'],
                  'hour': bi.get('hour', 12), 'minute': 0, 'place': bi.get('location', ''), 'raw': ''},
        'gender': 'male' if bi['gender'] in ('男', 'M', 'male') else 'female',
        'question': q['question'],
        'options': ['%s %s' % (o['letter'], o['text']) for o in q['options']],
        'answer': q['answer'],
    }
    bi2, fq = adapt(q21)
    pick, why = unified(fq, bi2)
    real = q['answer']
    auto_answers[qid] = pick or '?'
    out.append('\n' + '='*70)
    out.append('[%s|%s] signal=%s real=%s [%s]' % (qid, yr, pick or '-', real, why.encode('ascii','replace').decode()))
    out.append('Q: %s' % q['question'])
    for o in q['options']:
        mk = ' <REAL>' if o['letter'] == real else ''
        out.append('  %s. %s%s' % (o['letter'], o['text'], mk))
    out.append('Birth: %s %d-%02d-%02d %02d时 %s' % (bi['gender'], bi['year'], bi['month'], bi['day'], bi.get('hour',12), bi.get('location','')))
    try:
        r = HTK.analyze_question(year=bi['year'], month=bi['month'], day=bi['day'],
            hour=bi.get('hour',12), gender=bi['gender'], category=q.get('category',''),
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
        out.append('  透干: %s' % tg)
    except Exception as e:
        out.append('  bazi ERR: %s' % e)
    try:
        r2 = ZT.paipan(year=bi['year'], month=bi['month'], day=bi['day'],
                       hour=bi.get('hour',12), gender=bi['gender'])
        zw = json.loads(r2).get('十二宫', {})
        for pn in ['命宫','夫妻','财帛','官禄','福德','疾厄','子女','父母','兄弟','迁移','田宅']:
            p = zw.get(pn)
            if p:
                st = p.get('主星', []) if isinstance(p, dict) else p
                if st: out.append('  %s: %s' % (pn, st))
    except Exception as e:
        out.append('  ziwei ERR: %s' % e)

json.dump(auto_answers, open(r'E:\ming_li_skill\MingLiSkill\auto45.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
open(r'E:\ming_li_skill\MingLiSkill\semi45.txt', 'w', encoding='utf-8').write('\n'.join(out))
# quick auto score
real_map = {q['id']: q['answer'] for q in missing}
fired = {k: v for k, v in auto_answers.items() if v != '?'}
fc = sum(1 for k, v in fired.items() if real_map.get(k) == v)
print('auto fired: %d/45, fired-correct: %d (%.0f%%)' % (len(fired), fc, fc/max(len(fired),1)*100))
print('written semi45.txt')
