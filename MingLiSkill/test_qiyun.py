# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
import tools
from tools.calendar_engine import build_dayun_real
out = []
cases = [
    ('1981-06-17 male (yin-year, reverse)', '男', '辛酉', '甲午', 1981, 6, 17),
    ('1990-05-23 female (yang-year, reverse)', '女', '庚午', '辛巳', 1990, 5, 23),
    ('1974-04-28 male (yang-year, forward)', '男', '甲寅', '戊辰', 1974, 4, 28),
    ('1961-12-30 male (yin-year, reverse)', '男', '辛丑', '庚子', 1961, 12, 30),
    ('1983-03-26 female (yin? 癸亥 yin-year, female->forward)', '女', '癸亥', '乙卯', 1983, 3, 26),
]
for label, g, ygz, mgz, y, m, d in cases:
    dl, sa = build_dayun_real(g, ygz, mgz, y, m, d)
    out.append('%s start_age=%.1f first3=%s' % (label, sa, [(x['大运'], x['起运年龄']) for x in dl[:3]]))
with open(r'C:\Users\Administrator\AppData\Local\Temp\opencode\qiyun_test.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('ok')
