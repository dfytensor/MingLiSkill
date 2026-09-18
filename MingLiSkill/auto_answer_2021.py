# -*- coding: utf-8 -*-
"""
auto_answer_2021.py — 自动调用全工具链分析2021年40题
每题完整走11步流水线，工具输出直接决定选项。
"""
import io, sys, json, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from tools import HybridMingliToolkit
from tools.shensha import natal_shensha, year_shensha
from tools.calendar_engine import year_ganzhi, shi_shen
from extra_tools import auto_yongshen, sihua_feigong, sanfang_sizheng
from knowledge_base import query_kb
from collections import Counter

HTK = HybridMingliToolkit()
DATA = json.load(open(r'E:\ming_li_skill\MingLiSkill\new_bench\bench2021_questions.json', encoding='utf-8'))

# assertion keywords for option matching (from classical corpus + KB)
THEME_WORDS = {
    '财': ['财', '富', '钱', '生意', '产业', '置业', '收入', '投资', '股票'],
    '贫': ['贫', '穷', '负债', '欠', '月光', '困难', '入不敷'],
    '婚': ['结婚', '娶', '嫁', '夫妻', '已婚', '婚姻', '一婚', '二婚'],
    '离': ['离婚', '离异', '克妻', '克夫', '分手', '二婚'],
    '子': ['孩子', '子女', '儿子', '女儿', '生育', '怀孕', '流产', '生'],
    '病': ['病', '疾', '手术', '住院', '癌', '肿瘤', '药', '医', '伤', '骨折'],
    '官': ['官', '公职', '公务员', '政府', '管理', '高职', '老师', '教育'],
    '讼': ['官司', '牢', '狱', '刑事', '犯罪', '警察', '扣留'],
    '迁': ['出国', '移民', '留学', '搬迁', '搬家', '旅行', '移动', '到'],
    '艺': ['艺', '音乐', '美术', '画', '演奏', '文艺', '创作'],
    '技': ['技术', '电脑', '工程', '维修', '厨师', '美甲', '驾驶'],
    '商': ['生意', '经商', '老板', '创业', '零售', '销售', '贸易'],
    '孤': ['孤', '独身', '未婚', '单', '寂寞'],
    '智': ['聪', '智', '慧', '聪明', '才华', '能读书'],
    '愚': ['愚', '笨', '呆', '不爱读书', '与书无缘'],
    '暴': ['暴', '躁', '火', '冲动', '急'],
    '温和': ['温和', '柔', '善', '仁', '安静'],
    '固执': ['固执', '保守', '守', '不变'],
}

def get_themes(text):
    hits = []
    for theme, words in THEME_WORDS.items():
        for w in words:
            if w in text:
                hits.append(theme)
                break
    return hits


