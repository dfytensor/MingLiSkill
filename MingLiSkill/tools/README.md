# tools/ 排盘工具包说明

确定性命理计算工具集，全部基于天文历法算法实现，**不含任何统计猜测成分**。
输出已与灵犀问道官方排盘逐柱核对一致。

## 工具清单

| 模块 | 入口 | 功能 |
|------|------|------|
| `hybrid_tools.py` | `HybridMingliToolkit.analyze_question()` | 统一入口：一次调用返回八字+紫微+十神+神煞+大运+详表 |
| `calendar_engine.py` | `year_ganzhi()`, `build_dayun_real()` | 万年历/流年干支/大运起运（真实节气计算，非近似） |
| `bazi_tools.py` | `BaziToolkit` | 四柱排盘/十神/五行力量/刑冲合害/ career|marriage 专项分析 |
| `ziwei_tools.py` | `ZiweiToolkit.paipan()` | 紫微安星/十二宫/主星亮度 |
| `shensha.py` | `natal_shensha()` | 神煞：红鸾天喜/桃花/驿马/华盖/文昌/三刑等 |
| `liunian_analyzer.py` | 流年分析 | 流年与命局作用关系 |
| `divination_tools.py` | 六爻/梅花 | 卜卦工具（本项目未深度使用） |

## 关键修正记录

开发过程中修复过两个真实历法 bug（详见 SKILL.md v6/v7）：

1. **流年干支偏移**：`year_ganzhi()` 早期版本默认参数导致所有流年干支偏移一年，
   已改为 `(year-4)%60` 精确计算
2. **大运起运近似**：早期用 (60-虚岁)/2 近似，已替换为真实节气间隔计算
   （`build_dayun_real()`，按出生日距节气日天数/3 折算）

## 使用示例

```python
from tools import HybridMingliToolkit
from tools.calendar_engine import year_ganzhi

print(year_ganzhi(2020))   # 庚子
tk = HybridMingliToolkit()
r = tk.analyze_question(year=1982, month=1, day=23, hour=1,
                        gender='男', category='', question='x',
                        options_json='[]')
import json
print(json.loads(r)['bazi']['四柱'])
# {'年柱': '辛酉', '月柱': '辛丑', '日柱': '丙午', '时柱': '己丑'}
# 与灵犀问道官方排盘一致
```

## 设计原则

- **排盘与解释分离**：工具只负责确定性计算，解释判断交给 agent
- **原子化**：每个工具单一职责，便于 agent 按需调用
- **可验证**：任意输出可与公开排盘站点交叉核对
