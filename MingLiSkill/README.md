# MingLi Skill

命理学（八字/紫微斗数）推理 Skill，为 LLM Agent 提供命理分析工具和系统化推理框架。

## 项目结构

```
MingLiSkill\
├── SKILL.md              ← 使用说明 + 推理指南 + 40条常见陷阱
├── README.md             ← 项目概述（本文件）
├── tools/                ← 核心工具库
│   ├── hybrid_tools.py   ← HybridMingliToolkit（主入口）
│   ├── calendar_engine.py← 干支/五行引擎
│   ├── bazi_tools.py     ← 八字排盘与分析
│   ├── ziwei_tools.py    ← 紫微斗数排盘与分析
│   └── ...
├── engine/               ← 规则引擎
├── predict_mingli.py     ← 批量推理脚本
├── hybrid_router.py      ← 混合路由策略
└── run_bench_*.py        ← Benchmark 测试脚本
```

## 两种使用模式

### 1. Agent + Skill（当前主力，~93% 准确率）

LLM Agent 调用 `analyze_question` 获取排盘数据后，按照 SKILL.md 中的推理规则自主推理。

**最新测试** (2026-06-11, deepseek-v4-pro + MingLi-Bench 随机15题):

| 类别 | 正确 | 题数 | 准确率 |
|------|------|------|--------|
| 事业 | 5 | 5 | 100% |
| 学业 | 2 | 3 | 67% |
| 健康 | 3 | 3 | 100% |
| 家庭 | 4 | 4 | 100% |
| 婚姻 | 1 | 1 | 100% |
| 性格 | 1 | 1 | 100% |
| **总计** | **14** | **15** | **93.3%** |

```python
from tools import HybridMingliToolkit
import json

htk = HybridMingliToolkit()
result = htk.analyze_question(
    year=1990, month=6, day=15, hour=12, gender='男',
    category='事业', question='此命最适合从事什么行业？',
    options_json=json.dumps([...])
)
# Agent 读取返回的排盘数据 → 按推理规则自主推理 → 给出答案
```

### 2. 规则引擎 / 混合路由（离线批量）

纯 Python 规则引擎或 LLM+工具混合路由，适合批量 Benchmark 测试。

| 方法 | 准确率 | 题数 | 排名 |
|------|--------|------|------|
| 纯规则引擎 v3 | 33.75% | 54/160 | 全球第 8 |
| LLM + 工具注入 (qwen3.5-9b) | 35.10% | 53/151 | 全球第 7 |
| 混合路由 | 41.77% | 66/158 | 全球第 2 |

## 规则引擎亮点

- **速度**: 0.02 秒/题（vs LLM 的分钟级）
- **零成本**: 纯 Python，0 GPU
- **确定性强**: 结果可复现
- 在灾劫（100%）、健康（53%）等模式匹配型类别表现突出

## 工具清单

| 工具包 | 工具数 | 功能 |
|--------|--------|------|
| BaziToolkit | 16 | 八字排盘、大运、流年、十神、喜忌、冲合 |
| ZiweiToolkit | 10 | 紫微12宫排盘、命宫/官禄/夫妻等宫分析 |
| LiuYaoToolkit | — | 六爻占卜 |
| MeiHuaToolkit | — | 梅花易数 |
| QiMenToolkit | — | 奇门遁甲 |
| LiuRenToolkit | — | 大六壬 |
| PhysiognomyToolkit | — | 面相手相 |
| FengShuiToolkit | — | 风水 |

## 推理规则体系

SKILL.md 包含 40 条系统化推理规则 + 分类推理指南 + 40 个常见陷阱，核心规则：

| # | 规则 | 说明 |
|---|------|------|
| 1 | 日主先行锚定 | 日主天干为底层操作系统 |
| 2 | 地支 > 天干 | 内在真实 > 外在表现 |
| 3 | 制化改写十神 | 有制化的十神行为被改写 |
| 4 | 谱系思维 | 禁止二分法，所有判断是连续谱 |
| 5 | 多信号交叉验证 | 最少 2 个独立信号源 |
| 6 | 正 > 偏原则 | 正神优先级高于偏神 |
| 7 | 力量权重 | 禁止按出现次数判断，必须乘五行力量 |
| 8 | 十神喜忌偏置 | 所有信号必须检查喜用忌神 |
| 9 | 印星透干加权 | 天干/地支本气/余气不同权重 |

更多细节见 [SKILL.md](./SKILL.md)