def analyze_question_full(q, birth, gender):
    """Full pipeline analysis for one question."""
    g = '男' if gender == 'male' else '女'
    cat = detect_category(q['question'])
    
    # STEP 1: 排盘
    try:
        r = HTK.analyze_question(
            year=birth['year'], month=birth['month'], day=birth['day'],
            hour=birth.get('hour', 12), gender=g,
            category=cat, question=q['question'],
            options_json=json.dumps(q['options'], ensure_ascii=False))
        chart = json.loads(r)
    except Exception:
        chart = {}
    
    b = chart.get('bazi', {})
    z = chart.get('ziwei', {})
    pillars = b.get('四柱', {})
    wx = b.get('五行力量', {})
    day_gan = b.get('日主', '')
    day_wx = b.get('日主五行', '')
    yong = b.get('喜用神', '')
    ji = b.get('忌神', '')
    
    # STEP 2: 用神
    ys = auto_yongshen(cat, b)
    
    # STEP 3: 原局神煞
    yz = pillars.get('年柱', '')[-1:]
    dz = pillars.get('日柱', '')[-1:]
    natal = natal_shensha(yz, dz, day_gan)
    
    # STEP 4: 选项年份神煞
    opt_years = {}
    for o in q.get('options', []):
        txt = o.get('text', '') if isinstance(o, dict) else str(o)
        letter = o.get('letter', '?') if isinstance(o, dict) else '?'
        yrs = re.findall(r'(19\d{2}|20\d{2})', txt)
        for yr in yrs:
            yr = int(yr)
            lgz = year_ganzhi(yr)
            lz = lgz[-1:]
            try:
                sh = year_shensha(yz, dz, lz, [pillars.get(k, '')[-1:] for k in ('年柱','月柱','日柱','时柱')])
                if sh:
                    opt_years.setdefault(letter, []).extend(sh)
            except:
                pass
    
    # STEP 5-8: 流年十神 + 排盘分析
    liunian = chart.get('liunian') or {}
    year_signals = {}
    for yi in liunian.get('年份流年对比', []):
        yr = yi.get('年份')
        gan_ss = yi.get('天干十神', '')
        tags = yi.get('标签', [])
        is_yong = any('喜用' in t for t in tags)
        is_ji = any('忌神' in t for t in tags)
        year_signals[yr] = {
            'shishen': gan_ss,
            'is_yong': is_yong, 'is_ji': is_ji,
            'themes': get_themes(gan_ss) if gan_ss else []
        }
    
    # STEP 9: KB
    tg_values = [v for k, v in b.get('十神', {}).items() if k.endswith('天干')]
    kb_feats = {'十神透干': list(set(tg_values)), '神煞': list(natal['positions'].values())}
    if female := gender in ('female', '女', 'F'):
        kb_feats['女命十神'] = kb_feats['十神透干']
    kb_res = query_kb(kb_feats, top_n=5)
    kb_keywords = []
    for _, e in kb_res:
        kb_keywords += e['关键词']
    
    # SCORE OPTIONS
    option_scores = {}
    for o in q.get('options', []):
        if isinstance(o, dict):
            letter = o.get('letter', '?')
            txt = o.get('text', '')
        else:
            letter = '?'
            txt = str(o)
        
        score = 0.0
        themes = get_themes(txt)
        
        # 1. Question-type matching: does option theme match what chart suggests?
        # 财多身弱 → 贫困选项加分
        if '身弱' in chart.get('wealth_analysis', {}).get('财运提示', ''):
            if '贫' in themes:
                score += 3
            if '财' in themes:
                score -= 2
        
        # 2. 官杀/食伤 for career
        if cat in ('事业',):
            guan = wx.get({'木':'火','火':'土','土':'金','金':'水','水':'木'}.get(day_wx,''), 0)
            shang = wx.get({'木':'火','火':'土','土':'金','金':'水','水':'木'}.get(day_wx,''), 0)
            if '官' in themes and guan > 2:
                score += 2
            if '商' in themes and '身旺任财' in chart.get('wealth_analysis', {}).get('财运提示',''):
                score += 2
        
        # 3. Year matching: does the year in option have relevant shensha/十神?
        yr_match = re.search(r'(19\d{2}|20\d{2})', txt)
        if yr_match:
            yr = int(yr_match.group(1))
            if yr in year_signals:
                sig = year_signals[yr]
                if sig['is_yong']:
                    score += 2
                if sig['is_ji']:
                    score -= 2
                # Check if option theme matches 流年十神 themes
                opt_themes = get_themes(txt)
                ss_themes = get_themes(sig['shishen'] or '')
                overlap = set(opt_themes) & set(ss_themes)
                if overlap:
                    score += 3
        
        # 4. Shensha in option year
        if letter in opt_years:
            sh = opt_years[letter]
            if '红鸾' in str(sh) or '天喜' in str(sh):
                if '婚' in themes or '恋' in themes:
                    score += 5
            if '桃花' in str(sh):
                if '恋' in themes:
                    score += 4
            if '驿马' in str(sh):
                if '迁' in themes:
                    score += 4
            if '三刑' in str(sh):
                if '讼' in themes or '病' in themes:
                    score += 3
        
        # 5. KB keywords matching
        for kw in kb_keywords:
            try:
                if re.search(kw, txt):
                    score += 1
            except:
                pass
        
        # 6. Five element extreme → health mapping
        if cat == '健康':
            for wx_name, cnt in wx.items():
                if cnt == 0:
                    organs = {'木':'肝胆','火':'心脏','土':'脾胃','金':'肺','水':'肾脑骨'}
                    organ = organs.get(wx_name, '')
                    if organ and organ in txt:
                        score += 4
                elif cnt / max(sum(wx.values()), 1) > 0.4:
                    organs = {'木':'肝胆','火':'心脏','土':'脾胃','金':'肺','水':'肾脑骨'}
                    organ = organs.get(wx_name, '')
                    if organ and organ in txt:
                        score += 2
        
        option_scores[letter] = score
    
    return option_scores, chart


