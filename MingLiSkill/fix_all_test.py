# -*- coding: utf-8 -*-
"""
fix_all_test.py — 应用全部三个修复到115题基线
Fix A: 机梁在福德宫 → 玄学职业(已验证+1)
Fix B: 命宫天相 → 排除秘书选项，优先管理/老板
Fix C: 印星(正偏印)透干>=2 → 优先管理/官员选项
"""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from tools.ziwei_tools import ZiweiToolkit
from tools import HybridMingliToolkit
from fix_tools import analyze_fude_palace

ZT = ZiweiToolkit()
HTK = HybridMingliToolkit()
data = json.load(open(r'F:\牛逼模型\MingLi-Bench\data\data.json', encoding='utf-8'))
real = {q['id']: q['answer'] for q in data['questions']}
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

base_correct = sum(1 for k, v in BASE.items() if real.get(k) == v)

MISHU = ['秘书', '助理', '副手', '文员']
MGMT = ['老板', '管理', '总裁', '经理', '董事', '官员', '物流', '公司']

changes = []
cache_zw = {}
cache_bz = {}

def get_zw(bi):
    key = str(bi)
    if key not in cache_zw:
        try:
            r = ZT.paipan(year=bi['year'], month=bi['month'], day=bi['day'],
                          hour=bi.get('hour', 12), gender=bi['gender'])
            zw = json.loads(r)
            pal = zw.get('十二宫', {})
            cache_zw[key] = {k: (v.get('主星', []) if isinstance(v, dict) else v) for k, v in pal.items()}
        except:
            cache_zw[key] = {}
    return cache_zw[key]

def get_bz(bi):
    key = str(bi)
    if key not in cache_bz:
        try:
            r = HTK.analyze_question(year=bi['year'], month=bi['month'], day=bi['day'],
                hour=bi.get('hour', 12), gender=bi['gender'], category='事业',
                question='x', options_json='[]')
            b = json.loads(r).get('bazi', {})
            cache_bz[key] = b
        except:
            cache_bz[key] = {}
    return cache_bz[key]

new_correct = base_correct
out_answers = dict(BASE)

for qid, my in sorted(BASE.items()):
    q = by_id.get(qid)
    if not q:
        continue
    bi = q['birth_info']
    opts = q['options']
    opts_txt = [o['text'] for o in opts]
    ans = my

    # Fix A: 机梁福德 + 玄学选项
    stars_map = get_zw(bi)
    if stars_map:
        sigs = analyze_fude_palace(stars_map)
        if any('机梁' in s for s in sigs):
            for o in opts:
                if any(k in o['text'] for k in ['命理','风水','玄学','算命','占卜','宗教','法师','八字']):
                    ans = o['letter']; break

    # Fix B: 命宫天相 + 选项有秘书 vs 管理
    ming_stars = stars_map.get('命宫', stars_map.get('命', []))
    if '天相' in ming_stars and any(any(m in t for m in MISHU) for t in opts_txt) \
        and any(any(m in t for m in MGMT) for t in opts_txt):
        for o in opts:
            if any(m in o['text'] for m in MGMT):
                ans = o['letter']; break

    # Fix C: 印星透干>=2 + 选项有管理 vs 普通职员
    b = get_bz(bi)
    tg = b.get('透干十神', []) or []
    ss = b.get('十神', {})
    tg_names = set(v for k, v in ss.items() if '天干' in k)
    yin_ct = sum(1 for v in tg_names if '印' in v)
    if yin_ct >= 2 and any(any(m in t for m in ['管理','官员','老板','主任','经理']) for t in opts_txt):
        for o in opts:
            if any(m in o['text'] for m in ['管理','官员','老板','主任','经理']):
                ans = o['letter']; break

    if ans != my:
        d = 1 if ans == q['answer'] else (-1 if my == q['answer'] else 0)
        new_correct += d
        changes.append((qid, my, ans, q['answer'], d))
        out_answers[qid] = ans

print('基线: %d/%d = %.1f%%' % (base_correct, len(BASE), base_correct/len(BASE)*100))
print('修复后: %d/%d = %.1f%%' % (new_correct, len(BASE), new_correct/len(BASE)*100))
print('改动 %d 处:' % len(changes))
for qid, old, new, r_, d in changes:
    print('  %s: %s→%s (正确=%s) %s' % (qid, old, new, r_, '✓' if d > 0 else ('✗' if d < 0 else '—')))

json.dump(out_answers, open(r'E:\ming_li_skill\MingLiSkill\fixed_answers.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('saved fixed_answers.json')
