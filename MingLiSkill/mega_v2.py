# -*- coding: utf-8 -*-
"""
mega_v2.py — 用 enhanced detailed_analysis 的全量160题引擎
与 run_2021_enhanced.py 相同逻辑（40% on 2021），应用于主 benchmark。
"""
import io, sys, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\ming_li_skill\MingLiSkill')
from tools import HybridMingliToolkit

HTK = HybridMingliToolkit()
DATA_PATH = r'F:\牛逼模型\MingLi-Bench\data\data.json'

SS_THEMES = {
    '正财': ['财', '钱', '收入', '富', '稳定', '工资'], '偏财': ['投资', '意外', '父', '生意', '投机', '横财'],
    '正官': ['工作', '升职', '官', '公职', '丈夫', '管理'], '七杀': ['压力', '竞争', '伤', '手术', '杀', '开创'],
    '正印': ['学', '文书', '房', '母', '证书', '传统', '保守', '中式'], '偏印': ['玄学', '偏门', '独特', '古怪', '创新', '偏'],
    '食神': ['才华', '艺术', '餐饮', '子女', '温和', '享受'], '伤官': ['创作', '口才', '叛逆', '离婚', '聪明', '古灵精怪'],
    '比肩': ['朋友', '合作', '竞争', '自我'], '劫财': ['被骗', '破财', '争夺', '朋友', '投机'],
}

ORGAN_MAP = {'木': ['肝胆', '筋', '目'], '火': ['心', '小肠', '血脉'], '土': ['脾胃', '肌肉'],
             '金': ['肺', '大肠', '皮毛'], '水': ['肾', '膀胱', '骨', '耳']}


def score_options(question, chart, category):
    da = chart.get('detailed_analysis', {})
    b = chart.get('bazi', {})
    wx = b.get('五行力量', {})
    yong = b.get('喜用神', '')
    ji = b.get('忌神', '')
    wealth_tip = chart.get('wealth_analysis', {}).get('财运提示', '')
    ss_detail = da.get('十神详表', {})
    wx_bal = da.get('五行平衡', {})
    gender_ss = da.get('性别十神', {})
    gender = chart.get('gender', '')
    female = gender in ('女', 'F', 'female')
    
    liunian = chart.get('liunian') or {}
    
    # 十神强度计算
    ss_strength = {}
    for ss_name, positions in ss_detail.items():
        strength = len(positions)
        strength += sum(1 for p in positions if p.get('有根'))
        strength += sum(0.5 for p in positions if '天干' in p.get('位置', ''))
        ss_strength[ss_name] = strength
    
    option_scores = {}
    option_signals = {}
    
    for o in question.get('options', []):
        letter = o.get('letter', '?')
        txt = o.get('text', '')
        score = 0.0
        signals = []
        
        # S1: 十神强度匹配
        for ss_name, strength in ss_strength.items():
            themes = SS_THEMES.get(ss_name, [])
            for theme in themes:
                if theme in txt and strength > 0.5:
                    score += 1.0 * min(strength, 4)
                    signals.append('十神:%s(%s)' % (ss_name, theme))
        
        # S2: 印星对比（偏印 vs 正印）
        pian = ss_strength.get('偏印', 0)
        zheng = ss_strength.get('正印', 0)
        if pian > zheng * 1.5 and zheng < 1:
            if any(t in txt for t in ['独特', '古怪', '创新', '偏', '玄学', '欧式']):
                score += 3; signals.append('偏印>>正印→偏门')
            if any(t in txt for t in ['传统', '中式', '复古', '保守']):
                score -= 2; signals.append('正印弱→不传统')
        elif zheng > pian * 1.5:
            if any(t in txt for t in ['传统', '中式', '大学', '正规']):
                score += 3; signals.append('正印>>偏印→传统')
        
        # S3: 五行平衡
        for w, detail in wx_bal.items():
            status = detail.get('状态', '')
            organs = detail.get('脏腑', '').split('/')
            if status in ('缺', '极旺', '偏弱'):
                for organ in organs:
                    if organ and organ in txt and category == '健康':
                        bonus = {'缺': 5, '极旺': 3, '偏弱': 1}.get(status, 0)
                        score += bonus; signals.append('五行%s:%s(%s)' % (status, w, organ))
        
        # S4: 性别十神
        if female:
            guan_info = gender_ss.get('官星现状', {})
            shang_guan_count = len(guan_info.get('伤官', []))
            guan_count = len(guan_info.get('正官', [])) + len(guan_info.get('七杀', []))
            if shang_guan_count > 0 and guan_count == 0:
                if '离婚' in txt or '分手' in txt:
                    score += 3; signals.append('女伤官无官→婚变')
            if guan_count > 0 and '已婚' in txt:
                score += 2; signals.append('女有官→已婚')
        else:
            cai_info = gender_ss.get('财星现状', {})
        
        # S5: 喜忌
        if yong and yong in txt: score += 2; signals.append('喜用')
        if ji and ji in txt: score -= 2; signals.append('忌神')
        
        # S6: 身强身弱
        if '身弱' in wealth_tip:
            if any(t in txt for t in ['贫', '穷', '债', '无']): score += 2; signals.append('身弱→贫')
            if any(t in txt for t in ['富', '老板', '管理']): score -= 2
        if '身旺' in wealth_tip:
            if any(t in txt for t in ['富', '老板', '管理', '商']): score += 2; signals.append('身旺任财')
        
        # S7: 流年
        yr_match = re.search(r'(19\d{2}|20\d{2})', txt)
        if yr_match:
            yr = int(yr_match.group(1))
            for yi in (chart.get('liunian') or {}).get('年份流年对比', []):
                if yi.get('年份') == yr:
                    tags = yi.get('标签', [])
                    if any('喜用' in t for t in tags): score += 2; signals.append('流年喜用')
                    if any('忌神' in t for t in tags): score -= 2; signals.append('流年忌神')
                    
                    gan_ss = yi.get('天干十神', '')
                    themes = SS_THEMES.get(gan_ss, [])
                    for theme in themes:
                        if theme in txt:
                            score += 3; signals.append('流年十神:%s→%s' % (gan_ss, theme))
        
        option_scores[letter] = score
        option_signals[letter] = signals
    
    return option_scores, option_signals


