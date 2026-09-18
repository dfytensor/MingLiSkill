# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

doc = '''

---

## v20: 外部数据扩展 — 历年比赛真题库 (hkjfma.org 官方存档)

### 新获取数据 (data_archive/)

| 文件 | 内容 | 状态 |
|------|------|------|
| official_answer_keys.json | 2018/2023/2024 三届官方答案表 (各40题) | ✓ 完整可判分 |
| comp2020_questions.json | 2020第十一届 40题 8命例 (含23:50子时案例分析) | 题全, 答案缺 |
| comp2019_questions.json | 2019第十届 40题 8命例 (含双胞胎同年月日时案例) | 题全, 答案缺 |

数据来源: 香港青年术数家协会 hkjfma.org 历年比赛页面图片 → 视觉OCR提取。
MingLi-Bench 覆盖 2022-2025; 本次新增 2018/2019/2020 三届 = 120 题
净新增可判分数据: 2018届 40 题 (有题? 无 — 仅答案表)。
严格可判分净增: 0 (2018只有答案, 2019/2020只有题目)。

### 数据价值分析

1. **2019/2020 共80题完整题面**: 虽无官方答案, 但:
   - 2020 有获奖名单分数 (冠军17/30, 亚军16/30, 季军15/30) → 人类水平标定
   - 2019 有508人参赛逐题投票分布截图 → 可做难度/区分度分析
   - 可作为"无标签一致性测试集"(同题多方法答案一致性=信号可靠性)
2. **2018/2023/2024 官方答案表**: 与 MingLi-Bench (2022-2025) 交叉核对
   可检测基准标签错误; 2023命例老师名单已记录。
3. **双胞胎命例 (2019 Q36-40)**: 同八字不同命的官方案例 — 直接支撑
   "同八字不同命"边界讨论。

### 待办 (下轮闭环)

1. 2019/2020 找官方答案: Facebook 社团 hkjfma 组内或联系协会
2. 2018 题目: 可能在 FB 或纸质场刊
3. 用 2020 题面做无标签多方法一致性审计 (LLM推理 vs 机制信号 投票一致率)
4. data.json 160题按年份重分块后与 2023/2024 官方答案交叉核对标签

### OCR 工具链沉淀

- 题目图下载: fetch_*.py (URL编码+curl)
- 视觉OCR: 图片→结构化文本 (题目/选项/命例信息完整提取, 含繁简混排)
- 原始图片存档: data2020/ (10张), data2019/ (13张答案页+10张题目)
'''

with open(r'E:\ming_li_skill\MingLiSkill\SKILL.md', 'a', encoding='utf-8') as f:
    f.write(doc)
print('v20 appended, lines:', open(r'E:\ming_li_skill\MingLiSkill\SKILL.md', encoding='utf-8').read().count('\n') + 1)
