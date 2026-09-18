# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
import tools
from tools.calendar_engine import year_ganzhi, build_four_pillars

expect = {1984: '甲子', 1995: '乙亥', 1997: '丁丑', 2003: '癸未',
          2004: '甲申', 2010: '庚寅', 2020: '庚子', 2021: '辛丑'}
ok = True
for y, gz in expect.items():
    got = year_ganzhi(y)
    flag = 'OK' if got == gz else 'FAIL'
    if got != gz:
        ok = False
    print('liunian %d -> %s (expect %s) %s' % (y, got, gz, flag))

c1 = build_four_pillars(1984, 12, 9, 17, '女')
print('natal 1984-12-09 year pillar:', c1['四柱']['年柱'], '(expect 甲子)')

c2 = build_four_pillars(1984, 1, 10, 12, '男')
print('natal 1984-01-10 year pillar:', c2['四柱']['年柱'], '(expect 癸亥)')

print('ALL OK' if ok else 'HAS FAIL')
