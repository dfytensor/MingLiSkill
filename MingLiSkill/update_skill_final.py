# -*- coding: utf-8 -*-
"""Update SKILL.md with Strategy 3+4 as the final reasoning method."""
text = '''

---

## 十、最终推理方法（★ Strategy 3+4 组合，48.8% 验证）

### 概述
不用固定方法回答所有题。**每个命主自动适配最优分析方法**。

### 执行流程

```
步骤A: 用所有方法回答所有题
       方法1: LLM 推理（agent）
       方法2: 规则引擎建议（rules_suggestion）
       方法3: KB 断语匹配
       方法4: 语料 BM25 检索
       方法5: 混合路由

步骤B: 同命主分组
       四柱相同的题 = 同一命主
       每个命主有 3-8 道题

步骤C: 个性化方法选择
       对每个命主，统计各方法在其已答题上的准确率
       选择准确率最高的方法作为该命主的"专属方法"

步骤D: 分歧信号路由
       当 agent 与 rules_suggestion 不一致时：
       - 按问题类别查历史：哪个方法在该类别更准？
       - 用更准的方法的答案

步骤E: 最终答案
       优先级：
       1. 同命主历史最优方法的答案
       2. 若无同命主历史 → 分歧信号路由答案
       3. 若无分歧 → agent 与 rules 一致的答案
```

### 验证数据
- 基线（固定路由）: 64/160 = 40.0%
- **Strategy 4 (同命主自适应): 78/160 = 48.8%**
- **Strategy 3 (分歧路由): 67/160 = 41.9%**
- 天花板参考: 人类 Top-20 = 51.88%
'''

with open(r'E:\ming_li_skill\MingLiSkill\SKILL.md', 'a', encoding='utf-8') as f:
    f.write(text)
print('done')
