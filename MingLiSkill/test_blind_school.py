# -*- coding: utf-8 -*-
"""Test blind school on wrong answers from benchmark."""
import io, sys, json, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from tools import HybridMingliToolkit
from blind_school import analyze_gong, xiangfa_read, classify_ti_yong, day_wx_map
from collections import Counter

HTK = HybridMingliToolkit()
DATA = json.load(open(r'F:\牛逼模型\MingLi-Bench\data\data.json', encoding='utf-8'))
KEY = {q['id']: q for q in DATA['questions']}

# Load wrong answers
wrong = json.load(open(r'E:\ming_li_skill\MingLiSkill\wrong_answers.json', encoding='utf-8'))

# For each wrong answer, run 盲派做功分析
# Check if the 做功 type matches the correct answer's theme
out = []
blind_can_fix = 0
blind_checked = 0

for qid, w in sorted(wrong.items()):
    q = KEY[qid]
    bi = q['birth_info']
    g = '男' if bi['gender'] == '男' else '女'
    real = w['real']
    cat = w['cat']
    
    try:
        r = HTK.analyze_question(
            year=bi['year'], month=bi['month'], day=bi['day'],
            hour=bi.get('hour', 12), gender=bi['gender'],
            category=cat, question=q['question'],
            options_json=json.dumps(q['options'], ensure_ascii=False))
        chart = json.loads(r)
    except:
        continue
    
    b = chart.get('bazi', {})
    ss = b.get('十神', {})
    wx = b.get('五行力量', {})
    pillars = b.get('四柱', {})
    
    # Build 十神力量 map (十神 -> 五行力量)
    wx_scores = {}
    for pos, ss_name in ss.items():
        gan = pos.replace('天干','').replace('地支','')
        # Map 十神 to its 五行
        day_gan = b.get('日主','')
        # For simplicity: use the 五行力量 of the corresponding position
        if '天干' in pos:
            gz = pillars.get(pos.replace('天干','柱'), '')
            if gz:
                gan_char = gz[0]
                from tools.calendar_engine import WUXING_GAN
                wx_name = WUXING_GAN.get(gan_char, '')
                if wx_name:
                    wx_scores[ss_name] = max(wx_scores.get(ss_name, 0), wx.get(wx_name, 0))
    
    # 做功分析
    gongs = analyze_gong(ss, wx_scores)
    
    # 象法
    story = xiangfa_read(pillars)
    
    # Check if 做功 keywords match any option
    for o in q['options']:
        letter = o['letter']
        txt = o['text']
        for g in gongs:
            for kw in g['关键词']:
                try:
                    if kw in txt:
                        # This 做功 type matches this option
                        if letter == real:
                            blind_can_fix += 1
                            out.append('FIX %s [%s] 做功=%s 效率=%s 状态=%s → %s ✓' % (
                                qid, cat, g['做功'], g['效率'], g['状态'], letter))
                        else:
                            out.append('MISS %s [%s] 做功=%s matched %s but real=%s' % (
                                qid, cat, g['做功'], letter, real))
                except:
                    pass
    
    blind_checked += 1

out.append('')
out.append('=== Summary ===')
out.append('Wrong answers checked: %d' % blind_checked)
out.append('盲派做功 can fix: %d' % blind_can_fix)
out.append('Fix rate: %.1f%%' % (blind_can_fix / max(blind_checked, 1) * 100))

with open(r'E:\ming_li_skill\MingLiSkill\blind_school_result.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('checked %d, can fix %d (%.1f%%)' % (blind_checked, blind_can_fix, blind_can_fix/max(blind_checked,1)*100))
