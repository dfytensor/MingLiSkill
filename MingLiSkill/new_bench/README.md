# BaziQA

八字命理 AI 能力基准测试框架。通过标准化的选择题数据集，评估 AI 八字分析的准确率，并按多个维度（流年运势、感情、六亲、事业等）进行统计。

数据集来源于论文 **[BaziQA-Benchmark: Evaluating Symbolic and Temporally Compositional Reasoning in Large Language Models](https://arxiv.org/abs/2602.12889)**。

**[查看测试结果 →](RESULT.md)**

## 工作流程

```text
数据集 (data/*.json)
    ↓
benchmark.py
    ↓
result-<mode>/*_cache.json
    ↓
score.py
    ↓
scores / scores-0
    ↓
patch_scores.py（按需）
    ↓
stats.py
```

完整链路可以理解为：

```text
1. benchmark.py
   读取题库 -> 调用排盘接口 -> 调用解盘接口 -> 把 solve_response 缓存下来

2. score.py
   根据缓存中的 uuid 拉取 AI 完整回答 -> 用 Gemini 提取每题答案 -> 判分

3. patch_scores.py
   如果某些命主 benchmark 成功了，但 score 时漏掉，就只补这些漏评命主

4. regen.py
   如果某个 uuid 取不到有效回答，就重新调一次解盘接口，生成新的 solve_response

5. stats.py
   汇总某个评分目录下所有数据集的总体准确率和各维度准确率
```

推荐顺序：

```text
benchmark.py -> score.py -> patch_scores.py（如有缺失） -> stats.py
```

如果 `patch_scores.py` 里出现 `回答为空，跳过`，说明不是评分逻辑本身出问题，而是缓存里的 `uuid` 对应不到有效回答。此时正确顺序是：

```text
regen.py -> patch_scores.py -> stats.py
```

## mode 说明

`benchmark.py` 支持两种 mode：

- `mode 1`：默认模式，结果写入 `result-1/`
- `mode 0`：额外测试模式，结果写入 `result-0/`

为了避免不同 mode 的结果互相覆盖，评分目录也分开：

```text
mode 1:
  benchmark -> result-1/
  score     -> scores/

mode 0:
  benchmark -> result-0/
  score     -> scores-0/
```

## 项目结构

```text
├── benchmark.py     # 基准测试：调用排盘/解盘 API，缓存结果
├── score.py         # 评分系统：拉取 AI 回答、提取答案、计算得分
├── patch_scores.py  # 补全 score 阶段漏评的命主
├── regen.py         # 对回答为空/无效的命主重新生成 solve_response
├── stats.py         # 统计汇总：多维度准确率报告
├── data/            # 数据集（按竞赛年份组织）
├── result-0/        # mode 0 的排盘/解盘缓存结果
├── result-1/        # mode 1 的排盘/解盘缓存结果
├── scores/          # mode 1 的评分结果及汇总
└── scores-0/        # mode 0 的评分结果及汇总（按需生成）
```

## 环境配置

在项目根目录创建 `.env` 文件：

```env
AUTH_TOKEN=你的lookfate授权token
GEMINI_KEY=你的Gemini API密钥
GEMINI_BASE=https://api.apiplus.org/v1
GEMINI_MODEL=gemini-3-flash-preview
```

最少依赖：

```bash
python3 -m pip install requests
```

## 使用方法

### 1. 运行基准测试

```bash
# 默认运行 data/ 下所有数据集，生成 mode 1 结果到 result-1/
python benchmark.py

# 运行指定数据集
python benchmark.py data/contest8_2025.json

# 生成 mode 0 测试数据到 result-0/
python benchmark.py --mode 0

# 指定 mode 0 + 指定数据集
python benchmark.py --mode 0 data/contest8_2025.json
```

说明：

- `benchmark.py` 会按 `person_id` 使用缓存，已生成过的命主不会重复请求。
- 缓存文件保存的是 `profile`、题目、以及解盘接口返回的 `solve_response`。
- `solve_response.data` 通常是后续获取完整 AI 回答时用到的 `uuid`。

### 2. 评分

```bash
# 默认读取 result-1/ 并输出到 scores/
python score.py

# 评分 mode 0 结果，默认输出到 scores-0/
python score.py --mode 0

# 自定义目录
python score.py <结果目录> <输出目录>
```

说明：

- `score.py` 不会重新调解盘接口。
- 它会读取缓存中的 `uuid`，然后去 lookfate 拉取完整回答。
- 再调用 Gemini 完成两件事：题目维度分类、从回答中提取 AI 选择的选项。
- 最终输出每道题的评分明细和该数据集的统计结果。

### 3. 补全漏评结果

```bash
# 补全 mode 1 的漏评命主
python patch_scores.py

# 补全 mode 0 的漏评命主
python patch_scores.py --mode 0
```

`patch_scores.py` 的作用：

- 找出“缓存里有，但评分结果里没有”的命主。
- 只补这些缺失命主，不会整份重新评分。
- 补完后会自动重算数据集统计，并重新生成汇总。

注意：

- 它只能补“评分缺失”。
- 如果日志里出现 `回答为空，跳过`，说明这个 `uuid` 本身拿不到有效回答，单靠 `patch_scores.py` 解决不了。

### 4. 重新生成无效回答

```bash
# 重新生成单个命主的 mode 1 回答
python regen.py <person_id>

# 重新生成单个命主的 mode 0 回答
python regen.py --mode 0 <person_id>

# 找出缺失评分后批量重跑
python regen.py --mode 0 --all-failed
```

`regen.py` 的作用：

- 重新调用排盘接口和解盘接口。
- 更新缓存中的 `solve_response`。
- 适用于 `score.py` 或 `patch_scores.py` 拿不到回答正文的情况。

通常在 `regen.py` 之后，再执行一次：

```bash
python patch_scores.py --mode 0
python stats.py scores-0
```

### 5. 统计汇总

```bash
# 默认读取 scores/
python stats.py

# 指定目录
python stats.py <评分目录>
```

例如查看 mode 0 汇总：

```bash
python stats.py scores-0
```

## 常见操作

### 跑完整的 mode 1 流程

```bash
python benchmark.py
python score.py
python patch_scores.py
python stats.py
```

### 跑完整的 mode 0 流程

```bash
python benchmark.py --mode 0
python score.py --mode 0
python patch_scores.py --mode 0
python stats.py scores-0
```

### 单个命主回答为空时的补救

假设日志类似：

```text
[female_19831028_P004] 获取 AI 回答... uuid=...
[female_19831028_P004] 回答为空，跳过
```

处理方式：

```bash
python regen.py --mode 0 female_19831028_P004
python patch_scores.py --mode 0
python stats.py scores-0
```

## 结果文件说明

### benchmark 缓存文件

路径示例：

```text
result-0/contest8_2025_cache.json
```

每个 `person_id` 下主要包含：

- `profile`
- `questions`
- `solve_response`

其中 `solve_response.data` 是后续拉取回答详情的关键字段。

### score 评分文件

路径示例：

```text
scores-0/contest8_2025.json
```

主要包含：

- `stats`：该数据集的总体和各维度准确率
- `details`：每一道题的评分明细，包括正确答案、AI 提取答案、是否答对、维度等

## 评分维度

| 维度 | 说明 |
|------|------|
| 流年运势 | 特定年份发生的事件、运势起伏 |
| 感情 | 恋爱、婚姻、离婚 |
| 六亲 | 父母、兄弟姐妹、子女 |
| 事业 | 职业、工作、创业 |
| 性格 | 性格特征、外表描述 |
| 学业 | 读书、学历 |
| 财富 | 财运、投资 |
| 健康 | 疾病、身体状况 |
| 其他 | 无法归入以上类别 |

## 数据集格式

每个数据集为 JSON 文件，第一项为元数据，后续为命主信息：

```json
[
  {"contest_id": "...", "total_questions": 50},
  {
    "person_id": "person_001",
    "name": "某某",
    "profile": {
      "birth": {"year": 1990, "month": 1, "day": 15, "hour": 8, "minute": 0},
      "gender": "male"
    },
    "questions": [
      {
        "question": "命主的职业是？",
        "options": ["A. 教师", "B. 医生", "C. 工程师", "D. 律师"],
        "answer": "C"
      }
    ]
  }
]
```
