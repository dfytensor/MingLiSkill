# -*- coding: utf-8 -*-
"""dump_charts_1419.py — 2019/2020 全部命例紧凑排盘"""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from tools import HybridMingliToolkit
from tools.ziwei_tools import ZiweiToolkit

HTK = HybridMingliToolkit()
ZT = ZiweiToolkit()

PERSONS = [
    ('2020-P1', '女', 1962, 4, 4, 9, '香港'),
    ('2020-P2', '女', 1979, 3, 1, 23, '广州'),
    ('2020-P3', '女', 1985, 3, 15, 11, '香港'),
    ('2020-P4', '男', 1979, 7, 21, 5, '香港'),
    ('2020-P5', '女', 1986, 5, 6, 11, '香港'),
    ('2020-P6', '女', 1962, 6, 16, 13, '马来西亚'),
    ('2020-P7', '女', 1993, 11, 25, 15, '广西'),
    ('2019-P1', '男', 1982, 1, 23, 1, '台湾'),
    ('2019-P2', '男', 1987, 7, 10, 17, '马来西亚'),
    ('2019-P3', '女', 1984, 12, 28, 7, '大陆'),
    ('2019-P4', '女', 1971, 5, 28, 1, '香港'),
    ('2019-P5', '女', 1962, 8, 26, 3, '香港'),
    ('2019-P6', '女', 1977, 4, 30, 13, '香港'),
    ('2019-P7', '女', 1986, 7, 23, 3, '香港'),
]

out = []
for pid, g, y, mo, d, h, loc in PERSONS:
    out.append('\n=== %s: %s %d-%02d-%02d %02d时 %s ===' % (pid, g, y, mo, d, h, loc))
    try:
        r = HTK.analyze_question(year=y, month=mo, day=d, hour=h, gender=g,
            category='', question='x', options_json='[]')
        b = json.loads(r).get('bazi', {})
        pillars = b.get('四柱', {})
        wx = b.get('五行力量', {})
        tot = sum(wx.values()) or 1
        ss = b.get('十神', {})
        out.append('四柱: %s | 日主=%s(%s) %s' % (pillars, b.get('日主'), b.get('日主五行'), b.get('日主强弱')))
        out.append('五行%: %s' % ' '.join('%s=%.0f' % (k, v/tot*100) for k, v in wx.items()))
        tg = sorted(set(v for k, v in ss.items() if '天干' in k))
        ssc = {}
        for v in ss.values(): ssc[v] = ssc.get(v, 0) + 1
        out.append('透干: %s | 十神计数: %s' % (tg, json.dumps(ssc, ensure_ascii=False)))
    except Exception as e:
        out.append('bazi ERR %s' % e)
    try:
        r2 = ZT.paipan(year=y, month=mo, day=d, hour=h, gender=g)
        zw = json.loads(r2).get('十二宫', {})
        stars = []
        for pn in ['命宫','夫妻','财帛','官禄','福德','疾厄','子女','父母','兄弟','迁移','田宅']:
            p = zw.get(pn)
            if p:
                st = p.get('主星', []) if isinstance(p, dict) else p
                if st: stars.append('%s:%s' % (pn, '/'.join(st)))
        out.append('紫微: %s' % ' '.join(stars))
    except Exception as e:
        out.append('ziwei ERR %s' % e)

open(r'E:\ming_li_skill\MingLiSkill\charts1419.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('written, persons: %d' % len(PERSONS))
