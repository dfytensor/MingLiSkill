# -*- coding: utf-8 -*-
"""Re-analyze P028 (1977-07-06 male) with FIXED detailed_analysis data."""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from tools import HybridMingliToolkit

HTK = HybridMingliToolkit()
questions = json.load(open(r'E:\ming_li_skill\MingLiSkill\new_bench\bench2021_questions.json', encoding='utf-8'))

# Get P028 questions
p028_qs = [q for q in questions if 'P028' in q['person_id']]
bi = p028_qs[0]['birth']
gender = '男'

out = []
out.append('=== P028 (male 1977-07-06) FIXED detailed_analysis ===')

# Full chart with detailed analysis
r = HTK.analyze_question(
    year=bi['year'], month=bi['month'], day=bi['day'],
    hour=bi.get('hour', 12), gender=gender,
    category='综合', question='综合分析',
    options_json='[]')
chart = json.loads(r)

b = chart.get('bazi', {})
da = chart.get('detailed_analysis', {})
pillars = b.get('四柱', {})
wx = b.get('五行力量', {})
ss = b.get('十神', {})
ten_gods = b.get('十神', {})
day_gan = b.get('日主', '')

out.append('四柱: %s' % json.dumps(pillars, ensure_ascii=False))
out.append('日主: %s(%s) %s' % (day_gan, b.get('日主五行'), b.get('日主强弱')))
out.append('喜用: %s | 忌: %s' % (b.get('喜用神'), b.get('忌神')))
out.append('五行: %s' % json.dumps(wx, ensure_ascii=False))

# 十神详表 (FIXED)
ss_detail = da.get('十神详表', {})
out.append('\n=== 十神详表 (FIXED with correct stem/root/wuxing) ===')
for ss_name, positions in ss_detail.items():
    strength = len(positions) + sum(1 for p in positions if p.get('有根')) + sum(0.5 for p in positions if p.get('透干'))
    out.append('  %s (强度%.1f):' % (ss_name, strength))
    for p in positions:
        out.append('    %s | 干=%s | 有根=%s | 五行=%s | 透干=%s' % (
            p['位置'], p['天干'], p['有根'], p['五行'], p['透干']))

# 五行平衡
wx_bal = da.get('五行平衡', {})
out.append('\n=== 五行平衡 ===')
for w, d in wx_bal.items():
    out.append('  %s: %s %s %s' % (w, d['占比'], d['状态'], d['脏腑']))

# 性别十神
gender_ss = da.get('性别十神', {})
out.append('\n=== 性别十神 ===')
out.append(json.dumps(gender_ss, ensure_ascii=False))

# 紫微
z = chart.get('ziwei', {})
out.append('\n=== 紫微 ===')
for k, v in z.items():
    out.append('  %s: %s' % (k, v))

# Questions
out.append('\n=== Questions ===')
for qq in p028_qs:
    out.append('\n%s: %s' % (qq['question_id'], qq['question']))
    for o in qq['options']:
        if isinstance(o, dict):
            out.append('  %s. %s' % (o.get('letter', '?'), str(o.get('text', ''))[:80]))
        else:
            out.append('  %s' % str(o)[:80])

with open(r'E:\ming_li_skill\MingLiSkill\p028_analysis.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('done, %d lines' % len(out))
