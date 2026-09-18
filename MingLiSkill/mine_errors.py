# -*- coding: utf-8 -*-
"""
mine_errors.py — 从96道错题中挖掘系统性错误模式
检查假设:
H1: 正确答案是否倾向"最具体/最极端"选项(比赛出题心理)
H2: 正确答案是否倾向含数字/年份的选项(应期题)
H3: 错选是否集中在某些类别(婚姻/事业/健康)
"""
import io, sys, json
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

data = json.load(open(r'F:\牛逼模型\MingLi-Bench\data\data.json', encoding='utf-8'))
by_id = {q['id']: q for q in data['questions']}

FILES = [
    r'E:\ming_li_skill\MingLiSkill\hybrid9_answers.json',
    r'E:\ming_li_skill\MingLiSkill\hybrid4_answers.json',
    r'E:\ming_li_skill\MingLiSkill\hybrid5_answers.json',
    r'E:\ming_li_skill\MingLiSkill\hybrid7_answers.json',
    r'E:\ming_li_skill\MingLiSkill\hybrid8_answers.json',
    r'E:\ming_li_skill\MingLiSkill\hybrid6_answers.json',
    r'E:\ming_li_skill\MingLiSkill\v5blind_answers.json',
]
def getletter(v):
    return v.get('answer', v) if isinstance(v, dict) else v
BASE = {}
for f in FILES:
    for k, v in json.load(open(f, encoding='utf-8')).items():
        BASE.setdefault(k, getletter(v))

wrong = [(k, v, by_id[k]) for k, v in BASE.items() if k in by_id and by_id[k]['answer'] != v]
right = [(k, v, by_id[k]) for k, v in BASE.items() if k in by_id and by_id[k]['answer'] == v]
print('wrong=%d right=%d total=%d' % (len(wrong), len(right), len(BASE)))

def optlen(o):
    return len(o['text'])

# H1: 最长选项(最具体)是否更常为正确答案?
def pick_longest(q):
    return max(q['options'], key=optlen)['letter']
def pick_shortest(q):
    return min(q['options'], key=optlen)['letter']

def score_rule(rule, qs):
    return sum(1 for _, _, q in qs if rule(q) == q['answer'])

for name, rule in [('最长选项', pick_longest), ('最短选项', pick_shortest)]:
    wr = score_rule(rule, wrong)
    rr = score_rule(rule, right)
    tot = len(wrong) + len(right)
    overall = sum(1 for _, _, q in wrong + right if rule(q) == q['answer'])
    print('%s: 在错题上会改对 %d/%d, 在对题上会改错 %d/%d, 全局命中率 %.1f%%' % (
        name, wr, len(wrong), len(right)-rr+ (tot-0)*0, len(right), overall/tot*100))

# H2: 含年份选项
def pick_year(q):
    cands = [o for o in q['options'] if any(c.isdigit() for c in o['text'])]
    return cands[0]['letter'] if len(cands) == 1 else None
def pick_year_majority(q):
    cands = [o for o in q['options'] if any(c.isdigit() for c in o['text'])]
    if not cands: return None
    return Counter(c['letter'] for c in cands).most_common(1)[0][0]

yq = [(k, v, q) for k, v, q in wrong + right if pick_year_majority(q)]
if yq:
    yr = sum(1 for _, v, q in yq if pick_year_majority(q) == q['answer'])
    print('含年份题: %d 道, 任选年份选项命中率 %.1f%% (随机=%.0f%%)' % (
        len(yq), yr/len(yq)*100, 100/4))

# H3: 错题类别分布
wc = Counter(q['category'] for _, _, q in wrong)
rc = Counter(q['category'] for _, _, q in right)
print('\n类别分布(错/总):')
for cat in sorted(set(wc) | set(rc)):
    t = wc[cat] + rc[cat]
    print('  %s: %d错/%d总 = %d%%' % (cat, wc[cat], t, wc[cat]*100//max(t,1)))

# H4: 我错选的字母分布 vs 正确答案字母分布
print('\n我的错选字母:', dict(Counter(v for _, v, _ in wrong)))
print('正确答案字母:', dict(Counter(q['answer'] for _, _, q in wrong)))

# H5: "最负面/最极端"选项测试 (含死亡/病/灾字)
def pick_negative(q):
    neg = [o for o in q['options'] if any(w in o['text'] for w in ['死','亡','病','癌','灾','离','婚','破','贫'])]
    return neg[0]['letter'] if len(neg) == 1 else None
nq = [(k, v, q) for k, v, q in wrong + right if pick_negative(q)]
if nq:
    nr = sum(1 for _, v, q in nq if pick_negative(q) == q['answer'])
    print('\n含唯一负面选项题: %d 道, 选负面命中率 %.1f%%' % (len(nq), nr/len(nq)*100))
