# -*- coding: utf-8 -*-
"""Simple direct test: call tools for each 2021 question, pick answer."""
import io, sys, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from tools import HybridMingliToolkit
from tools.shensha import natal_shensha, year_shensha
from tools.calendar_engine import year_ganzhi

HTK = HybridMingliToolkit()
DATA = json.load(open(r'E:\ming_li_skill\MingLiSkill\new_bench\bench2021_questions.json', encoding='utf-8'))

results = []
correct = total = 0

for qq in DATA:
    qid = qq['question_id']
    birth = qq['birth']
    gender_raw = qq.get('gender', 'male')
    gender = '男' if gender_raw == 'male' else '女'
    real = qq['answer'].upper() if qq.get('answer') else '?'
    question = qq.get('question', '')
    raw_options = qq.get('options', [])
    
    # Normalize options
    options = []
    for i, o in enumerate(raw_options):
        if isinstance(o, dict):
            letter = o.get('letter', chr(65 + i)).upper()
            text = o.get('text', str(o))
        else:
            letter = chr(65 + i)
            text = str(o)
        options.append({'letter': letter, 'text': text})
    
    # STEP 1: 排盘
    try:
        r = HTK.analyze_question(
            year=birth['year'], month=birth['month'], day=birth['day'],
            hour=birth.get('hour', 12), gender=gender,
            category='综合', question=question,
            options_json=json.dumps(options, ensure_ascii=False))
        chart = json.loads(r)
    except Exception as e:
        chart = {}
    
    b = chart.get('bazi', {})
    wx = b.get('五行力量', {})
    day_wx = b.get('日主五行', '')
    yong = b.get('喜用神', '')
    ji = b.get('忌神', '')
    wealth_tip = chart.get('wealth_analysis', {}).get('财运提示', '')
    pillars = b.get('四柱', {})
    
    # STEP 3: 神煞
    yz = pillars.get('年柱', '')[-1:]
    dz = pillars.get('日柱', '')[-1:]
    natal = natal_shensha(yz, dz, b.get('日主', ''))
    natal_zhis = [pillars.get(k, '')[-1:] for k in ('年柱','月柱','日柱','时柱')]
    
    # STEP 4-5: 流年神煞+十神 for each option year
    option_scores = {}
    for opt in options:
        L = opt['letter']
        txt = opt['text']
        score = 0.0
        themes = []
        theme_words = {
            '婚': ['结婚','娶','嫁','婚','夫妻'], '离': ['离婚','离异','分手'],
            '子': ['孩子','子','女','生育','怀孕','流产'],
            '财': ['财','富','钱','生意','产业','投资','股'],
            '贫': ['贫','穷','负债','欠','困难'],
            '病': ['病','疾','手术','住院','癌','伤','骨折'],
            '官': ['官','公职','政府','公务员','老师','管理'],
            '讼': ['官司','牢','狱','刑事','罪'],
            '迁': ['出国','移民','留学','搬迁','到','旅行'],
            '学': ['学','读书','大学','文凭','毕业'],
            '技': ['技术','电脑','厨师','维修','美甲'],
            '商': ['生意','经商','老板','创业','销售'],
            '孤': ['孤','独身','未婚','单'],
            '智': ['聪','智','慧','才华','能读书'],
            '暴': ['暴','躁','火','冲','急'],
        }
        for theme, words in theme_words.items():
            for w in words:
                if w in txt:
                    themes.append(theme)
                    break
        
        # 喜忌加持
        if yong:
            for wx_name, cnt in wx.items():
                if wx_name == yong and cnt > 2:
                    for theme, words in theme_words.items():
                        pass  # 喜用五行相关主题加分（简化）
        
        # 年份匹配: 流年十神/神煞
        yr_match = re.search(r'(19\d{2}|20\d{2})', txt)
        if yr_match:
            yr = int(yr_match.group(1))
            lgz = year_ganzhi(yr)
            lz = lgz[-1:]
            # 神煞
            try:
                sh = year_shensha(yz, dz, lz, natal_zhis)
                sh_str = str(sh)
                if '红鸾' in sh_str or '天喜' in sh_str:
                    if any(t in themes for t in ('婚',)):
                        score += 5
                if '桃花' in sh_str:
                    if any(t in themes for t in ('恋',)):
                        score += 4
                if '驿马' in sh_str:
                    if any(t in themes for t in ('迁',)):
                        score += 4
                if '三刑' in sh_str:
                    if any(t in themes for t in ('讼', '病')):
                        score += 3
            except:
                pass
            
            # 流年干支五行 vs 喜忌
            lg_gan = lgz[:1] if lgz else ''
            from tools.calendar_engine import WUXING_GAN, WUXING_ZHI
            lg_wx = WUXING_GAN.get(lg_gan, '')
            if lg_wx == yong:
                score += 2
            if lg_wx == ji:
                score -= 2
        
        # 五行=0 器官对应（健康题）
        if '病' in themes or '健康' in question:
            for wx_name, cnt in wx.items():
                if cnt == 0:
                    organ_map = {'木':'肝胆','火':'心脏','土':'脾胃','金':'肺','水':'肾脑骨'}
                    organ = organ_map.get(wx_name, '')
                    if organ and organ in txt:
                        score += 5
        
        # 身弱/身强修正
        if '身弱' in wealth_tip:
            if any(t in themes for t in ('贫',)):
                score += 3
            if any(t in themes for t in ('财', '商')):
                score -= 2
        if '身旺' in wealth_tip:
            if any(t in themes for t in ('财', '商')):
                score += 2
        
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
                                            json.dumps(option_scores)))

lines = ['=== 2021 AUTO TOOL PIPELINE v2 ===']
lines.append('Score: %d/%d = %.1f%%' % (correct, total, correct / total * 100))
lines.append('Previous manual answer: 12/40 = 30.0%')
lines.append('Previous main benchmark: 64/160 = 40.0%')
lines.append('')
lines += results
with open(r'E:\ming_li_skill\MingLiSkill\new_bench\auto_v2_result.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('AUTO v2: %d/%d = %.1f%%' % (correct, total, correct / total * 100))
