# -*- coding: utf-8 -*-
"""Test the 3 fixes on the 3 wrong questions."""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from tools import HybridMingliToolkit
from tools.ziwei_tools import ZiweiToolkit
from fix_tools import analyze_fude_palace, check_guan_sha_absence

HTK = HybridMingliToolkit()
ZT = ZiweiToolkit()

CASES = [
    dict(qid='ftb_0055', bi=dict(year=1986, month=4, day=24, hour=21, gender='男'),
         expect='D', label='命理风水顾问', focus='fude'),
    dict(qid='ftb_0078', bi=dict(year=1980, month=7, day=11, hour=9, gender='男'),
         expect='B', label='物流老板', focus='tianxiang'),
    dict(qid='ftb_0016', bi=dict(year=1977, month=10, day=26, hour=11, gender='女'),
         expect='A', label='家庭主妇', focus='guansha'),
]

for c in CASES:
    bi = c['bi']
    print('='*60)
    print('%s → 应选%s(%s) | 检查: %s' % (c['qid'], c['expect'], c['label'], c['focus']))
    try:
        r = HTK.analyze_question(year=bi['year'], month=bi['month'], day=bi['day'],
            hour=bi['hour'], gender=bi['gender'], category='事业',
            question='职业', options_json='[]')
        chart = json.loads(r)
        b = chart.get('bazi', {})
        ten_gods = b.get('十神', {})
        wx = b.get('五行力量', {})
        tg = b.get('四柱', {})
        print('  日主=%s 强弱=%s' % (b.get('日主'), b.get('日主强弱')))
    except Exception as e:
        print('  bazi fail: %s' % e); ten_gods, wx = {}, {}
    
    if c['focus'] == 'guansha':
        sigs, cnt, pct = check_guan_sha_absence(ten_gods, wx)
        for s in sigs: print('  ✅ %s' % s)
        print('  官杀: %d (%.1f%%)' % (cnt, pct))
    
    if c['focus'] in ('fude',):
        try:
            r2 = ZT.paipan(year=bi['year'], month=bi['month'], day=bi['day'],
                           hour=bi['hour'], gender=bi['gender'])
            zw = json.loads(r2)
            pal = zw.get('十二宫', {})
            fd = pal.get('福德', pal.get('福德宫', {}))
            fd_stars = fd.get('主星', []) if isinstance(fd, dict) else fd
            print('  福德宫: %s' % fd_stars)
            sigs = analyze_fude_palace({k: (v.get('主星',[]) if isinstance(v,dict) else v) for k,v in pal.items()})
            for s in sigs: print('  ✅ %s' % s)
        except Exception as e:
            print('  ziwei fail: %s' % e)
    
    if c['focus'] == 'tianxiang':
        ss = set(ten_gods.values())
        print('  十神: %s' % sorted(ss))
        print('  天相在十神? %s' % ('天相' in ss))
        # 印星检查
        yin = [s for s in ss if '印' in s]
        print('  印星: %s → 天相/印星=掌印管理者' % yin)
