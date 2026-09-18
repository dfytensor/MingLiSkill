# -*- coding: utf-8 -*-
"""Retrospective test of marriage_scorer on all marriage year-questions in the 102 pool."""
import io, sys, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
import tools
from marriage_scorer import rank_years

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
]

def extract_years(text):
    return sorted(set(int(m) for m in re.findall(r'(1[89]\d{2}|20\d{2})', text)))

rows = []
for cf, af in PAIRS:
    charts = {c['id']: c for c in json.load(open(r'E:\ming_li_skill\MingLiSkill\%s' % cf, encoding='utf-8'))}
    ans = json.load(open(r'E:\ming_li_skill\MingLiSkill\%s' % af, encoding='utf-8'))
    for qid, a in ans.items():
        q = key[qid]
        if q.get('category') != '婚姻':
            continue
        c = charts[qid]
        bi = c['birth_info']
        ln = c['chart_data'].get('liunian') or {}
        if not ln.get('年份流年对比'):
            continue
        # chart dict for scorer: reuse four pillars etc.
        b = c['chart_data']['bazi']
        chart = {
            '日主': b['日主'], 'gender': bi['gender'], '四柱': b['四柱'],
        }
        # candidate years: years from options or detected
        opt_text = ' '.join(o['text'] for o in q['options'])
        years = set(extract_years(q['question'] + ' ' + opt_text)) | set(ln.get('检测到的年份', []))
        ranked = [r for r in rank_years(chart, ln) if r['year'] in years]
        if not ranked:
            continue
        best = ranked[0]
        # option letter for scorer's best year
        real_letter = q['answer']
        real_year = None
        for o in q['options']:
            ys = extract_years(o['text'])
            if real_year is None and ys:
                real_year = ys
        # match best year to option
        pick_letter = None
        for o in q['options']:
            if str(best['year']) in o['text']:
                pick_letter = o['letter']
                break
        rows.append({
            'qid': qid, 'q': q['question'][:38], 'mine': a['answer'], 'real': real_letter,
            'scorer_pick': pick_letter, 'best_year': best['year'], 'score': best['score'],
            'ranking': [(r['year'], r['score']) for r in ranked],
        })

ok_scorer = sum(1 for r in rows if r['scorer_pick'] == r['real'])
ok_mine = sum(1 for r in rows if r['mine'] == r['real'])
lines = []
lines.append('婚姻年份题(有流年数据): %d 题' % len(rows))
lines.append('婚期评分器: %d/%d = %.1f%%' % (ok_scorer, len(rows), ok_scorer / len(rows) * 100))
lines.append('我的盲测:   %d/%d = %.1f%%' % (ok_mine, len(rows), ok_mine / len(rows) * 100))
lines.append('')
for r in rows:
    mark_s = 'OK' if r['scorer_pick'] == r['real'] else 'X'
    mark_m = 'OK' if r['mine'] == r['real'] else 'X'
    lines.append('%s [%s] mine=%s(%s) scorer=%s(%s %s) real=%s  rank=%s' % (
        r['qid'], r['q'], r['mine'], mark_m, r['scorer_pick'], r['best_year'], r['score'], r['real'], r['ranking'][:4]))

with open(r'E:\ming_li_skill\MingLiSkill\marriage_scorer_eval.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('scorer %d/%d | mine %d/%d | total %d' % (ok_scorer, len(rows), ok_mine, len(rows), len(rows)))
