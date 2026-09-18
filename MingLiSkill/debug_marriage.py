# -*- coding: utf-8 -*-
import io, sys, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
import tools
DATA_PATH = r'F:\牛逼模型\MingLi-Bench\data\data.json'
with open(DATA_PATH, encoding='utf-8') as f:
    data = json.load(f)
key = {q['id']: q for q in data['questions']}
cf, af = 'blind30_charts.json', 'blind30_answers.json'
charts = {c['id']: c for c in json.load(open(r'E:\ming_li_skill\MingLiSkill\%s' % cf, encoding='utf-8'))}
ans = json.load(open(r'E:\ming_li_skill\MingLiSkill\%s' % af, encoding='utf-8'))
n_total = n_mar = n_ln = 0
for qid, a in ans.items():
    q = key[qid]
    n_total += 1
    if q.get('category') != '婚姻':
        continue
    n_mar += 1
    c = charts[qid]
    ln = c['chart_data'].get('liunian') or {}
    has = bool(ln.get('年份流年对比'))
    if has:
        n_ln += 1
        b = c['chart_data']['bazi']
        print(qid, b['日主'], bi if (bi := c['birth_info']) else None, ln.get('检测到的年份'))
print('total=%d marriage=%d with_liunian=%d' % (n_total, n_mar, n_ln))
# test scorer import
from marriage_scorer import rank_years, spouse_stars
print('spouse_stars 癸,男:', spouse_stars('癸', '男'))
chart = {'日主': '癸', 'gender': '男', '四柱': {'年柱': '庚申', '月柱': '癸未', '日柱': '乙酉', '时柱': '辛巳'}}
# ftb_0077 in blind30
if 'ftb_0077' in charts:
    c = charts['ftb_0077']
    b = c['chart_data']['bazi']
    chart = {'日主': b['日主'], 'gender': c['birth_info']['gender'], '四柱': b['四柱']}
    ln = c['chart_data'].get('liunian', {})
    print('rank ftb_0077:', [(r['year'], r['score']) for r in rank_years(chart, ln)])
