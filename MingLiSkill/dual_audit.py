# -*- coding: utf-8 -*-
"""
dual_audit.py — 反向闭环审计
X信号(七杀伤病/官非/枭神停滞/劫财破耗/伤官小财) 在 ftb-115 上验证
基线: fixed_answers_v6.json (82/115)
"""
import io, sys, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from tools import HybridMingliToolkit
from tools.calendar_engine import shi_shen
from blind2021_run import unified, adapt

HTK = HybridMingliToolkit()
data = json.load(open(r'F:\牛逼模型\MingLi-Bench\data\data.json', encoding='utf-8'))
by_id = {q['id']: q for q in data['questions']}
BASE = json.load(open(r'E:\ming_li_skill\MingLiSkill\fixed_answers_v6.json', encoding='utf-8'))

# 只审计 X 信号: 复制 unified 但屏蔽 m3/m2(已是v6一部分), 单独测试X效果
# 简化: 全 unified 跑一遍, 只记录「X3/X4/X5/X1/X2 前缀」的改动
gain = loss = 0
details = []
for qid in sorted(BASE):
    q = by_id.get(qid)
    if not q: continue
    bi = {'year': q['birth_info']['year'], 'month': q['birth_info']['month'],
          'day': q['birth_info']['day'], 'hour': q['birth_info'].get('hour', 12),
          'gender': q['birth_info']['gender']}
    my = BASE[qid]; real = q['answer']
    pick, why = unified(q, bi)
    if pick is None or pick == my: continue
    if not any(why.startswith(x) for x in ('X1', 'X2', 'X3', 'X4', 'X5')):
        continue
    was = my == real; now = pick == real
    if now and not was: gain += 1; tag = 'GAIN'
    elif was and not now: loss += 1; tag = 'LOSS'
    else: continue
    BASE[qid] = pick
    details.append('%s: %s->%s real=%s %s [%s]' % (qid, my, pick, real, tag, why.encode('ascii','replace').decode()))

final = sum(1 for k, v in BASE.items() if k in by_id and by_id[k]['answer'] == v)
print('REVERSE X-AUDIT on ftb-115: +%d / -%d' % (gain, loss))
print('in-sample now: %d/115 = %.1f%%' % (final, final/115*100))
for d in details:
    print(' ', d)
json.dump(BASE, open(r'E:\ming_li_skill\MingLiSkill\fixed_answers_v7.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('saved fixed_answers_v7.json')