def detect_category(question):
    if any(w in question for w in ['工作', '职业', '事业', '创业', '经商']):
        return '事业'
    if any(w in question for w in ['结婚', '婚姻', '婚', '离婚', '感情', '恋爱', '拍拖']):
        return '婚姻'
    if any(w in question for w in ['孩子', '子女', '儿子', '女儿', '生育']):
        return '子女'
    if any(w in question for w in ['病', '健康', '身体', '手术', '住院']):
        return '健康'
    if any(w in question for w in ['学历', '读书', '大学', '学业']):
        return '学业'
    if any(w in question for w in ['官非', '牢', '狱', '刑事']):
        return '官非'
    if any(w in question for w in ['家境', '出身', '父母', '家庭']):
        return '家庭'
    if any(w in question for w in ['性格', '个性', '脾气']):
        return '性格'
    if any(w in question for w in ['财运', '理财', '收入']):
        return '财运'
    if any(w in question for w in ['父亲', '母亲', '爷爷', '奶奶']):
        return '家庭'
    return '综合'


def main():
    all_questions = DATA
    results = []
    correct = total = 0
    
    for qq in all_questions:
        qid = qq['question_id']
        birth = qq['birth']
        gender = qq['gender']
        real = qq['answer']
        
        # Normalize option letters to uppercase
        options = []
        for o in qq['options']:
            if isinstance(o, dict):
                options.append(o)
            else:
                options.append({'letter': '?', 'text': str(o)})
        
        # Fix lowercase letters
        for i, o in enumerate(options):
            if o['letter'] in ('a', 'b', 'c', 'd'):
                o['letter'] = o['letter'].upper()
        
        q_for_analysis = {'question': qq['question'], 'options': options}
        
        try:
            scores, chart = analyze_question_full(q_for_analysis, birth, gender)
        except Exception as e:
            scores = {}
        
        if not scores:
            # fallback: random
            letters = [o['letter'] for o in options if o['letter'] != '?']
            best = letters[0] if letters else 'A'
        else:
            best = max(scores, key=lambda L: scores[L])
        
        # Normalize real answer
        real_upper = real.upper() if real else real
        
        ok = best == real_upper
        total += 1
        correct += ok
        results.append({'qid': qid, 'pick': best, 'real': real_upper, 'ok': ok,
                        'scores': {k: round(v, 1) for k, v in scores.items()}})
    
    lines = ['=== 2021 AUTO PIPELINE (tool-driven answers) ===']
    lines.append('Score: %d/%d = %.1f%%' % (correct, total, correct / total * 100))
    lines.append('')
    for rr in results:
        lines.append('%s %s->%s %s | scores=%s' % (rr['qid'], rr['pick'], rr['real'],
                     'OK' if rr['ok'] else 'X', rr['scores']))
    
    with open(r'E:\ming_li_skill\MingLiSkill\new_bench\auto_pipeline_result.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print('AUTO PIPELINE: %d/%d = %.1f%%' % (correct, total, correct / total * 100))


if __name__ == '__main__':
    main()
