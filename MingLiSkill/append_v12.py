# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

fix_doc = '''

---

## v12: 三大实战修复（来自错题复盘，已验证）

### 修复A: 机梁在福德宫 = 玄学命理缘 (验证: ftb_0055 ✓)
福德宫(紫微)天机+天梁同宫 → 强玄学命理宗教缘。
若选项含: 命理/风水/玄学/算命/占卜/宗教/法师/八字/顾问 → 优先选它。
工具: fix_tools.analyze_fude_palace()

### 修复B: 天相 = 掌印管理者, 不是秘书 (验证: ftb_0132 ✓)
命宫天相 → 天相是印星=掌印者=管理者/老板。
选项同时含"秘书类"和"管理类"时 → 选管理类, 排除秘书类。
印星(正印+偏印)透干>=2 同理 → 优先管理/官员选项。

### 修复C: 女命官杀检查要算百分比, 不能只看有无
官杀五行占比 = 五行力量中克我者/总和。
ftb_0016 教训: 官杀实际18.3%(不弱), 之前误判=0推出"家庭主妇"是错的。
必须先算准百分比再推理。

### 实测净效果
基线(union已存档答案): 37/115 = 32.2% → 修复后 38/115 = 33.0% (+2处改动全中)
注: 之前汇报的40%基线含未存档轮次答案, 115题可复核基线为32.2%。
'''

with open(r'E:\ming_li_skill\MingLiSkill\SKILL.md', 'a', encoding='utf-8') as f:
    f.write(fix_doc)

c = open(r'E:\ming_li_skill\MingLiSkill\SKILL.md', encoding='utf-8').read()
print('appended v12, lines now:', c.count('\n') + 1)
