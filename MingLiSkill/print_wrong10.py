# -*- coding: utf-8 -*-
"""Print FULL tool output for 10 wrong questions so LLM can carefully analyze."""
import io, sys, json, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from tools import HybridMingliToolkit
from tools.ziwei_tools import ZiweiToolkit
from tools.bazi_tools import BaziToolkit
from tools.shensha import natal_shensha

HTK = HybridMingliToolkit()
ZT = ZiweiToolkit()
BT = BaziToolkit()

data = json.load(open(r'F:\牛逼模型\MingLi-Bench\data\data.json', encoding='utf-8'))
key = {q['id']: q for q in data['questions']}

# Pick 10 wrong questions from different categories
WRONG = [
    'ftb_0016',  # 事业
    'ftb_0055',  # 事业
    'ftb_0078',  # 事业
    'ftb_0013',  # 婚姻
    'ftb_0044',  # 婚姻
    'ftb_0077',  # 婚姻
    'ftb_0001',  # 健康
    'ftb_0060',  # 健康
    'ftb_0030',  # 财运
    'ftb_0117',  # 家庭
]

out = []
for qid in WRONG:
    q = key[qid]
    bi = q['birth_info']
    real = q['answer']
    
    out.append('\n' + '='*70)
    out.append('Q: %s | Real: %s' % (q['question'][:60], real))
    out.append('Birth: %s %d-%02d-%02d %02d时 %s' % (bi['gender'], bi['year'], bi['month'], bi['day'], bi.get('hour',12), bi.get('location','')))
    for o in q['options']:
        marker = ' ◀◀' if o['letter'] == real else ''
        out.append('  %s. %s%s' % (o['letter'], o['text'][:60], marker))
    
    # TOOL 1: Full analyze_question (includes detailed_analysis now)
    try:
        r = HTK.analyze_question(
            year=bi['year'], month=bi['month'], day=bi['day'],
            hour=bi.get('hour', 12), gender=bi['gender'],
            category=q['category'], question=q['question'],
            options_json=json.dumps(q['options'], ensure_ascii=False))
        chart = json.loads(r)
    except:
        chart = {}
    
    b = chart.get('bazi', {})
    da = chart.get('detailed_analysis', {})
    z = chart.get('ziwei', {})
    
    # 十神详表
    ss_detail = da.get('十神详表', {})
    if ss_detail:
        out.append('\n  [十神详表]')
        for ss_name, positions in ss_detail.items():
            strength = len(positions) + sum(1 for p in positions if p.get('有根'))
            out.append('    %s (力%.0f):' % (ss_name, strength))
            for p in positions:
                out.append('      %s 干=%s 根=%s 行=%s 透=%s' % (
                    p['位置'], p['天干'], p['有根'], p['五行'], p['透干']))
    
    # 五行平衡
    wx_bal = da.get('五行平衡', {})
    if wx_bal:
        out.append('  [五行平衡]')
        for w, d in wx_bal.items():
            out.append('    %s: %s%% %s (%s)' % (w, d['占比'], d['状态'], d['脏腑']))
    
    # 性别十神
    gender_ss = da.get('性别十神', {})
    if gender_ss:
        out.append('  [性别十神]')
        out.append('    %s' % json.dumps(gender_ss, ensure_ascii=False)[:200])
    
    # TOOL 2: Ziwei full
    try:
        r2 = ZT.paipan(year=bi['year'], month=bi['month'], day=bi['day'],
                       hour=bi.get('hour', 12), gender=bi['gender'])
        zw = json.loads(r2)
        zw_palaces = zw.get('十二宫', {})
        out.append('  [紫微12宫]')
        for palace, pdata in zw_palaces.items():
            stars = pdata.get('主星', [])
            if stars:
                out.append('    %s(%s): %s' % (palace, pdata.get('宫位地支',''), ', '.join(stars)))
    except:
        pass
    
    # TOOL 3: BaziToolkit career analysis
    try:
        pillars = b.get('四柱', {})
        r3 = BT.analyze_career(pillars, bi['gender'])
        c3 = json.loads(r3)
        if c3.get('success'):
            out.append('  [BaziToolkit事业分析]')
            out.append('    %s' % json.dumps(c3, ensure_ascii=False)[:300])
    except:
        pass
    
    # TOOL 4: BaziToolkit marriage analysis
    try:
        r4 = BT.analyze_marriage(pillars, bi['gender'])
        c4 = json.loads(r4)
        if c4.get('success'):
            out.append('  [BaziToolkit婚姻分析]')
            out.append('    %s' % json.dumps(c4, ensure_ascii=False)[:300])
    except:
        pass

with open(r'E:\ming_li_skill\MingLiSkill\wrong10_analysis.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('written %d lines' % len(out))