def main():
    with open(DATA_PATH, encoding='utf-8') as f:
        data = json.load(f)
    
    correct = total = 0
    detail = []
    cat_stats = {}
    
    for q in data['questions']:
        bi = q['birth_info']
        cat = q['category']
        try:
            r = HTK.analyze_question(
                year=bi['year'], month=bi['month'], day=bi['day'],
                hour=bi.get('hour', 12), gender=bi['gender'],
                category=cat, question=q['question'],
                options_json=json.dumps(q['options'], ensure_ascii=False))
            chart = json.loads(r)
        except:
            chart = {}
        
        scores, signals = score_options(q, chart, cat)
        best = max(scores, key=lambda L: scores[L]) if scores else 'A'
        real = q['answer']
        ok = best == real
        total += 1
        correct += ok
        cat_stats.setdefault(cat, [0,0])
        cat_stats[cat][0] += ok
        cat_stats[cat][1] += 1
        detail.append('%s %-4s %s->%s %s' % (q['id'], cat, best, real, 'OK' if ok else 'X'))
    
    lines = ['=== MEGA V2 (enhanced detailed_analysis) ===']
    lines.append('Score: %d/%d = %.1f%%' % (correct, total, correct/total*100))
    lines.append('vs committed: 64/160 = 40.0%')
    lines.append('vs 2021 test: 16/40 = 40.0%')
    lines.append('')
    for cat, s in sorted(cat_stats.items()):
        lines.append('  %s: %d/%d (%.0f%%)' % (cat, s[0], s[1], s[0]/max(s[1],1)*100))
    lines += detail
    with open(r'E:\ming_li_skill\MingLiSkill\mega_v2_result.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print('MEGA V2: %d/%d = %.1f%%' % (correct, total, correct/total*100))


if __name__ == '__main__':
    main()
