# -*- coding: utf-8 -*-
"""Tool maturity audit: actually call each tool, check output quality."""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')

out = []

# ============ 1. ZiweiToolkit 排盘 ============
from tools.ziwei_tools import ZiweiToolkit
zt = ZiweiToolkit()
try:
    r = zt.paipan(year=1990, month=6, day=15, hour=12, gender='男')
    d = json.loads(r)
    out.append('=== 1. ZiweiToolkit.paipan ===')
    out.append('status: %s' % ('OK' if d else 'EMPTY'))
    out.append('keys: %s' % list(d.keys())[:10])
    # Check if palaces have real star data
    if 'palaces' in str(d.keys()) or '命宫' in str(d.keys()):
        out.append('has palace data: YES')
    # Show raw output structure
    out.append('raw output (first 500 chars): %s' % r[:500])
except Exception as e:
    out.append('=== 1. ZiweiToolkit.paipan: FAIL ===')
    out.append('Error: %s' % e)

# ============ 2. ZiweiToolkit.analyze_palace ============
try:
    r2 = zt.analyze_palace('命宫', json.dumps(['紫微', '天府']))
    out.append('\n=== 2. analyze_palace(命宫, [紫微,天府]) ===')
    out.append('output (first 400 chars): %s' % r2[:400])
except Exception as e:
    out.append('\n=== 2. analyze_palace: FAIL ===')
    out.append('Error: %s' % e)

# ============ 3. ZiweiToolkit.analyze_career ============
try:
    r3 = zt.analyze_career(json.dumps(['武曲', '七杀']), json.dumps(['紫微']))
    out.append('\n=== 3. analyze_career ===')
    out.append('output (first 300 chars): %s' % r3[:300])
except Exception as e:
    out.append('\n=== 3. analyze_career: FAIL ===')
    out.append('Error: %s' % e)

# ============ 4. LiuYaoToolkit ============
from tools.divination_tools import LiuYaoToolkit
ly = LiuYaoToolkit()
try:
    r4 = ly.cast_hexagram(method='time', coins='')
    out.append('\n=== 4. LiuYaoToolkit.cast_hexagram ===')
    out.append('output (first 400 chars): %s' % r4[:400])
except Exception as e:
    out.append('\n=== 4. LiuYao cast: FAIL ===')
    out.append('Error: %s' % e)

try:
    r5 = ly.analyze_hexagram('乾为天', '事业')
    out.append('\n=== 5. analyze_hexagram(乾为天, 事业) ===')
    out.append('output (first 400 chars): %s' % r5[:400])
except Exception as e:
    out.append('\n=== 5. analyze_hexagram: FAIL ===')
    out.append('Error: %s' % e)

# ============ 5. QiMenToolkit ============
from tools.divination_tools import QiMenToolkit
qm = QiMenToolkit()
try:
    r6 = qm.build_qimen_pan(2024, 1, 15, 10)
    out.append('\n=== 6. QiMenToolkit.build_qimen_pan ===')
    d6 = json.loads(r6)
    out.append('status: %s' % d6.get('success', '?'))
    out.append('keys: %s' % list(d6.keys())[:8])
    out.append('output (first 300 chars): %s' % r6[:300])
except Exception as e:
    out.append('\n=== 6. QiMen: FAIL ===')
    out.append('Error: %s' % e)

# ============ 6. MeiHuaToolkit ============
from tools.divination_tools import MeiHuaToolkit
mh = MeiHuaToolkit()
try:
    r7 = mh.cast_meihua(15, 28, 2024)
    out.append('\n=== 7. MeiHuaToolkit.cast_meihua ===')
    out.append('output (first 300 chars): %s' % r7[:300])
except Exception as e:
    out.append('\n=== 7. MeiHua: FAIL ===')
    out.append('Error: %s' % e)

# ============ 7. LiuRenToolkit ============
from tools.divination_tools import LiuRenToolkit
lr = LiuRenToolkit()
try:
    r8 = lr.build_liuren_pan(2024, 1, 15, 10)
    out.append('\n=== 8. LiuRenToolkit.build_liuren_pan ===')
    out.append('output (first 300 chars): %s' % r8[:300])
except Exception as e:
    out.append('\n=== 8. LiuRen: FAIL ===')
    out.append('Error: %s' % e)

# ============ 8. BaziToolkit 关键函数 ============
from tools.bazi_tools import BaziToolkit
bt = BaziToolkit()
tool_list = [m for m in dir(bt) if not m.startswith('_') and callable(getattr(bt, m, None))]
out.append('\n=== 9. BaziToolkit available methods ===')
out.append('%s' % tool_list)

with open(r'E:\ming_li_skill\MingLiSkill\tool_audit.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('done, %d lines' % len(out))
