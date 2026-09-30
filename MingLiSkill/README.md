<div align="center">

# MingLi Skill

**中文命理（八字 / 紫微斗数）LLM Agent Skill —— 含 555 题官方真题库、确定性排盘工具链与可复现的验证协议**

</div>

本项目是一个面向 LLM Agent 的中国命理分析 Skill，覆盖八字（子平）与紫微斗数两大体系。项目不仅提供排盘与推理工具，更重要的是建立了一套**可复现、不可作弊的效果验证协议**，并给出了关于「命理规则能否被统计挖掘」的实证结论。

---

## 核心特性

- **确定性排盘工具链**（25+ 工具）：万年历 / 四柱 / 十神 / 十二长生 / 神煞 / 大运起运 / 紫微安星 / 四化飞宫 / 盲派做功等，输出与官方排盘逐柱核对一致
- **555 题官方真题库**：来自全球命理师大赛（hkjfma.org）2010-2026 全部 17 届，含官方答案，已结构化（`data_archive/`）
- **完整验证协议**：训练/留出集划分、预注册预测（git 时间戳锁定）、统计显著性检验
- **诚实的实验档案**：所有尝试（成功与失败）全部记录在 `SKILL.md`（v1-v24，1500+ 行）

## 实测结果（诚实版）

| 方法 | 样本内 | 预注册盲测 | 说明 |
|------|--------|-----------|------|
| 规则信号引擎 | 71.3% | **30.0%** | 样本内为过拟合上界 |
| LLM 逐题推理 | 40.0% | 未测 | 与最强 LLM 基线持平 |
| 人类 Top-20 | — | 51.88% | 官方统计 |
| 随机 | — | 25% | 四选一 |

**核心结论**（经 555 题统计检验，109 个事件年样本）：
比赛正确答案与八字-流年机制特征之间**不存在跨出题体系统计显著的映射**（全部特征 lift≈1.0）。样本内挖掘的"规律"是小样本幻觉；冠军的优势来自识别出题老师的个人体系，而非普适规则。

## 安装

```bash
git clone https://github.com/dfytensor/MingLiSkill.git
cd MingLiSkill
pip install -r requirements.txt   # 若无依赖文件则无第三方硬依赖(纯标准库)
```

## 快速使用

```python
import sys
sys.path.insert(0, 'MingLiSkill')

from tools import HybridMingliToolkit
import json

toolkit = HybridMingliToolkit()
# 输入公历生日, 输出八字+紫微+十神+神煞+大运全量数据
result = toolkit.analyze_question(
    year=1974, month=4, day=28, hour=16, gender='男',
    category='事业', question='命主的职业?',
    options_json='[]')
chart = json.loads(result)
print(chart['bazi']['四柱'])       # 四柱干支
print(chart['detailed_analysis'])  # 十神详表/五行平衡/性别十神
```

命令行批量评测：

```bash
cd MingLiSkill
python blind2021_run.py        # 在2021届40题上运行统一信号引擎
python dual_audit.py           # 反向闭环审计
python extract_asklingxi.py    # 重新抓取/更新555题官方答案
```

## 仓库结构

```
MingLiSkill/
├── SKILL.md                    # 方法论主文档: 11步流水线+56规则+v1-v24全部实验档案
├── README.md
├── tools/                      # 确定性排盘工具包
│   ├── hybrid_tools.py         #   HybridMingliToolkit 统一入口
│   ├── calendar_engine.py      #   万年历/流年/大运起运(真太阳时)
│   ├── bazi_tools.py           #   四柱/十神/刑冲合害
│   ├── ziwei_tools.py          #   紫微安星/十二宫
│   ├── shensha.py              #   神煞系统
│   └── ...
├── data_archive/               # 官方真题库与实验数据
│   ├── asklingxi_answers.json  #   17届555题官方答案
│   ├── master2.json            #   命例四柱+答案结构化
│   ├── dataset555.json         #   事件年特征数据集
│   ├── feature_stats.json      #   特征统计检验结果
│   └── official_answer_keys.json #  2018/2023/2024官方答案(图片OCR)
├── comp2019_questions.json / comp2020_questions.json  # 两届完整题面
├── preregistered_predictions.json  # 预注册预测(已判分30%)
├── marriage_fix_v2/v3.py 等    # 六个信号引擎(含失败记录)
├── blind2021_run.py            # 统一信号引擎+双集盲测
├── dual_audit.py               # 反向闭环审计
├── mine555_v2.py               # 555题统计监督学习流水线
└── corpus/ books/              # 2MB古籍语料(渊海子平/子平真诠/穷通宝鉴等)
```

## 方法论：五层闭环

本项目的方法论核心是一套**以泛化为唯一验收标准**的闭环：

1. **挖掘层**：错题 + 工具全量数据 → 候选模式
2. **机制层**：候选必须映射到古典命理机制，拒绝纯关键词共现
3. **语义层**：命理方向 → 同义词族（含简繁变体）
4. **验证层**：内审（挖掘集 GAIN/LOSS）→ 盲测（独立集）→ 双集命中才算规则
5. **迭代层**：盲测失败即降级/删除；新数据轮换为下轮挖掘集

## 预注册协议

为杜绝"先看答案再找规律"的自欺，本项目实现了预注册验证：

1. 在官方答案公开前，对 2019/2020 两届 70 题提交预测（git commit `44151f4` 时间戳锁定）
2. 官方答案公开后（来自 asklingxi.com 完整题库）立即判分
3. 判分标准预先写死：>51.88% 超人类 / 40-52% LLM 基线 / <30% 机制不泛化
4. **实际结果：21/70 = 30.0%** → 结论：机制信号在全新数据上不成立

## 数据来源与致谢

- 真题与官方答案：[香港青年术数家协会](https://hkjfma.org) 历届全球命理师大赛
- 结构化题库镜像：[灵犀问道](https://asklingxi.com/mingli-dasai)
- 基准封装参考：[MingLi-Bench](https://github.com/DestinyLinker/MingLi-Bench)（本仓库已用官方答案逐题验证其 2023/2024 两届标签 80/80 一致）
- 古籍语料：渊海子平、子平真诠、穷通宝鉴、滴天髓等公开电子文本

## License

仅供命理研究与学习参考。
