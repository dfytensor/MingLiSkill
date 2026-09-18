# -*- coding: utf-8 -*-
"""Retrospective: do real answer years hit 红鸾/天喜/桃花/驿马 more than chance?"""
import io, sys, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
import tools
from tools.shensha import year_shensha
from tools.calendar_engine import year_ganzhi

DATA_PATH = r'F:\牛逼模型\MingLi-Bench\data\data.json'
with open(DATA_PATH, encoding='utf-8') as f:
    data = json.load(f)
key = {q['id']: q for q in data['questions']}

PAIRS = [
    ('blind15_charts.json', 'blind15_answers.json'),
    ('v5blind_charts.json', 'v5blind_answers.json'),
    ('blind30_charts.json', 'blind30_answers.json'),
    ('hybrid4_charts.json', 'hybrid4_answers.json'),
    ('hybrid5_charts.json', 'hybrid5_answers.json'),
    ('hybrid6_charts.json', 'hybrid6_answers.json'),
    ('hybrid7_charts.json', 'hybrid7_answers.json'),
]

def extract_years(text):
    return sorted(set(int(m) for m in re.findall(r'(1[89]\d{2}|20\d{2})', text)))

stats = {'marriage': [0, 0], 'love': [0, 0], 'any': [0, 0]}
detail = []
for cf, af in PAIRS:
    charts = {c['id']: c for c in json.load(open(r'E:\ming_li_skill\MingLiSkill\%s' % cf, encoding='utf-8'))}
    ans = json.load(open(r'E:\ming_li_skill\MingLiSkill\%s' % af, encoding='utf-8'))
    for qid, a in ans.items():
        q = key[qid]
        c = charts[qid]
        bi = c['birth_info']
        b = c['chart_data']['bazi']
        pillars = b['四柱']
        natal_zhis = [pillars[k][1] for k in ('年柱', '月柱', '日柱', '时柱')]
        opt_text = ' '.join(o['text'] for o in q['options'])
        years = sorted(set(extract_years(q['question'] + ' ' + opt_text)))
        if not years:
            continue
        real = q['answer']
        real_opt = next((o for o in q['options'] if o['letter'] == real), None)
        real_years = extract_years(real_opt['text']) if real_opt else []
        if not real_years:
            continue
        real_year = real_years[0]
        is_marriage = q['category'] == '婚姻' and re.search(r'结婚|婚|拍拖|恋爱', q['question'] + opt_text)
        is_love = re.search(r'拍拖|恋爱', q['question'] + opt_text)
        hits = year_shensha(pillars['年柱'][1], pillars['日柱'][1],
                            year_ganzhi(real_year)[1], natal_zhis)
        hongxi = [h for h in hits if '红鸾' in h or '天喜' in h]
        taohua = [h for h in hits if '桃花' in h]
        yima = [h for h in hits if '驿马' in h]
        if is_marriage:
            stats['marriage'][1] += 1
            if hongxi or taohua:
                stats['marriage'][0] += 1
        if is_love:
            stats['love'][1] += 1
            if taohua:
                stats['love'][0] += 1
        stats['any'][1] += 1
        if hits:
            stats['any'][0] += 1
        detail.append('%s [%s] real=%d(%s) hits=%s' % (qid, q['category'], real_year, real,
                       ','.join(hits) if hits else '-'))

lines = ['红鸾/天喜/桃花 信号回顾统计（标准查表，无自由参数）:']
lines.append('婚姻/婚恋题: 真实答案年命中红鸾天喜或桃花 %d/%d = %.0f%%' % (stats['marriage'][0], stats['marriage'][1], stats['marriage'][0]/max(stats['marriage'][1],1)*100))
lines.append('恋爱题: 命中桃花 %d/%d' % (stats['love'][0], stats['love'][1]))
lines.append('全部带年份选项题: 任一神煞命中 %d/%d = %.0f%% (4神煞×随机基线~%d%%)' % (
    stats['any'][0], stats['any'][1], stats['any'][0]/max(stats['any'][1],1)*100,
    round(4/12*100)))
lines.append('')
lines += detail
with open(r'E:\ming_li_skill\MingLiSkill\shensha_signal.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('marriage %d/%d | any %d/%d' % (stats['marriage'][0], stats['marriage'][1], stats['any'][0], stats['any'][1]))
