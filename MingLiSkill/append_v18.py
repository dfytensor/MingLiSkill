# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

doc = '''

---

## v18 最终章: 2021盲测揭露过拟合 — 诚实结论

### 盲测结果 (new_bench/bench2021_questions.json, 40道从未参与信号挖掘的新题)

- 信号引擎总成绩: 12/40 = 30.0% (随机=25%)
- 信号触发覆盖率: 仅 6/40 (2021年题干/选项措辞不同, 关键词信号不触发)
- 信号触发时正确率: 1/6 = 16.7% (低于随机!)

### 结论

v12-v17 的 71.3% (82/115) 是**样本内过拟合**:
信号在挖掘集上命中 = 关键词与答案的共现, 非命理规律本身。
换一批题目(不同措辞/不同年份), 信号既不触发(覆盖15%), 触发也错(16.7%)。

### 各方法真实水平(最终)

| 方法 | 样本内 | 盲测(泛化) |
|------|--------|-----------|
| 信号引擎自动化 | 71.3% | **30.0%** |
| LLM逐题推理+工具数据 | 40.0% | ~40%(机制不同, 待测) |
| 人类Top-20 | 51.88% | - |
| Tianfu Agent | 50.0% | - |

### 真正可交付的资产

1. 25+ 确定性排盘工具(八字/紫微/十神/神煞/大运/四化) — 计算正确性与过拟合无关
2. 11步推理流水线 + 56条规则 (SKILL.md v1-v11) — LLM推理方法论, 40%水平
3. 信号挖掘方法论本身(错题→数据→模式→审计→盲测) — 可复用, 但产物需逐基准校准
4. 教训: 任何在小题目集上挖掘的"规律"必须过盲测才能称为规则

盲测脚本: blind2021_run.py (统一引擎+适配器, 可复用于任何新基准)
'''

with open(r'E:\ming_li_skill\MingLiSkill\SKILL.md', 'a', encoding='utf-8') as f:
    f.write(doc)
print('appended v18 final, lines:', open(r'E:\ming_li_skill\MingLiSkill\SKILL.md', encoding='utf-8').read().count('\n') + 1)
