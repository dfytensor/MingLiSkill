# -*- coding: utf-8 -*-
"""
Run 2021 questions with ENHANCED analyze_question (detailed_analysis).
This is a true prospective test: the enhanced data extractor is new,
and we check if it improves the score from 30% (manual) / 27.5% (auto).
"""
import io, sys, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from tools import HybridMingliToolkit

HTK = HybridMingliToolkit()
DATA = json.load(open(r'E:\ming_li_skill\MingLiSkill\new_bench\bench2021_questions.json', encoding='utf-8'))
KEY = {q['question_id']: q['answer'].upper() if q.get('answer') else '?' for q in DATA}

results = []
correct = total = 0

for qq in DATA:
    qid = qq['question_id']
    birth = qq['birth']
    gender_raw = qq.get('gender', 'male')
    gender = '男' if gender_raw == 'male' else '女'
    question = qq.get('question', '')
    options = []
    for i, o in enumerate(qq.get('options', [])):
        if isinstance(o, dict):
            letter = o.get('letter', chr(65 + i)).upper()
            text = o.get('text', str(o))
        else:
            letter = chr(65 + i)
            text = str(o)
        options.append({'letter': letter, 'text': text})
    
    real = KEY.get(qid, '?')
    
    # Call enhanced analyze_question (with detailed_analysis)
    try:
        r = HTK.analyze_question(
            year=birth['year'], month=birth['month'], day=birth['day'],
            hour=birth.get('hour', 12), gender=gender,
            category='综合', question=question,
            options_json=json.dumps(options, ensure_ascii=False))
        chart = json.loads(r)
    except:
        chart = {}
    
    da = chart.get('detailed_analysis', {})
    b = chart.get('bazi', {})
    wx = b.get('五行力量', {})
    ss_detail = da.get('十神详表', {})
    wx_bal = da.get('五行平衡', {})
    gender_ss = da.get('性别十神', {})
    pillars = b.get('四柱', {})
    
    # Score options using detailed data
    option_scores = {}
    for opt in options:
        L = opt['letter']
        txt = opt['text']
        score = 0.0
        
        # 1. 十神详表推理
        # 检查选项关键词是否与强十神匹配
        for ss_name, positions in ss_detail.items():
            # Count positions with root (strong) vs without
            rooted = sum(1 for p in positions if p.get('有根'))
            transparent = sum(1 for p in positions if '天干' in p.get('位置', ''))
            strength = len(positions) + rooted + transparent * 0.5
            
            # Map 十神 to likely life themes
            ss_themes = {
                '正财': ['财', '钱', '收入', '富', '稳定'], '偏财': ['投资', '意外', '父', '生意', '投机'],
                '正官': ['工作', '升职', '官', '公职', '丈夫'], '七杀': ['压力', '竞争', '伤', '手术', '杀'],
                '正印': ['学', '文书', '房', '母', '证书', '传统', '保守'], '偏印': ['玄学', '偏门', '独特', '古怪', '创新'],
                '食神': ['才华', '艺术', '餐饮', '子女', '温和'], '伤官': ['创作', '口才', '叛逆', '离婚', '聪明'],
                '比肩': ['朋友', '合作', '竞争', '自我'], '劫财': ['被骗', '破财', '争夺', '朋友'],
                '正官+七杀': ['官杀混杂'],
            }
            themes = ss_themes.get(ss_name, [])
            for theme in themes:
                if theme in txt and strength > 1:
                    score += 1.5 * strength
        
        # 2. 五行平衡 → 健康器官
        for w, detail in wx_bal.items():
            status = detail.get('状态', '')
            organ = detail.get('脏腑', '')
            if status in ('缺', '极旺', '偏弱') and organ:
                # Split organ string and check each
                for o_name in organ.split('/'):
                    if o_name and o_name in txt:
                        if status == '缺':
                            score += 4
                        elif status == '极旺':
                            score += 2
                        elif status == '偏弱':
                            score += 1
        
        # 3. 性别十神推理
        if gender == '女':
            guan_info = gender_ss.get('官星现状', {})
            shang_guan = guan_info.get('伤官', [])
            if shang_guan and '离婚' in txt:
                score += 2
            if shang_guan and any(t in txt for t in ['桃花', '外遇']):
                score += 2
        
        # 4. 五行喜忌
        yong = b.get('喜用神', '')
        ji = b.get('忌神', '')
        if yong and yong in txt:
            score += 2
        if ji and ji in txt:
            score -= 2
        
        option_scores[L] = score
    
    # Pick best
    if option_scores:
        best = max(option_scores, key=lambda L: option_scores[L])
    else:
        best = options[0]['letter'] if options else 'A'
    
    ok = best == real
    total += 1
    correct += ok
    results.append('%s %s->%s %s | %s' % (qid, best, real, 'OK' if ok else 'X',
                    json.dumps({k: round(v,1) for k,v in option_scores.items()})))

lines = ['=== 2021 PROSPECTIVE with ENHANCED detailed_analysis ===']
lines.append('Score: %d/%d = %.1f%%' % (correct, total, correct / total * 100))
lines.append('vs manual reasoning: 12/40 = 30.0%')
lines.append('vs auto pipeline v1: 11/40 = 27.5%')
lines.append('vs auto pipeline v2: 11/40 = 27.5%')
lines.append('')
lines += results
with open(r'E:\ming_li_skill\MingLiSkill\new_bench\enhanced_result.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('ENHANCED: %d/%d = %.1f%%' % (correct, total, correct / total * 100))
